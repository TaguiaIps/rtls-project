from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from rtls_api.models import SpatialAreaType, UserRole, UserStatus


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: str


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str | None
    role: str
    status: str


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    role: UserRole | None = None
    status: UserStatus | None = None


class AdminSummaryResponse(BaseModel):
    current_user: CurrentUserResponse
    managed_roles: list[str]


class SpatialPoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class SiteCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    timezone_name: str | None = Field(default=None, max_length=80)


class FloorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    level_label: str | None = Field(default=None, max_length=80)


class FloorScaleUpdateRequest(BaseModel):
    point_a: SpatialPoint
    point_b: SpatialPoint
    real_world_distance_m: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_distinct_points(self) -> FloorScaleUpdateRequest:
        if self.point_a == self.point_b:
            raise ValueError("Scale reference points must be distinct")
        return self


class SpatialAreaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    area_type: SpatialAreaType
    points: list[SpatialPoint]
    sla_eligible: bool = False
    alert_participation: bool = True

    @model_validator(mode="after")
    def validate_polygon(self) -> SpatialAreaCreateRequest:
        if len(self.points) < 3:
            raise ValueError("Polygon must contain at least three points")
        return self


class SpatialAreaUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    area_type: SpatialAreaType | None = None
    points: list[SpatialPoint] | None = None
    sla_eligible: bool | None = None
    alert_participation: bool | None = None

    @model_validator(mode="after")
    def validate_polygon(self) -> SpatialAreaUpdateRequest:
        if self.points is not None and len(self.points) < 3:
            raise ValueError("Polygon must contain at least three points")
        return self


class FloorSummaryResponse(BaseModel):
    id: str
    site_id: str
    name: str
    level_label: str | None
    has_floor_plan: bool
    scale_configured: bool


class SiteResponse(BaseModel):
    id: str
    name: str
    timezone_name: str | None
    floors: list[FloorSummaryResponse]


class FloorPlanAssetResponse(BaseModel):
    id: str
    floor_id: str
    original_filename: str
    mime_type: str
    width_px: int
    height_px: int
    file_download_path: str


class FloorScaleResponse(BaseModel):
    point_a: SpatialPoint
    point_b: SpatialPoint
    real_world_distance_m: float
    pixels_per_meter: float
    configured_at: datetime


class SpatialAreaResponse(BaseModel):
    id: str
    floor_id: str
    name: str
    area_type: SpatialAreaType
    points: list[SpatialPoint]
    sla_eligible: bool
    alert_participation: bool


class FloorDetailResponse(BaseModel):
    id: str
    site_id: str
    name: str
    level_label: str | None
    scale_configured: bool
    floor_plan: FloorPlanAssetResponse | None
    scale: FloorScaleResponse | None
    areas: list[SpatialAreaResponse]
