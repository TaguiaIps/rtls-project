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
