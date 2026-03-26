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
