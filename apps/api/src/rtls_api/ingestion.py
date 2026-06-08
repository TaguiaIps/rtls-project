from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from rtls_api.config import Settings
from rtls_api.ingestion_store import MessageDedupeStore
from rtls_api.models import (
    AssetTag,
    Gateway,
    GatewayHealthStatus,
    GatewayHeartbeat,
    RawReading,
)
from rtls_api.positioning import PositioningService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def telemetry_topic(settings: Settings) -> str:
    return f"{settings.mqtt_topic_prefix.rstrip('/')}/data/+"


def heartbeat_topic(settings: Settings) -> str:
    return f"{settings.mqtt_topic_prefix.rstrip('/')}/heartbeat/+"


def gateway_health_status(
    *,
    settings: Settings,
    last_seen_at: datetime,
    now: datetime | None = None,
) -> GatewayHealthStatus:
    observed_now = ensure_utc(now or utc_now())
    normalized_last_seen_at = ensure_utc(last_seen_at)
    if observed_now - normalized_last_seen_at <= timedelta(
        seconds=settings.gateway_heartbeat_stale_after_seconds
    ):
        return GatewayHealthStatus.HEALTHY
    return GatewayHealthStatus.STALE


class TelemetryReadingPayload(BaseModel):
    tag_id: str = Field(min_length=1, max_length=120)
    rssi: int = Field(ge=-200, le=0)
    tx_power: int | None = Field(default=None, ge=-200, le=100)
    channel: int | None = Field(default=None, ge=0, le=255)


class TelemetryEnvelope(BaseModel):
    gateway_id: str = Field(min_length=1, max_length=120)
    message_id: str = Field(min_length=1, max_length=120)
    gateway_timestamp: datetime | None = None
    firmware_version: str | None = Field(default=None, max_length=120)
    readings: list[TelemetryReadingPayload]

    @model_validator(mode="after")
    def validate_readings_present(self) -> TelemetryEnvelope:
        if not self.readings:
            raise ValueError("Telemetry must contain at least one reading")
        return self


class HeartbeatEnvelope(BaseModel):
    gateway_id: str = Field(min_length=1, max_length=120)
    message_id: str = Field(min_length=1, max_length=120)
    gateway_timestamp: datetime | None = None
    firmware_version: str | None = Field(default=None, max_length=120)
    battery_level_percent: float | None = Field(default=None, ge=0, le=100)


@dataclass(frozen=True)
class IngestionResult:
    accepted: bool
    message_type: str
    reason: str
    raw_reading_count: int = 0


class TelemetryIngestionService:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        settings: Settings,
        dedupe_store: MessageDedupeStore,
        positioning_service: PositioningService,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._dedupe_store = dedupe_store
        self._positioning_service = positioning_service

    def process_message(
        self,
        *,
        topic: str,
        payload_bytes: bytes,
        broker_received_at: datetime | None = None,
    ) -> IngestionResult:
        received_at = ensure_utc(broker_received_at or utc_now())
        message_type, topic_gateway_id = _parse_topic(topic, self._settings)
        if message_type is None or topic_gateway_id is None:
            return IngestionResult(False, "unknown", "unsupported_topic")

        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError:
            return IngestionResult(False, message_type, "malformed_json")

        try:
            if message_type == "telemetry":
                envelope = TelemetryEnvelope.model_validate(payload)
            else:
                envelope = HeartbeatEnvelope.model_validate(payload)
        except ValidationError:
            return IngestionResult(False, message_type, "invalid_payload")

        if envelope.gateway_id != topic_gateway_id:
            return IngestionResult(False, message_type, "gateway_id_mismatch")

        with self._session_factory() as db:
            gateway = db.scalar(
                select(Gateway).where(Gateway.gateway_identifier == envelope.gateway_id)
            )
            if gateway is None:
                return IngestionResult(False, message_type, "unknown_gateway")

            claimed = self._dedupe_store.claim_message(
                gateway.gateway_identifier,
                envelope.message_id,
                self._settings.ingestion_dedupe_ttl_seconds,
            )
            if not claimed:
                return IngestionResult(False, message_type, "duplicate_message")

            if message_type == "telemetry":
                reading_count = self._persist_telemetry(
                    db=db,
                    gateway=gateway,
                    envelope=envelope,
                    broker_received_at=received_at,
                )
                db.flush()
                self._positioning_service.update_positions_for_tags(
                    db=db,
                    tag_identifiers={reading.tag_id for reading in envelope.readings},
                    observed_at=received_at,
                )
                db.commit()
                return IngestionResult(True, message_type, "accepted", reading_count)

            self._persist_heartbeat(
                db=db,
                gateway=gateway,
                envelope=envelope,
                broker_received_at=received_at,
            )
            db.commit()
            return IngestionResult(True, message_type, "accepted", 0)

    def _persist_telemetry(
        self,
        *,
        db: Session,
        gateway: Gateway,
        envelope: TelemetryEnvelope,
        broker_received_at: datetime,
    ) -> int:
        tag_identifiers = {reading.tag_id for reading in envelope.readings}
        known_tags = db.scalars(
            select(AssetTag).where(AssetTag.tag_identifier.in_(tag_identifiers))
        ).all()
        tags_by_identifier = {asset_tag.tag_identifier: asset_tag for asset_tag in known_tags}

        for reading in envelope.readings:
            asset_tag = tags_by_identifier.get(reading.tag_id)
            db.add(
                RawReading(
                    gateway_id=gateway.id,
                    asset_tag_id=asset_tag.id if asset_tag else None,
                    tag_identifier=reading.tag_id,
                    message_id=envelope.message_id,
                    broker_received_at=broker_received_at,
                    gateway_timestamp=ensure_utc(envelope.gateway_timestamp),
                    firmware_version=envelope.firmware_version,
                    rssi=reading.rssi,
                    tx_power=reading.tx_power,
                    channel=reading.channel,
                )
            )
        return len(envelope.readings)

    def _persist_heartbeat(
        self,
        *,
        db: Session,
        gateway: Gateway,
        envelope: HeartbeatEnvelope,
        broker_received_at: datetime,
    ) -> None:
        latest = db.get(GatewayHeartbeat, gateway.id)
        if latest is None:
            latest = GatewayHeartbeat(
                gateway_id=gateway.id,
                last_seen_at=broker_received_at,
                message_id=envelope.message_id,
            )
            db.add(latest)

        latest.last_seen_at = broker_received_at
        latest.gateway_timestamp = ensure_utc(envelope.gateway_timestamp)
        latest.message_id = envelope.message_id
        latest.firmware_version = envelope.firmware_version
        latest.battery_level_percent = envelope.battery_level_percent


def _parse_topic(topic: str, settings: Settings) -> tuple[str | None, str | None]:
    prefix = settings.mqtt_topic_prefix.rstrip("/")
    telemetry_prefix = f"{prefix}/data/"
    heartbeat_prefix = f"{prefix}/heartbeat/"
    if topic.startswith(telemetry_prefix):
        gateway_id = topic.removeprefix(telemetry_prefix)
        if gateway_id and "/" not in gateway_id:
            return "telemetry", gateway_id
    if topic.startswith(heartbeat_prefix):
        gateway_id = topic.removeprefix(heartbeat_prefix)
        if gateway_id and "/" not in gateway_id:
            return "heartbeat", gateway_id
    return None, None
