import type { RuntimeServiceDefinition, UserRole } from "@rtls/contracts";

export const PRODUCT_NAME = "RTLS Analytics Platform";
export const API_BASE_URL = "http://localhost:8000";
export const ROLE_HOME_ROUTE: Record<UserRole, string> = {
  Administrator: "/admin",
  "General User": "/operations"
};

export const LOCAL_STACK_SERVICES: RuntimeServiceDefinition[] = [
  {
    name: "web",
    label: "Web",
    purpose: "Runs the React workspace shell and later operational screens."
  },
  {
    name: "api",
    label: "API",
    purpose: "Hosts FastAPI endpoints and the future realtime gateway."
  },
  {
    name: "worker",
    label: "Worker",
    purpose: "Owns background jobs until later changes split ingest and events."
  },
  {
    name: "mqtt-broker",
    label: "MQTT Broker",
    purpose: "Accepts telemetry from gateways during local integration work."
  },
  {
    name: "redis",
    label: "Redis",
    purpose: "Provides ephemeral coordination, dedupe support, and cache capabilities."
  },
  {
    name: "timescaledb",
    label: "TimescaleDB",
    purpose: "Stores the future operational and time-series data model."
  },
  {
    name: "object-storage",
    label: "Object Storage",
    purpose: "Stores floor plans, export artifacts, and future calibration assets."
  }
];
