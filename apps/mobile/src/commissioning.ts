import type {
  AssetTagRecord,
  FloorDetail,
  GatewayRecord,
  SiteRecord,
  SpatialAreaRecord,
  SpatialPoint
} from "@rtls/contracts";

export type CommissioningTargetKind = "gateway" | "asset_tag" | "unknown";

export type CommissioningTarget = {
  kind: CommissioningTargetKind;
  identifier: string;
  displayName: string;
  description: string;
  gateway?: GatewayRecord;
  assetTag?: AssetTagRecord;
};

export type CalibrationWaypoint = {
  id: string;
  label: string;
  point: SpatialPoint;
  kind: "zone" | "gateway" | "default";
};

export type CalibrationProgress = {
  completedCount: number;
  totalCount: number;
  nextWaypoint: CalibrationWaypoint | null;
};

export type CommissioningSessionSummary = {
  target_identifier: string;
  target_kind: CommissioningTargetKind;
  target_display_name: string;
  site_id: string;
  site_name: string;
  floor_id: string;
  floor_name: string;
  zone_id: string | null;
  zone_name: string | null;
  started_at: string;
  completed_at: string;
  elapsed_seconds: number;
  sample_count: number;
  completed_waypoints: number;
  total_waypoints: number;
};

const MAX_COMMISSIONING_SUMMARIES = 5;
const DEFAULT_WAYPOINTS: CalibrationWaypoint[] = [
  { id: "default-1", label: "Entry anchor", point: { x: 0.25, y: 0.25 }, kind: "default" },
  { id: "default-2", label: "Center pass", point: { x: 0.5, y: 0.5 }, kind: "default" },
  { id: "default-3", label: "Exit anchor", point: { x: 0.75, y: 0.75 }, kind: "default" }
];

export function normalizeIdentifier(value: string) {
  return value.trim().toUpperCase();
}

export function extractIdentifierFromQrPayload(payload: string) {
  const trimmedPayload = payload.trim();
  if (!trimmedPayload) {
    return "";
  }

  const jsonIdentifier = extractIdentifierFromJsonPayload(trimmedPayload);
  if (jsonIdentifier) {
    return normalizeIdentifier(jsonIdentifier);
  }

  const urlIdentifier = extractIdentifierFromUrlPayload(trimmedPayload);
  if (urlIdentifier) {
    return normalizeIdentifier(urlIdentifier);
  }

  return normalizeIdentifier(trimmedPayload);
}

export function resolveCommissioningTarget(
  scannedCode: string,
  gateways: GatewayRecord[],
  assets: AssetTagRecord[]
): CommissioningTarget | null {
  const normalizedCode = extractIdentifierFromQrPayload(scannedCode);
  if (!normalizedCode) {
    return null;
  }

  const gateway = gateways.find(
    (candidate) => normalizeIdentifier(candidate.gateway_identifier) === normalizedCode
  );
  if (gateway) {
    return {
      kind: "gateway",
      identifier: gateway.gateway_identifier,
      displayName: gateway.display_name,
      description: `${gateway.hardware_tier} gateway`,
      gateway
    };
  }

  const assetTag = assets.find(
    (candidate) => normalizeIdentifier(candidate.tag_identifier) === normalizedCode
  );
  if (assetTag) {
    return {
      kind: "asset_tag",
      identifier: assetTag.tag_identifier,
      displayName: assetTag.display_name,
      description: assetTag.asset_category,
      assetTag
    };
  }

  return {
    kind: "unknown",
    identifier: normalizedCode,
    displayName: normalizedCode,
    description: "Unknown device"
  };
}

export function buildCalibrationWaypoints(
  floorDetail: FloorDetail | null,
  selectedZoneId: string | null
): CalibrationWaypoint[] {
  if (!floorDetail) {
    return DEFAULT_WAYPOINTS;
  }

  const zone = floorDetail.areas.find((area) => area.id === selectedZoneId) ?? null;
  const otherAreas = floorDetail.areas.filter(
    (area) => area.id !== selectedZoneId && area.area_type !== "restricted_zone"
  );

  const waypoints: CalibrationWaypoint[] = [];
  if (zone) {
    waypoints.push({
      id: `zone-${zone.id}`,
      label: `${zone.name} anchor`,
      point: areaCentroid(zone),
      kind: "zone"
    });
  }

  for (const gateway of floorDetail.gateways.slice(0, 2)) {
    waypoints.push({
      id: `gateway-${gateway.id}`,
      label: gateway.display_name,
      point: gateway.placement,
      kind: "gateway"
    });
  }

  for (const area of otherAreas.slice(0, 2)) {
    waypoints.push({
      id: `area-${area.id}`,
      label: area.name,
      point: areaCentroid(area),
      kind: "zone"
    });
  }

  const uniqueWaypoints = dedupeWaypoints(waypoints);
  return uniqueWaypoints.length ? uniqueWaypoints : DEFAULT_WAYPOINTS;
}

export function buildCalibrationProgress(
  waypoints: CalibrationWaypoint[],
  captures: SpatialPoint[]
): CalibrationProgress {
  const completedWaypointIds = new Set(
    waypoints
      .filter((waypoint) =>
        captures.some((capture) => distanceBetweenPoints(capture, waypoint.point) <= 0.08)
      )
      .map((waypoint) => waypoint.id)
  );

  const nextWaypoint =
    waypoints.find((waypoint) => !completedWaypointIds.has(waypoint.id)) ?? null;

  return {
    completedCount: completedWaypointIds.size,
    totalCount: waypoints.length,
    nextWaypoint
  };
}

export function upsertCommissioningSummary(
  entries: CommissioningSessionSummary[],
  summary: CommissioningSessionSummary
) {
  const nextEntries = entries.filter(
    (entry) =>
      !(
        entry.target_identifier === summary.target_identifier &&
        entry.floor_id === summary.floor_id
      )
  );
  nextEntries.unshift(summary);
  return nextEntries.slice(0, MAX_COMMISSIONING_SUMMARIES);
}

export function buildCommissioningSummary(params: {
  target: CommissioningTarget;
  site: SiteRecord;
  floor: FloorDetail;
  zone: SpatialAreaRecord | null;
  startedAt: string;
  completedAt: string;
  captures: SpatialPoint[];
  progress: CalibrationProgress;
}): CommissioningSessionSummary {
  const elapsedSeconds = Math.max(
    0,
    Math.round(
      (new Date(params.completedAt).getTime() - new Date(params.startedAt).getTime()) / 1000
    )
  );

  return {
    target_identifier: params.target.identifier,
    target_kind: params.target.kind,
    target_display_name: params.target.displayName,
    site_id: params.site.id,
    site_name: params.site.name,
    floor_id: params.floor.id,
    floor_name: params.floor.name,
    zone_id: params.zone?.id ?? null,
    zone_name: params.zone?.name ?? null,
    started_at: params.startedAt,
    completed_at: params.completedAt,
    elapsed_seconds: elapsedSeconds,
    sample_count: params.captures.length,
    completed_waypoints: params.progress.completedCount,
    total_waypoints: params.progress.totalCount
  };
}

export function formatElapsedDuration(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes <= 0) {
    return `${seconds}s`;
  }
  return `${minutes}m ${seconds}s`;
}

export function describeTargetKind(kind: CommissioningTargetKind) {
  switch (kind) {
    case "gateway":
      return "Gateway";
    case "asset_tag":
      return "Asset Tag";
    default:
      return "Unknown";
  }
}

function areaCentroid(area: SpatialAreaRecord): SpatialPoint {
  if (!area.points.length) {
    return { x: 0.5, y: 0.5 };
  }

  const totals = area.points.reduce(
    (current, point) => ({
      x: current.x + point.x,
      y: current.y + point.y
    }),
    { x: 0, y: 0 }
  );

  return {
    x: clampRelativeValue(totals.x / area.points.length),
    y: clampRelativeValue(totals.y / area.points.length)
  };
}

function extractIdentifierFromJsonPayload(payload: string) {
  if (!payload.startsWith("{")) {
    return "";
  }

  try {
    const parsed = JSON.parse(payload) as Record<string, unknown>;
    const supportedKeys = [
      "identifier",
      "gateway_id",
      "gatewayId",
      "tag_id",
      "tagId",
      "device_id",
      "deviceId"
    ];

    for (const key of supportedKeys) {
      const value = parsed[key];
      if (typeof value === "string" && value.trim()) {
        return value;
      }
    }
  } catch {
    return "";
  }

  return "";
}

function extractIdentifierFromUrlPayload(payload: string) {
  if (!payload.includes("://")) {
    return "";
  }

  try {
    const parsed = new URL(payload);
    const supportedKeys = ["identifier", "gateway_id", "tag_id", "device_id", "id"];
    for (const key of supportedKeys) {
      const value = parsed.searchParams.get(key);
      if (value && value.trim()) {
        return value;
      }
    }

    const pathSegments = parsed.pathname
      .split("/")
      .map((segment) => segment.trim())
      .filter(Boolean);
    const lastSegment = pathSegments[pathSegments.length - 1];
    return lastSegment ?? "";
  } catch {
    return "";
  }
}

function dedupeWaypoints(waypoints: CalibrationWaypoint[]) {
  const seen = new Set<string>();
  const nextWaypoints: CalibrationWaypoint[] = [];

  for (const waypoint of waypoints) {
    const key = `${waypoint.label}:${waypoint.point.x.toFixed(3)}:${waypoint.point.y.toFixed(3)}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    nextWaypoints.push({
      ...waypoint,
      point: {
        x: clampRelativeValue(waypoint.point.x),
        y: clampRelativeValue(waypoint.point.y)
      }
    });
  }

  return nextWaypoints;
}

function distanceBetweenPoints(pointA: SpatialPoint, pointB: SpatialPoint) {
  return Math.hypot(pointA.x - pointB.x, pointA.y - pointB.y);
}

function clampRelativeValue(value: number) {
  return Math.max(0.02, Math.min(0.98, value));
}
