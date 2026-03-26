from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.ingestion import TelemetryIngestionService, ensure_utc
from rtls_api.main import create_app
from rtls_api.models import (
    AssetBatteryProfile,
    AssetTag,
    AssetUpdateRateProfile,
    Floor,
    Gateway,
    GatewayHeartbeat,
    RawReading,
    Site,
    UserRole,
)


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-ingestion.db'}",
        redis_url="memory://ingestion-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        **overrides,
    )


def issue_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_gateway(app, *, gateway_identifier: str = "gw-lobby-01") -> tuple[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Flagship Site", timezone_name="America/Bahia")
        db.add(site)
        db.flush()
        floor = Floor(site_id=site.id, name="Lobby", level_label="L1")
        db.add(floor)
        db.flush()
        gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier=gateway_identifier,
            display_name="Lobby Gateway",
            hardware_tier="Economic",
            placement_x=0.25,
            placement_y=0.4,
        )
        db.add(gateway)
        db.commit()
        return gateway.id, floor.id


def create_ingestion_service(app, settings: Settings) -> TelemetryIngestionService:
    return TelemetryIngestionService(
        session_factory=app.state.session_factory,
        settings=settings,
        dedupe_store=app.state.message_dedupe_store,
    )


def test_valid_telemetry_ingestion_persists_raw_readings(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    gateway_id: str
    with TestClient(app):
        gateway_id, _ = seed_gateway(app)
        with app.state.session_factory() as db:
            db.add(
                AssetTag(
                    tag_identifier="TAG-001",
                    display_name="Cart 1",
                    asset_category="cart",
                    update_rate_profile=AssetUpdateRateProfile.BALANCED.value,
                    battery_profile=AssetBatteryProfile.STANDARD.value,
                )
            )
            db.commit()

        service = create_ingestion_service(app, settings)
        result = service.process_message(
            topic="rtls/data/gw-lobby-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-lobby-01",
                    "message_id": "msg-001",
                    "gateway_timestamp": "2026-03-25T12:00:00Z",
                    "firmware_version": "1.4.0",
                    "readings": [
                        {"tag_id": "TAG-001", "rssi": -63, "tx_power": -8, "channel": 37},
                        {"tag_id": "TAG-999", "rssi": -71},
                    ],
                }
            ).encode("utf-8"),
            broker_received_at=datetime(2026, 3, 25, 12, 0, 1, tzinfo=timezone.utc),
        )

        assert result.accepted is True
        assert result.reason == "accepted"
        assert result.raw_reading_count == 2

        with app.state.session_factory() as db:
            readings = db.scalars(
                select(RawReading)
                .where(RawReading.gateway_id == gateway_id)
                .order_by(RawReading.tag_identifier.asc())
            ).all()

        assert [reading.tag_identifier for reading in readings] == ["TAG-001", "TAG-999"]
        assert readings[0].asset_tag_id is not None
        assert readings[1].asset_tag_id is None
        assert ensure_utc(readings[0].broker_received_at) == datetime(
            2026, 3, 25, 12, 0, 1, tzinfo=timezone.utc
        )


def test_ingestion_rejects_malformed_unknown_and_duplicate_messages(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app):
        seed_gateway(app)
        service = create_ingestion_service(app, settings)

        malformed = service.process_message(
            topic="rtls/data/gw-lobby-01",
            payload_bytes=b"{not-json",
        )
        assert malformed.accepted is False
        assert malformed.reason == "malformed_json"

        invalid_payload = service.process_message(
            topic="rtls/data/gw-lobby-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-lobby-01",
                    "message_id": "msg-invalid",
                    "readings": [],
                }
            ).encode("utf-8"),
        )
        assert invalid_payload.accepted is False
        assert invalid_payload.reason == "invalid_payload"

        unknown_gateway = service.process_message(
            topic="rtls/data/gw-missing-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-missing-01",
                    "message_id": "msg-unknown",
                    "readings": [{"tag_id": "TAG-001", "rssi": -60}],
                }
            ).encode("utf-8"),
        )
        assert unknown_gateway.accepted is False
        assert unknown_gateway.reason == "unknown_gateway"

        first = service.process_message(
            topic="rtls/data/gw-lobby-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-lobby-01",
                    "message_id": "msg-dup",
                    "readings": [{"tag_id": "TAG-001", "rssi": -60}],
                }
            ).encode("utf-8"),
        )
        duplicate = service.process_message(
            topic="rtls/data/gw-lobby-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-lobby-01",
                    "message_id": "msg-dup",
                    "readings": [{"tag_id": "TAG-001", "rssi": -60}],
                }
            ).encode("utf-8"),
        )

        assert first.accepted is True
        assert duplicate.accepted is False
        assert duplicate.reason == "duplicate_message"

        with app.state.session_factory() as db:
            readings = db.scalars(select(RawReading)).all()

        assert len(readings) == 1


def test_heartbeat_ingestion_updates_gateway_health_feed(tmp_path: Path) -> None:
    settings = build_settings(tmp_path, gateway_heartbeat_stale_after_seconds=300)
    app = create_app(settings)

    with TestClient(app) as client:
        _, floor_id = seed_gateway(app)
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Admin",
            )
            db.commit()

        service = create_ingestion_service(app, settings)
        heartbeat_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = service.process_message(
            topic="rtls/heartbeat/gw-lobby-01",
            payload_bytes=json.dumps(
                {
                    "gateway_id": "gw-lobby-01",
                    "message_id": "hb-001",
                    "gateway_timestamp": "2026-03-25T12:03:00Z",
                    "firmware_version": "1.4.2",
                    "battery_level_percent": 88,
                }
            ).encode("utf-8"),
            broker_received_at=heartbeat_time,
        )
        assert result.accepted is True

        admin_token = issue_token(client, "admin@example.com", "StrongPass123")
        response = client.get(
            "/api/admin/gateway-health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "gateway_id": response.json()[0]["gateway_id"],
                "floor_id": floor_id,
                "floor_name": "Lobby",
                "gateway_identifier": "gw-lobby-01",
                "display_name": "Lobby Gateway",
                "hardware_tier": "Economic",
                "status": "healthy",
                "last_seen_at": heartbeat_time.isoformat().replace("+00:00", "Z"),
                "gateway_timestamp": "2026-03-25T12:03:00Z",
                "message_id": "hb-001",
                "firmware_version": "1.4.2",
                "battery_level_percent": 88.0,
            }
        ]

        with app.state.session_factory() as db:
            stored_heartbeat = db.get(
                GatewayHeartbeat,
                response.json()[0]["gateway_id"],
            )

        assert stored_heartbeat is not None
        assert stored_heartbeat.message_id == "hb-001"


def test_worker_subscribes_to_data_and_heartbeat_topics(monkeypatch, tmp_path: Path) -> None:
    from rtls_api import worker

    settings = build_settings(tmp_path, mqtt_topic_prefix="pilot")
    monkeypatch.setattr(worker, "get_settings", lambda: settings)

    subscribed_topics: list[tuple[str, int]] = []

    class FakeClient:
        def subscribe(self, topic: str, qos: int) -> None:
            subscribed_topics.append((topic, qos))

    worker.subscribe_to_topics(FakeClient())

    assert subscribed_topics == [
        ("pilot/data/+", 1),
        ("pilot/heartbeat/+", 1),
    ]
