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
    source_gateway_count: Mapped[int] = mapped_column(Integer)
    source_reading_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset_tag: Mapped[AssetTag] = relationship(back_populates="location_history")
    floor: Mapped[Floor] = relationship()
    zone: Mapped[SpatialArea | None] = relationship()


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
