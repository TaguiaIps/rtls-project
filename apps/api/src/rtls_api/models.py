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
