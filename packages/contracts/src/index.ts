export type RuntimeServiceName =
  | "web"
  | "api"
  | "worker"
  | "mqtt-broker"
  | "redis"
  | "timescaledb"
  | "object-storage";

export interface RuntimeServiceDefinition {
  name: RuntimeServiceName;
  label: string;
  purpose: string;
}

export type UserRole = "Administrator" | "General User";

export type UserStatus = "active" | "disabled";

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
  role: UserRole;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  display_name: string | null;
  role: UserRole;
  status: UserStatus;
}

export type SpatialAreaType = "zone" | "table" | "restricted_zone" | "poi";
export type GatewayHardwareTier = "Economic" | "Premium";
export type AssetUpdateRateProfile = "slow" | "balanced" | "realtime";
export type AssetBatteryProfile = "long_life" | "standard" | "performance";
export type AssetLocationType = "point" | "zone";
export type LocationConfidenceLevel = "high" | "medium" | "low";
export type GatewayHealthStatus = "healthy" | "stale";
export type OperationsFeedStatus = "live" | "degraded" | "empty";
export type OperationsPrioritySeverity = "critical" | "warning";
export type OperationsPriorityKind =
  | "restricted_zone_asset"
  | "low_confidence_asset"
  | "stale_gateway";
export type AlertRuleType = "table_sla" | "unauthorized_geofence";
export type AlertSeverity = "critical" | "warning";
export type AlertStatus = "open" | "acknowledged" | "resolved" | "cleared";
export type AlertDeliveryChannel = "in_app" | "email";
export type AlertDeliveryStatus = "delivered" | "failed" | "skipped";
export type AlertActionType = "triggered" | "acknowledged" | "resolved" | "cleared";
export type UnauthorizedGeofenceTrigger = "entry" | "exit";

export interface FloorSummary {
  id: string;
  site_id: string;
  name: string;
  level_label: string | null;
  has_floor_plan: boolean;
  scale_configured: boolean;
}

export interface SiteRecord {
  id: string;
  name: string;
  timezone_name: string | null;
  floors: FloorSummary[];
}

export interface SpatialPoint {
  x: number;
  y: number;
}

export interface FloorPlanAsset {
  id: string;
  floor_id: string;
  original_filename: string;
  mime_type: string;
  width_px: number;
  height_px: number;
  file_download_path: string;
}

export interface FloorScale {
  point_a: SpatialPoint;
  point_b: SpatialPoint;
  real_world_distance_m: number;
  pixels_per_meter: number;
  configured_at: string;
}

export interface SpatialAreaRecord {
  id: string;
  floor_id: string;
  name: string;
  area_type: SpatialAreaType;
  points: SpatialPoint[];
  sla_eligible: boolean;
  alert_participation: boolean;
}

export interface GatewayRecord {
  id: string;
  floor_id: string;
  gateway_identifier: string;
  display_name: string;
  hardware_tier: GatewayHardwareTier;
  placement: SpatialPoint;
  notes: string | null;
}

export interface GatewayHealthRecord {
  gateway_id: string;
  floor_id: string;
  floor_name: string;
  gateway_identifier: string;
  display_name: string;
  hardware_tier: GatewayHardwareTier;
  status: GatewayHealthStatus;
  last_seen_at: string;
  gateway_timestamp: string | null;
  message_id: string;
  firmware_version: string | null;
  battery_level_percent: number | null;
}

export interface AssetTagRecord {
  id: string;
  tag_identifier: string;
  display_name: string;
  asset_category: string;
  update_rate_profile: AssetUpdateRateProfile;
  battery_profile: AssetBatteryProfile;
}

export interface AssetTagImportPreviewRecord {
  tag_identifier: string;
  display_name: string;
  asset_category: string;
  update_rate_profile: AssetUpdateRateProfile;
  battery_profile: AssetBatteryProfile;
}

export interface AssetTagImportValidationRow {
  row_number: number;
  values: Record<string, string>;
  errors: string[];
}

export interface AssetTagImportValidateResult {
  import_id: string | null;
  total_rows: number;
  valid_row_count: number;
  invalid_row_count: number;
  valid_rows: AssetTagImportPreviewRecord[];
  invalid_rows: AssetTagImportValidationRow[];
}

export interface AssetTagImportConfirmResult {
  created_count: number;
  assets: AssetTagRecord[];
}

export interface FloorDetail {
  id: string;
  site_id: string;
  name: string;
  level_label: string | null;
  scale_configured: boolean;
  floor_plan: FloorPlanAsset | null;
  scale: FloorScale | null;
  areas: SpatialAreaRecord[];
  gateways: GatewayRecord[];
}

export interface AdminSummary {
  current_user: AuthenticatedUser;
  managed_roles: UserRole[];
}

export interface AssetLocationRecord {
  asset_tag_id: string;
  tag_identifier: string;
  display_name: string;
  asset_category: string;
  floor_id: string;
  floor_name: string;
  site_id: string;
  site_name: string;
  observed_at: string;
  location_type: AssetLocationType;
  point: SpatialPoint | null;
  zone_id: string | null;
  zone_name: string | null;
  confidence_level: LocationConfidenceLevel;
  confidence_score: number;
  source_gateway_count: number;
  source_reading_count: number;
}

export interface AssetLocationHistoryRecord extends AssetLocationRecord {
  id: string;
}

export interface LiveLocationStreamEvent {
  event: "location.updated";
  location: AssetLocationRecord;
}

export interface OperationsOverviewKpis {
  active_assets: number;
  low_confidence_assets: number;
  restricted_zone_assets: number;
  stale_gateways: number;
}

export interface OperationsPriorityItem {
  id: string;
  kind: OperationsPriorityKind;
  severity: OperationsPrioritySeverity;
  title: string;
  summary: string;
  observed_at: string;
  floor_id: string | null;
  asset_tag_id: string | null;
  gateway_id: string | null;
}

export interface OperationsMapPreview {
  site_id: string | null;
  site_name: string | null;
  floor_id: string | null;
  floor_name: string | null;
  floor_plan: FloorPlanAsset | null;
  areas: SpatialAreaRecord[];
  gateways: GatewayRecord[];
  locations: AssetLocationRecord[];
}

export interface OperationsOverviewRecord {
  site_id: string | null;
  site_name: string | null;
  floor_id: string | null;
  floor_name: string | null;
  feed_status: OperationsFeedStatus;
  feed_updated_at: string | null;
  kpis: OperationsOverviewKpis;
  priority_items: OperationsPriorityItem[];
  gateway_snapshot: GatewayHealthRecord[];
  map_preview: OperationsMapPreview;
}

export interface AlertRuleDelivery {
  in_app: boolean;
  email: boolean;
  email_recipients: string[];
}

export interface TableSlaAlertRuleConfig {
  threshold_seconds: number;
  table_area_ids: string[];
}

export interface UnauthorizedGeofenceAlertRuleConfig {
  area_ids: string[];
  trigger_on: UnauthorizedGeofenceTrigger;
  asset_category: string | null;
}

export type AlertRuleConfig = TableSlaAlertRuleConfig | UnauthorizedGeofenceAlertRuleConfig;

export interface AlertRuleRecord {
  id: string;
  name: string;
  rule_type: AlertRuleType;
  severity: AlertSeverity;
  enabled: boolean;
  site_id: string | null;
  site_name: string | null;
  floor_id: string | null;
  floor_name: string | null;
  config: AlertRuleConfig;
  delivery: AlertRuleDelivery;
  created_at: string;
  updated_at: string;
}

export interface AlertNotificationSummaryRecord {
  unresolved_count: number;
  unread_count: number;
  active_critical_count: number;
  active_warning_count: number;
  latest_alert_at: string | null;
}

export interface AlertListItemRecord {
  id: string;
  rule_id: string;
  rule_name: string;
  rule_type: AlertRuleType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  summary: string;
  scope_key: string;
  scope_label: string;
  site_id: string | null;
  site_name: string | null;
  floor_id: string | null;
  floor_name: string | null;
  area_id: string | null;
  area_name: string | null;
  asset_tag_id: string | null;
  asset_label: string | null;
  first_triggered_at: string;
  last_triggered_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  cleared_at: string | null;
}

export interface AlertActionRecord {
  id: string;
  action_type: AlertActionType;
  actor_user_id: string | null;
  actor_email: string | null;
  actor_display_name: string | null;
  notes: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AlertNotificationDeliveryRecord {
  id: string;
  channel: AlertDeliveryChannel;
  destination: string;
  status: AlertDeliveryStatus;
  error_message: string | null;
  read_at: string | null;
  created_at: string;
}

export interface AlertDetailRecord extends AlertListItemRecord {
  condition_key: string | null;
  context: Record<string, unknown> | null;
  rule: AlertRuleRecord;
  actions: AlertActionRecord[];
  deliveries: AlertNotificationDeliveryRecord[];
}

export interface AlertRuleUpsertPayload {
  name: string;
  rule_type: AlertRuleType;
  enabled: boolean;
  threshold_seconds?: number;
  table_area_ids?: string[];
  area_ids?: string[];
  trigger_on?: UnauthorizedGeofenceTrigger;
  asset_category?: string | null;
  notify_in_app: boolean;
  notify_email: boolean;
  email_recipients: string[];
}

export interface AlertActionPayload {
  notes?: string | null;
}
