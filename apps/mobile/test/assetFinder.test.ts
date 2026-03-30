import { describe, expect, it } from "vitest";
import type { AssetLocationRecord } from "@rtls/contracts";

import {
  formatLastSeen,
  formatLocationContext,
  formatPrecisionContext,
  type RecentSearchEntry,
  upsertRecentSearch
} from "../src/assetFinder";
import { buildLiveMapHandoffUrl } from "../src/handoff";
import { buildSearchUrl, normalizeApiBaseUrl } from "../src/session";

function createAsset(overrides: Partial<AssetLocationRecord> = {}): AssetLocationRecord {
  return {
    asset_tag_id: "asset-1",
    tag_identifier: "POS-001",
    display_name: "POS Terminal 01",
    asset_category: "POS Terminal",
    floor_id: "floor-1",
    floor_name: "Dining",
    site_id: "site-1",
    site_name: "Flagship",
    observed_at: "2026-03-29T12:00:00Z",
    location_type: "point",
    point: { x: 12, y: 18 },
    zone_id: "zone-1",
    zone_name: "Dining South",
    confidence_level: "high",
    confidence_score: 0.91,
    source_tier: "Premium",
    source_modality: "UWB",
    precision_meters: 1.4,
    source_gateway_count: 3,
    source_reading_count: 8,
    ...overrides
  };
}

describe("asset finder helpers", () => {
  it("keeps recent searches ordered by latest access without duplicates", () => {
    const first = createAsset();
    const second = createAsset({ asset_tag_id: "asset-2", tag_identifier: "POS-002" });
    const third = createAsset({ asset_tag_id: "asset-3", tag_identifier: "POS-003" });

    const entries = upsertRecentSearch([], first, "2026-03-29T12:00:00Z");
    const withSecond = upsertRecentSearch(entries, second, "2026-03-29T12:01:00Z");
    const withThird = upsertRecentSearch(withSecond, third, "2026-03-29T12:02:00Z");
    const refreshedSecond = upsertRecentSearch(
      withThird,
      second,
      "2026-03-29T12:03:00Z"
    );

    expect(refreshedSecond.map((entry) => entry.asset.asset_tag_id)).toEqual([
      "asset-2",
      "asset-3",
      "asset-1"
    ]);
  });

  it("caps recent searches to five entries", () => {
    let entries: RecentSearchEntry[] = [];
    for (let index = 0; index < 6; index += 1) {
      entries = upsertRecentSearch(
        entries,
        createAsset({
          asset_tag_id: `asset-${index + 1}`,
          tag_identifier: `POS-00${index + 1}`
        }),
        `2026-03-29T12:0${index}:00Z`
      );
    }

    expect(entries).toHaveLength(5);
    expect(entries[0]?.asset.asset_tag_id).toBe("asset-6");
    expect(entries[4]?.asset.asset_tag_id).toBe("asset-2");
  });

  it("formats relative last-seen timestamps", () => {
    expect(
      formatLastSeen("2026-03-29T12:00:30Z", new Date("2026-03-29T12:01:00Z"))
    ).toBe("30s ago");
    expect(
      formatLastSeen("2026-03-29T11:58:00Z", new Date("2026-03-29T12:00:00Z"))
    ).toBe("2m ago");
    expect(
      formatLastSeen("2026-03-29T09:00:00Z", new Date("2026-03-29T12:00:00Z"))
    ).toBe("3h ago");
  });

  it("formats location and precision context from shared contracts", () => {
    const zoned = createAsset();
    const pointOnly = createAsset({
      zone_id: null,
      zone_name: null,
      source_modality: "BLE_RSSI",
      precision_meters: null,
      confidence_level: "medium"
    });

    expect(formatLocationContext(zoned)).toBe("Dining · Dining South");
    expect(formatLocationContext(pointOnly)).toBe("Dining · Flagship");
    expect(formatPrecisionContext(zoned)).toBe("UWB · ±1.4m");
    expect(formatPrecisionContext(pointOnly)).toBe("BLE_RSSI · medium confidence");
  });

  it("normalizes API bases and generates search URLs", () => {
    expect(normalizeApiBaseUrl("http://localhost:8000/")).toBe("http://localhost:8000");
    expect(buildSearchUrl("http://localhost:8000/", " tray cart ")).toBe(
      "http://localhost:8000/api/locations/search?query=tray+cart"
    );
  });

  it("generates a compatible Live Map handoff URL", () => {
    expect(
      buildLiveMapHandoffUrl("http://localhost:5173", createAsset())
    ).toBe(
      "http://localhost:5173/operations/live-map?site_id=site-1&floor_id=floor-1&asset_tag_id=asset-1"
    );
  });
});
