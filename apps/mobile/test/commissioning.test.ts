import { describe, expect, it } from "vitest";
import type {
  AssetTagRecord,
  FloorDetail,
  GatewayRecord,
  SiteRecord,
  SpatialAreaRecord
} from "@rtls/contracts";

import {
  buildCalibrationProgress,
  buildCalibrationWaypoints,
  buildCommissioningSummary,
  extractIdentifierFromQrPayload,
  resolveCommissioningTarget,
  upsertCommissioningSummary
} from "../src/commissioning";

function createSite(): SiteRecord {
  return {
    id: "site-1",
    name: "Flagship",
    timezone_name: "America/Bahia",
    floors: [
      {
        id: "floor-1",
        site_id: "site-1",
        name: "Dining",
        level_label: "L1",
        has_floor_plan: true,
        scale_configured: true
      }
    ]
  };
}

function createGateway(overrides: Partial<GatewayRecord> = {}): GatewayRecord {
  return {
    id: "gateway-1",
    floor_id: "floor-1",
    gateway_identifier: "GW-DINING-01",
    display_name: "Dining Gateway 01",
    hardware_tier: "Economic",
    placement: { x: 0.2, y: 0.3 },
    premium_profile: null,
    notes: null,
    ...overrides
  };
}

function createAsset(overrides: Partial<AssetTagRecord> = {}): AssetTagRecord {
  return {
    id: "asset-1",
    tag_identifier: "TAG-001",
    display_name: "Tray Cart 01",
    asset_category: "Tray Cart",
    update_rate_profile: "balanced",
    battery_profile: "standard",
    ...overrides
  };
}

function createArea(overrides: Partial<SpatialAreaRecord> = {}): SpatialAreaRecord {
  return {
    id: "area-1",
    floor_id: "floor-1",
    name: "Dining South",
    area_type: "zone",
    points: [
      { x: 0.1, y: 0.1 },
      { x: 0.3, y: 0.1 },
      { x: 0.3, y: 0.3 },
      { x: 0.1, y: 0.3 }
    ],
    sla_eligible: false,
    alert_participation: false,
    ...overrides
  };
}

function createFloorDetail(): FloorDetail {
  return {
    id: "floor-1",
    site_id: "site-1",
    name: "Dining",
    level_label: "L1",
    scale_configured: true,
    floor_plan: {
      id: "plan-1",
      floor_id: "floor-1",
      original_filename: "dining.png",
      mime_type: "image/png",
      width_px: 1000,
      height_px: 600,
      file_download_path: "/api/admin/floors/floor-1/floor-plan/file"
    },
    scale: {
      point_a: { x: 0.1, y: 0.1 },
      point_b: { x: 0.9, y: 0.1 },
      real_world_distance_m: 20,
      pixels_per_meter: 40,
      configured_at: "2026-03-29T12:00:00Z"
    },
    areas: [
      createArea(),
      createArea({
        id: "area-2",
        name: "Kitchen Pass",
        points: [
          { x: 0.55, y: 0.2 },
          { x: 0.72, y: 0.2 },
          { x: 0.72, y: 0.38 },
          { x: 0.55, y: 0.38 }
        ]
      })
    ],
    gateways: [
      createGateway(),
      createGateway({
        id: "gateway-2",
        gateway_identifier: "GW-KITCHEN-01",
        display_name: "Kitchen Gateway 01",
        placement: { x: 0.68, y: 0.26 }
      })
    ]
  };
}

describe("commissioning helpers", () => {
  it("resolves known gateways and asset tags from scanned identifiers", () => {
    const floor = createFloorDetail();
    const asset = createAsset();

    expect(
      resolveCommissioningTarget("gw-dining-01", floor.gateways, [asset])
    ).toMatchObject({
      kind: "gateway",
      identifier: "GW-DINING-01",
      displayName: "Dining Gateway 01"
    });

    expect(
      resolveCommissioningTarget("tag-001", floor.gateways, [asset])
    ).toMatchObject({
      kind: "asset_tag",
      identifier: "TAG-001",
      displayName: "Tray Cart 01"
    });
  });

  it("returns an unknown target when the identifier is not in the registry", () => {
    const floor = createFloorDetail();

    expect(
      resolveCommissioningTarget("missing-01", floor.gateways, [createAsset()])
    ).toMatchObject({
      kind: "unknown",
      identifier: "MISSING-01"
    });
  });

  it("extracts identifiers from supported QR payload shapes", () => {
    expect(extractIdentifierFromQrPayload("gw-dining-01")).toBe("GW-DINING-01");
    expect(
      extractIdentifierFromQrPayload('{"gateway_id":"gw-kitchen-01"}')
    ).toBe("GW-KITCHEN-01");
    expect(
      extractIdentifierFromQrPayload("https://rtls.example/scan?tag_id=tag-002")
    ).toBe("TAG-002");
  });

  it("builds calibration waypoints from the selected zone and known floor context", () => {
    const floor = createFloorDetail();

    const waypoints = buildCalibrationWaypoints(floor, "area-1");

    expect(waypoints[0]).toMatchObject({
      id: "zone-area-1",
      label: "Dining South anchor",
      kind: "zone"
    });
    expect(waypoints.some((waypoint) => waypoint.label === "Dining Gateway 01")).toBe(true);
    expect(waypoints).toHaveLength(4);
  });

  it("tracks calibration progress when captures reach route checkpoints", () => {
    const floor = createFloorDetail();
    const waypoints = buildCalibrationWaypoints(floor, "area-1");

    const progress = buildCalibrationProgress(waypoints, [
      { x: 0.21, y: 0.21 },
      { x: 0.2, y: 0.31 }
    ]);

    expect(progress.completedCount).toBe(2);
    expect(progress.totalCount).toBe(4);
    expect(progress.nextWaypoint?.label).toBe("Kitchen Gateway 01");
  });

  it("summarizes and deduplicates commissioning sessions by target and floor", () => {
    const site = createSite();
    const floor = createFloorDetail();
    const target = resolveCommissioningTarget("GW-DINING-01", floor.gateways, [createAsset()]);

    expect(target).not.toBeNull();

    const summary = buildCommissioningSummary({
      target: target!,
      site,
      floor,
      zone: floor.areas[0] ?? null,
      startedAt: "2026-03-29T12:00:00Z",
      completedAt: "2026-03-29T12:04:30Z",
      captures: [
        { x: 0.2, y: 0.2 },
        { x: 0.22, y: 0.31 }
      ],
      progress: buildCalibrationProgress(buildCalibrationWaypoints(floor, "area-1"), [
        { x: 0.2, y: 0.2 },
        { x: 0.22, y: 0.31 }
      ])
    });

    expect(summary.elapsed_seconds).toBe(270);
    expect(summary.zone_name).toBe("Dining South");

    const refreshedSummary = {
      ...summary,
      completed_at: "2026-03-29T12:05:00Z",
      elapsed_seconds: 300
    };

    const entries = upsertCommissioningSummary([], summary);
    const dedupedEntries = upsertCommissioningSummary(entries, refreshedSummary);

    expect(dedupedEntries).toHaveLength(1);
    expect(dedupedEntries[0]?.elapsed_seconds).toBe(300);
  });
});
