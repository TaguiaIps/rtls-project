from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    GENERAL_USER = "General User"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class SpatialAreaType(str, Enum):
    ZONE = "zone"
    TABLE = "table"
    RESTRICTED_ZONE = "restricted_zone"
    POI = "poi"


class GatewayHardwareTier(str, Enum):
    ECONOMIC = "Economic"
    PREMIUM = "Premium"


class PremiumTelemetryModality(str, Enum):
    BLE_AOA = "BLE_AOA"
    UWB = "UWB"


class PremiumCalibrationStatus(str, Enum):
    UNCALIBRATED = "uncalibrated"
    CALIBRATED = "calibrated"
    STALE = "stale"


class GatewayHealthStatus(str, Enum):
    HEALTHY = "healthy"
    STALE = "stale"


class AssetUpdateRateProfile(str, Enum):
    SLOW = "slow"
    BALANCED = "balanced"
    REALTIME = "realtime"


class AssetBatteryProfile(str, Enum):
    LONG_LIFE = "long_life"
    STANDARD = "standard"
    PERFORMANCE = "performance"


class AssetLocationType(str, Enum):
    POINT = "point"
    ZONE = "zone"


class LocationConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LocationSourceModality(str, Enum):
    BLE_RSSI = "BLE_RSSI"
    BLE_AOA = PremiumTelemetryModality.BLE_AOA.value
    UWB = PremiumTelemetryModality.UWB.value


class DerivedZoneEventType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


class DwellClosureReason(str, Enum):
    ZONE_CHANGE = "zone_change"
    FLOOR_CHANGE = "floor_change"
    RESOLVED_PLACEMENT_LOST = "resolved_placement_lost"


class TableServiceTimerStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"


class AlertRuleType(str, Enum):
    TABLE_SLA = "table_sla"
    UNAUTHORIZED_GEOFENCE = "unauthorized_geofence"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLEARED = "cleared"


class AlertDeliveryChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"


class AlertDeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


class AlertActionType(str, Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLEARED = "cleared"


class UnauthorizedGeofenceTrigger(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


class ExportJobFormat(str, Enum):
    CSV = "csv"


class ExportJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DataLifecycleRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text())
    role: Mapped[str] = mapped_column(String(32), default=UserRole.GENERAL_USER.value)
    status: Mapped[str] = mapped_column(String(16), default=UserStatus.ACTIVE.value)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    refresh_sessions: Mapped[list[RefreshSession]] = relationship(back_populates="user")


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[User] = relationship(back_populates="refresh_sessions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action_category: Mapped[str] = mapped_column(String(64))
    action_type: Mapped[str] = mapped_column(String(128), index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    timezone_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    floors: Mapped[list[Floor]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("site_id", "name", name="uq_floors_site_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    level_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    scale_point_a: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    scale_point_b: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    scale_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    scale_pixels_per_meter: Mapped[float | None] = mapped_column(Float, nullable=True)
    scale_configured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    site: Mapped[Site] = relationship(back_populates="floors")
    floor_plan_asset: Mapped[FloorPlanAsset | None] = relationship(
        back_populates="floor",
        cascade="all, delete-orphan",
        uselist=False,
    )
    areas: Mapped[list[SpatialArea]] = relationship(
        back_populates="floor",
        cascade="all, delete-orphan",
    )
    gateways: Mapped[list[Gateway]] = relationship(
        back_populates="floor",
        cascade="all, delete-orphan",
    )


class FloorPlanAsset(Base):
    __tablename__ = "floor_plan_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), unique=True, index=True)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(64))
    width_px: Mapped[int] = mapped_column(Integer)
    height_px: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    floor: Mapped[Floor] = relationship(back_populates="floor_plan_asset")


class SpatialArea(Base):
    __tablename__ = "spatial_areas"
    __table_args__ = (UniqueConstraint("floor_id", "name", name="uq_spatial_areas_floor_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    area_type: Mapped[str] = mapped_column(String(32))
    geometry: Mapped[list[dict[str, float]]] = mapped_column(JSON)
    sla_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_participation: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    floor: Mapped[Floor] = relationship(back_populates="areas")


class Gateway(Base):
    __tablename__ = "gateways"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    gateway_identifier: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    hardware_tier: Mapped[str] = mapped_column(String(32))
    placement_x: Mapped[float] = mapped_column(Float)
    placement_y: Mapped[float] = mapped_column(Float)
    premium_modality: Mapped[str | None] = mapped_column(String(32), nullable=True)
    premium_mounting_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    premium_mounting_angle_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_calibration_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    premium_calibration_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    floor: Mapped[Floor] = relationship(back_populates="gateways")
    raw_readings: Mapped[list[RawReading]] = relationship(
        back_populates="gateway",
        cascade="all, delete-orphan",
    )
    premium_raw_measurements: Mapped[list[PremiumRawMeasurement]] = relationship(
        back_populates="gateway",
        cascade="all, delete-orphan",
    )
    latest_heartbeat: Mapped[GatewayHeartbeat | None] = relationship(
        back_populates="gateway",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AssetTag(Base):
    __tablename__ = "asset_tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tag_identifier: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    asset_category: Mapped[str] = mapped_column(String(80))
    update_rate_profile: Mapped[str] = mapped_column(String(32))
    battery_profile: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    raw_readings: Mapped[list[RawReading]] = relationship(back_populates="asset_tag")
    premium_raw_measurements: Mapped[list[PremiumRawMeasurement]] = relationship(
        back_populates="asset_tag"
    )
    current_location: Mapped[AssetCurrentLocation | None] = relationship(
        back_populates="asset_tag",
        cascade="all, delete-orphan",
        uselist=False,
    )
    location_history: Mapped[list[AssetLocationHistory]] = relationship(
        back_populates="asset_tag",
        cascade="all, delete-orphan",
    )


class AssetTagImportSession(Base):
    __tablename__ = "asset_tag_import_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    rows: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RawReading(Base):
    __tablename__ = "raw_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    gateway_id: Mapped[str] = mapped_column(ForeignKey("gateways.id"), index=True)
    asset_tag_id: Mapped[str | None] = mapped_column(ForeignKey("asset_tags.id"), nullable=True)
    tag_identifier: Mapped[str] = mapped_column(String(120), index=True)
    message_id: Mapped[str] = mapped_column(String(120), index=True)
    broker_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    gateway_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    firmware_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rssi: Mapped[int] = mapped_column(Integer)
    tx_power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel: Mapped[int | None] = mapped_column(Integer, nullable=True)

    gateway: Mapped[Gateway] = relationship(back_populates="raw_readings")
    asset_tag: Mapped[AssetTag | None] = relationship(back_populates="raw_readings")


class PremiumRawMeasurement(Base):
    __tablename__ = "premium_raw_measurements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    gateway_id: Mapped[str] = mapped_column(ForeignKey("gateways.id"), index=True)
    asset_tag_id: Mapped[str | None] = mapped_column(ForeignKey("asset_tags.id"), nullable=True)
    tag_identifier: Mapped[str] = mapped_column(String(120), index=True)
    message_id: Mapped[str] = mapped_column(String(120), index=True)
    sequence_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    broker_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    gateway_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    firmware_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), index=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    azimuth_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    gateway: Mapped[Gateway] = relationship(back_populates="premium_raw_measurements")
    asset_tag: Mapped[AssetTag | None] = relationship(back_populates="premium_raw_measurements")


class AssetCurrentLocation(Base):
    __tablename__ = "asset_current_locations"

    asset_tag_id: Mapped[str] = mapped_column(ForeignKey("asset_tags.id"), primary_key=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("spatial_areas.id"), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    location_type: Mapped[str] = mapped_column(String(16))
    coordinate_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    coordinate_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(16))
    confidence_score: Mapped[float] = mapped_column(Float)
    source_tier: Mapped[str] = mapped_column(
        String(32),
        default=GatewayHardwareTier.ECONOMIC.value,
    )
    source_modality: Mapped[str] = mapped_column(
        String(32),
        default=LocationSourceModality.BLE_RSSI.value,
    )
    precision_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_gateway_count: Mapped[int] = mapped_column(Integer)
    source_reading_count: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    asset_tag: Mapped[AssetTag] = relationship(back_populates="current_location")
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea | None] = relationship()


class AssetLocationHistory(Base):
    __tablename__ = "asset_location_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_tag_id: Mapped[str] = mapped_column(ForeignKey("asset_tags.id"), index=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("spatial_areas.id"), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    location_type: Mapped[str] = mapped_column(String(16))
    coordinate_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    coordinate_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(16))
    confidence_score: Mapped[float] = mapped_column(Float)
    source_tier: Mapped[str] = mapped_column(
        String(32),
        default=GatewayHardwareTier.ECONOMIC.value,
    )
    source_modality: Mapped[str] = mapped_column(
        String(32),
        default=LocationSourceModality.BLE_RSSI.value,
    )
    precision_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_gateway_count: Mapped[int] = mapped_column(Integer)
    source_reading_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset_tag: Mapped[AssetTag] = relationship(back_populates="location_history")
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea | None] = relationship()


class DerivedZoneTransitionEvent(Base):
    __tablename__ = "derived_zone_transition_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_tag_id: Mapped[str] = mapped_column(ForeignKey("asset_tags.id"), index=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("spatial_areas.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(16), index=True)
    transition_boundary_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset_tag: Mapped[AssetTag] = relationship()
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea] = relationship()


class DerivedZoneDwellRecord(Base):
    __tablename__ = "derived_zone_dwell_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_tag_id: Mapped[str] = mapped_column(ForeignKey("asset_tags.id"), index=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("spatial_areas.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[float] = mapped_column(Float)
    closure_reason: Mapped[str] = mapped_column(String(32))
    entry_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("derived_zone_transition_events.id"),
        nullable=True,
    )
    exit_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("derived_zone_transition_events.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset_tag: Mapped[AssetTag] = relationship()
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea] = relationship()


class AssetZoneOccupancy(Base):
    __tablename__ = "asset_zone_occupancies"

    asset_tag_id: Mapped[str] = mapped_column(ForeignKey("asset_tags.id"), primary_key=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("spatial_areas.id"), index=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    entry_event_id: Mapped[str] = mapped_column(ForeignKey("derived_zone_transition_events.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    asset_tag: Mapped[AssetTag] = relationship()
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea] = relationship()
    entry_event: Mapped[DerivedZoneTransitionEvent] = relationship()


class TableServiceTimerState(Base):
    __tablename__ = "table_service_timer_states"

    table_area_id: Mapped[str] = mapped_column(
        ForeignKey("spatial_areas.id"),
        primary_key=True,
    )
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default=TableServiceTimerStatus.IDLE.value)
    active_visit_count: Mapped[int] = mapped_column(Integer, default=0)
    active_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_entry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_exit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_visit_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_visit_ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_visit_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    table_area: Mapped[SpatialArea] = relationship()
    floor: Mapped[Floor] = relationship()


class GatewayHeartbeat(Base):
    __tablename__ = "gateway_heartbeats"

    gateway_id: Mapped[str] = mapped_column(ForeignKey("gateways.id"), primary_key=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    gateway_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message_id: Mapped[str] = mapped_column(String(120))
    firmware_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    battery_level_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    gateway: Mapped[Gateway] = relationship(back_populates="latest_heartbeat")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    rule_type: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    site_id: Mapped[str | None] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    floor_id: Mapped[str | None] = mapped_column(
        ForeignKey("floors.id"),
        nullable=True,
        index=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    delivery: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    updated_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    site: Mapped[Site | None] = relationship()
    floor: Mapped[Floor | None] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_user_id])
    updated_by: Mapped[User | None] = relationship(foreign_keys=[updated_by_user_id])


class AlertInstance(Base):
    __tablename__ = "alert_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_id: Mapped[str] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    rule_type: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    scope_key: Mapped[str] = mapped_column(String(255), index=True)
    scope_label: Mapped[str] = mapped_column(String(255))
    site_id: Mapped[str | None] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    floor_id: Mapped[str | None] = mapped_column(
        ForeignKey("floors.id"),
        nullable=True,
        index=True,
    )
    area_id: Mapped[str | None] = mapped_column(
        ForeignKey("spatial_areas.id"),
        nullable=True,
        index=True,
    )
    asset_tag_id: Mapped[str | None] = mapped_column(
        ForeignKey("asset_tags.id"),
        nullable=True,
        index=True,
    )
    condition_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    context_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    first_triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    rule: Mapped[AlertRule] = relationship()
    site: Mapped[Site | None] = relationship()
    floor: Mapped[Floor | None] = relationship()
    area: Mapped[SpatialArea | None] = relationship()
    asset_tag: Mapped[AssetTag | None] = relationship()
    acknowledged_by: Mapped[User | None] = relationship(foreign_keys=[acknowledged_by_user_id])
    resolved_by: Mapped[User | None] = relationship(foreign_keys=[resolved_by_user_id])


class AlertAction(Base):
    __tablename__ = "alert_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    alert_id: Mapped[str] = mapped_column(ForeignKey("alert_instances.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(32), index=True)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    actor_display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    alert: Mapped[AlertInstance] = relationship()
    actor: Mapped[User | None] = relationship()


class AlertNotificationDelivery(Base):
    __tablename__ = "alert_notification_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    alert_id: Mapped[str] = mapped_column(ForeignKey("alert_instances.id"), index=True)
    channel: Mapped[str] = mapped_column(String(16), index=True)
    destination: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(16), index=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    alert: Mapped[AlertInstance] = relationship()


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    requested_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    report_kind: Mapped[str] = mapped_column(String(32), index=True)
    export_format: Mapped[str] = mapped_column(String(16), default=ExportJobFormat.CSV.value)
    status: Mapped[str] = mapped_column(
        String(16),
        default=ExportJobStatus.PENDING.value,
        index=True,
    )
    floor_id: Mapped[str | None] = mapped_column(ForeignKey("floors.id"), nullable=True, index=True)
    site_id: Mapped[str | None] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    report_params: Mapped[dict[str, Any]] = mapped_column(JSON)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    requested_by: Mapped[User] = relationship()
    floor: Mapped[Floor | None] = relationship()
    site: Mapped[Site | None] = relationship()


class DataLifecycleRun(Base):
    __tablename__ = "data_lifecycle_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    requested_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(16),
        default=DataLifecycleRunStatus.PENDING.value,
        index=True,
    )
    retention_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    rollup_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requested_by: Mapped[User] = relationship()


class AnalyticsHeatmapHourlyRollup(Base):
    __tablename__ = "analytics_heatmap_hourly_rollups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    asset_category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    bucket_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    grid_columns: Mapped[int] = mapped_column(Integer)
    grid_rows: Mapped[int] = mapped_column(Integer)
    row_index: Mapped[int] = mapped_column(Integer)
    column_index: Mapped[int] = mapped_column(Integer)
    sample_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    floor: Mapped[Floor] = relationship()


class AnalyticsTableSlaHourlyRollup(Base):
    __tablename__ = "analytics_table_sla_hourly_rollups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"), index=True)
    table_area_id: Mapped[str] = mapped_column(ForeignKey("spatial_areas.id"), index=True)
    bucket_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_visit_count: Mapped[int] = mapped_column(Integer)
    breach_count: Mapped[int] = mapped_column(Integer)
    avg_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    floor: Mapped[Floor] = relationship()
    table_area: Mapped[SpatialArea] = relationship()
