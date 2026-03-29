from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from rtls_api.models import (
    AlertActionType,
    AlertDeliveryChannel,
    AlertDeliveryStatus,
    AlertRuleType,
    AlertSeverity,
    AlertStatus,
    AssetBatteryProfile,
    AssetLocationType,
    AssetUpdateRateProfile,
    DerivedZoneEventType,
    DwellClosureReason,
    GatewayHardwareTier,
    GatewayHealthStatus,
    LocationConfidenceLevel,
    SpatialAreaType,
    TableServiceTimerStatus,
    UnauthorizedGeofenceTrigger,
    UserRole,
    UserStatus,
)


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


class GatewayCreateRequest(BaseModel):
    gateway_identifier: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=120)
    hardware_tier: GatewayHardwareTier
    placement: SpatialPoint
    notes: str | None = Field(default=None, max_length=500)


class GatewayUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    hardware_tier: GatewayHardwareTier | None = None
    placement: SpatialPoint | None = None
    notes: str | None = Field(default=None, max_length=500)


class AssetTagCreateRequest(BaseModel):
    tag_identifier: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=120)
    asset_category: str = Field(min_length=1, max_length=80)
    update_rate_profile: AssetUpdateRateProfile
    battery_profile: AssetBatteryProfile


class AssetTagUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    asset_category: str | None = Field(default=None, min_length=1, max_length=80)
    update_rate_profile: AssetUpdateRateProfile | None = None
    battery_profile: AssetBatteryProfile | None = None


class AssetTagImportConfirmRequest(BaseModel):
    import_id: str = Field(min_length=1, max_length=64)


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


class GatewayResponse(BaseModel):
    id: str
    floor_id: str
    gateway_identifier: str
    display_name: str
    hardware_tier: GatewayHardwareTier
    placement: SpatialPoint
    notes: str | None


class GatewayHealthResponse(BaseModel):
    gateway_id: str
    floor_id: str
    floor_name: str
    gateway_identifier: str
    display_name: str
    hardware_tier: GatewayHardwareTier
    status: GatewayHealthStatus
    last_seen_at: datetime
    gateway_timestamp: datetime | None
    message_id: str
    firmware_version: str | None
    battery_level_percent: float | None


class OperationsOverviewKpisResponse(BaseModel):
    active_assets: int = Field(ge=0)
    low_confidence_assets: int = Field(ge=0)
    restricted_zone_assets: int = Field(ge=0)
    stale_gateways: int = Field(ge=0)


class OperationsPriorityItemResponse(BaseModel):
    id: str
    kind: str
    severity: str
    title: str
    summary: str
    observed_at: datetime
    floor_id: str | None
    asset_tag_id: str | None
    gateway_id: str | None


class OperationsMapPreviewResponse(BaseModel):
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    floor_plan: FloorPlanAssetResponse | None
    areas: list[SpatialAreaResponse]
    gateways: list[GatewayResponse]
    locations: list[AssetLocationResponse]


class OperationsOverviewResponse(BaseModel):
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    feed_status: str
    feed_updated_at: datetime | None
    kpis: OperationsOverviewKpisResponse
    priority_items: list[OperationsPriorityItemResponse]
    gateway_snapshot: list[GatewayHealthResponse]
    map_preview: OperationsMapPreviewResponse


class AssetTagResponse(BaseModel):
    id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    update_rate_profile: AssetUpdateRateProfile
    battery_profile: AssetBatteryProfile


class AssetTagImportPreviewRecord(BaseModel):
    tag_identifier: str
    display_name: str
    asset_category: str
    update_rate_profile: AssetUpdateRateProfile
    battery_profile: AssetBatteryProfile


class AssetTagImportValidationRow(BaseModel):
    row_number: int
    values: dict[str, str]
    errors: list[str]


class AssetTagImportValidateResponse(BaseModel):
    import_id: str | None
    total_rows: int
    valid_row_count: int
    invalid_row_count: int
    valid_rows: list[AssetTagImportPreviewRecord]
    invalid_rows: list[AssetTagImportValidationRow]


class AssetTagImportConfirmResponse(BaseModel):
    created_count: int
    assets: list[AssetTagResponse]


class FloorDetailResponse(BaseModel):
    id: str
    site_id: str
    name: str
    level_label: str | None
    scale_configured: bool
    floor_plan: FloorPlanAssetResponse | None
    scale: FloorScaleResponse | None
    areas: list[SpatialAreaResponse]
    gateways: list[GatewayResponse]


class AssetLocationResponse(BaseModel):
    asset_tag_id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    floor_id: str
    floor_name: str
    site_id: str
    site_name: str
    observed_at: datetime
    location_type: AssetLocationType
    point: SpatialPoint | None
    zone_id: str | None
    zone_name: str | None
    confidence_level: LocationConfidenceLevel
    confidence_score: float = Field(ge=0, le=1)
    source_gateway_count: int = Field(ge=0)
    source_reading_count: int = Field(ge=0)


class AssetLocationHistoryResponse(AssetLocationResponse):
    id: str


class LiveLocationStreamEvent(BaseModel):
    event: str = "location.updated"
    location: AssetLocationResponse


class DerivedZoneTransitionEventResponse(BaseModel):
    id: str
    asset_tag_id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    floor_id: str
    floor_name: str
    site_id: str
    site_name: str
    zone_id: str
    zone_name: str
    observed_at: datetime
    event_type: DerivedZoneEventType
    transition_boundary_id: str


class DerivedZoneDwellRecordResponse(BaseModel):
    id: str
    asset_tag_id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    floor_id: str
    floor_name: str
    site_id: str
    site_name: str
    zone_id: str
    zone_name: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float = Field(ge=0)
    closure_reason: DwellClosureReason


class TableServiceTimerStateResponse(BaseModel):
    table_area_id: str
    table_name: str
    floor_id: str
    floor_name: str
    site_id: str
    site_name: str
    status: TableServiceTimerStatus
    active_visit_count: int = Field(ge=0)
    boundary_at: datetime | None
    elapsed_seconds: float = Field(ge=0)
    active_since: datetime | None
    last_entry_at: datetime | None
    last_exit_at: datetime | None
    last_visit_started_at: datetime | None
    last_visit_ended_at: datetime | None
    last_visit_duration_seconds: float | None = Field(default=None, ge=0)


class RoundTripMeasurementResponse(BaseModel):
    asset_tag_id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    floor_id: str
    floor_name: str
    site_id: str
    site_name: str
    origin_zone_id: str
    origin_zone_name: str
    destination_zone_id: str
    destination_zone_name: str
    origin_entered_at: datetime
    destination_entered_at: datetime
    completed_at: datetime
    outbound_seconds: float = Field(ge=0)
    return_seconds: float = Field(ge=0)
    total_seconds: float = Field(ge=0)


class AnalyticsHeatmapCellResponse(BaseModel):
    row: int = Field(ge=0)
    column: int = Field(ge=0)
    center: SpatialPoint
    sample_count: int = Field(ge=1)
    intensity: float = Field(ge=0, le=1)


class AnalyticsHeatmapResponse(BaseModel):
    site_id: str
    site_name: str
    floor_id: str
    floor_name: str
    asset_category: str | None
    start_at: datetime
    end_at: datetime
    grid_columns: int = Field(ge=1)
    grid_rows: int = Field(ge=1)
    total_samples: int = Field(ge=0)
    max_density: int = Field(ge=0)
    cells: list[AnalyticsHeatmapCellResponse]


class AnalyticsTrajectoryResponse(BaseModel):
    asset_tag_id: str
    tag_identifier: str
    display_name: str
    asset_category: str
    site_id: str
    site_name: str
    floor_id: str
    floor_name: str
    start_at: datetime
    end_at: datetime
    points: list[AssetLocationHistoryResponse]


class AnalyticsSummaryResponse(BaseModel):
    sample_count: int = Field(ge=0)
    avg_duration_seconds: float | None = Field(default=None, ge=0)
    max_duration_seconds: float | None = Field(default=None, ge=0)


class AnalyticsDwellSummaryResponse(AnalyticsSummaryResponse):
    threshold_seconds: float | None = Field(default=None, gt=0)
    threshold_source: str
    threshold_breach_count: int = Field(ge=0)


class AnalyticsDwellRecordResponse(DerivedZoneDwellRecordResponse):
    threshold_seconds: float | None = Field(default=None, gt=0)
    threshold_breached: bool


class AnalyticsDwellReportResponse(BaseModel):
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    zone_id: str | None
    zone_name: str | None
    asset_category: str | None
    start_at: datetime
    end_at: datetime
    summary: AnalyticsDwellSummaryResponse
    records: list[AnalyticsDwellRecordResponse]


class AnalyticsRoundTripSummaryResponse(AnalyticsSummaryResponse):
    avg_outbound_seconds: float | None = Field(default=None, ge=0)
    avg_return_seconds: float | None = Field(default=None, ge=0)


class AnalyticsRoundTripReportResponse(BaseModel):
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    origin_zone_id: str
    origin_zone_name: str
    destination_zone_id: str
    destination_zone_name: str
    asset_category: str | None
    start_at: datetime
    end_at: datetime
    summary: AnalyticsRoundTripSummaryResponse
    records: list[RoundTripMeasurementResponse]


class AnalyticsSlaTrendBucketResponse(BaseModel):
    bucket_started_at: datetime
    completed_visit_count: int = Field(ge=0)
    breach_count: int = Field(ge=0)
    avg_duration_seconds: float | None = Field(default=None, ge=0)
    max_duration_seconds: float | None = Field(default=None, ge=0)


class AnalyticsSlaTrendResponse(BaseModel):
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    table_area_id: str
    table_name: str
    start_at: datetime
    end_at: datetime
    bucket_minutes: int = Field(ge=1)
    threshold_source: str
    threshold_seconds: float | None = Field(default=None, gt=0)
    current_timer: TableServiceTimerStateResponse | None
    buckets: list[AnalyticsSlaTrendBucketResponse]


class AlertRuleUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rule_type: AlertRuleType
    enabled: bool = True
    threshold_seconds: float | None = Field(default=None, gt=0)
    table_area_ids: list[str] | None = None
    area_ids: list[str] | None = None
    trigger_on: UnauthorizedGeofenceTrigger | None = None
    asset_category: str | None = Field(default=None, min_length=1, max_length=80)
    notify_in_app: bool = True
    notify_email: bool = False
    email_recipients: list[EmailStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rule_shape(self) -> AlertRuleUpsertRequest:
        if not self.notify_in_app:
            raise ValueError("In-app delivery must stay enabled for delivered alerts")
        if self.notify_email and not self.email_recipients:
            raise ValueError("Email recipients are required when email delivery is enabled")
        if self.rule_type == AlertRuleType.TABLE_SLA:
            if self.threshold_seconds is None:
                raise ValueError("threshold_seconds is required for table SLA rules")
            if not self.table_area_ids:
                raise ValueError("table_area_ids is required for table SLA rules")
            return self
        if not self.area_ids:
            raise ValueError("area_ids is required for unauthorized geofence rules")
        if self.trigger_on is None:
            raise ValueError("trigger_on is required for unauthorized geofence rules")
        return self


class AlertRuleDeliveryResponse(BaseModel):
    in_app: bool
    email: bool
    email_recipients: list[EmailStr]


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    rule_type: AlertRuleType
    severity: AlertSeverity
    enabled: bool
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    config: dict[str, object]
    delivery: AlertRuleDeliveryResponse
    created_at: datetime
    updated_at: datetime


class AlertNotificationSummaryResponse(BaseModel):
    unresolved_count: int = Field(ge=0)
    unread_count: int = Field(ge=0)
    active_critical_count: int = Field(ge=0)
    active_warning_count: int = Field(ge=0)
    latest_alert_at: datetime | None


class AlertListItemResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    rule_type: AlertRuleType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    summary: str
    scope_key: str
    scope_label: str
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None
    area_id: str | None
    area_name: str | None
    asset_tag_id: str | None
    asset_label: str | None
    first_triggered_at: datetime
    last_triggered_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    cleared_at: datetime | None


class AlertActionResponse(BaseModel):
    id: str
    action_type: AlertActionType
    actor_user_id: str | None
    actor_email: str | None
    actor_display_name: str | None
    notes: str | None
    details: dict[str, object] | None
    created_at: datetime


class AlertNotificationDeliveryResponse(BaseModel):
    id: str
    channel: AlertDeliveryChannel
    destination: str
    status: AlertDeliveryStatus
    error_message: str | None
    read_at: datetime | None
    created_at: datetime


class AlertDetailResponse(AlertListItemResponse):
    condition_key: str | None
    context: dict[str, object] | None
    rule: AlertRuleResponse
    actions: list[AlertActionResponse]
    deliveries: list[AlertNotificationDeliveryResponse]


class AlertActionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)
