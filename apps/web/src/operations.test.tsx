import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const STORAGE_KEY = "rtls-auth-session";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onopen: (() => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    queueMicrotask(() => {
      this.onopen?.();
    });
  }

  close() {
    this.onclose?.();
  }

  emit(data: unknown) {
    this.onmessage?.(
      new MessageEvent("message", {
        data: JSON.stringify(data)
      })
    );
  }
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

const sitesResponse = [
  {
    id: "site-1",
    name: "Salvador Flagship",
    timezone_name: "America/Bahia",
    floors: [
      {
        id: "floor-1",
        site_id: "site-1",
        name: "Dining Hall A",
        level_label: "L1",
        has_floor_plan: true,
        scale_configured: true
      }
    ]
  }
];

const overviewResponse = {
  site_id: "site-1",
  site_name: "Salvador Flagship",
  floor_id: "floor-1",
  floor_name: "Dining Hall A",
  feed_status: "degraded",
  feed_updated_at: "2026-03-26T12:00:00Z",
  kpis: {
    active_assets: 4,
    low_confidence_assets: 1,
    restricted_zone_assets: 1,
    stale_gateways: 1
  },
  priority_items: [
    {
      id: "restricted-zone:asset-1",
      kind: "restricted_zone_asset",
      severity: "critical",
      title: "Waiter Tag 881 entered a restricted zone",
      summary: "Last known zone: Cold Storage.",
      observed_at: "2026-03-26T12:00:00Z",
      floor_id: "floor-1",
      asset_tag_id: "asset-1",
      gateway_id: null
    }
  ],
  gateway_snapshot: [
    {
      gateway_id: "gateway-1",
      floor_id: "floor-1",
      floor_name: "Dining Hall A",
      gateway_identifier: "gw-overview-02",
      display_name: "Dining Gateway 2",
      hardware_tier: "Economic",
      status: "stale",
      last_seen_at: "2026-03-26T11:50:00Z",
      gateway_timestamp: null,
      message_id: "hb-001",
      firmware_version: "1.2.3",
      battery_level_percent: 82
    }
  ],
  map_preview: {
    site_id: "site-1",
    site_name: "Salvador Flagship",
    floor_id: "floor-1",
    floor_name: "Dining Hall A",
    floor_plan: {
      id: "floor-plan-1",
      floor_id: "floor-1",
      original_filename: "overview.png",
      mime_type: "image/png",
      width_px: 1280,
      height_px: 720,
      file_download_path: "/api/admin/floors/floor-1/floor-plan/file"
    },
    areas: [
      {
        id: "zone-1",
        floor_id: "floor-1",
        name: "Cold Storage",
        area_type: "restricted_zone",
        points: [
          { x: 0.55, y: 0.1 },
          { x: 0.85, y: 0.1 },
          { x: 0.85, y: 0.4 }
        ],
        sla_eligible: false,
        alert_participation: true
      }
    ],
    gateways: [
      {
        id: "gateway-1",
        floor_id: "floor-1",
        gateway_identifier: "gw-overview-02",
        display_name: "Dining Gateway 2",
        hardware_tier: "Economic",
        placement: { x: 0.4, y: 0.2 },
        notes: null
      }
    ],
    locations: [
      {
        asset_tag_id: "asset-1",
        tag_identifier: "TAG-881",
        display_name: "Waiter Tag 881",
        asset_category: "staff",
        floor_id: "floor-1",
        floor_name: "Dining Hall A",
        site_id: "site-1",
        site_name: "Salvador Flagship",
        observed_at: "2026-03-26T12:00:00Z",
        location_type: "zone",
        point: null,
        zone_id: "zone-1",
        zone_name: "Cold Storage",
        confidence_level: "low",
        confidence_score: 0.41,
        source_gateway_count: 1,
        source_reading_count: 1
      }
    ]
  }
};

const floorDetailResponse = {
  id: "floor-1",
  site_id: "site-1",
  name: "Dining Hall A",
  level_label: "L1",
  scale_configured: true,
  floor_plan: overviewResponse.map_preview.floor_plan,
  scale: {
    point_a: { x: 0.1, y: 0.1 },
    point_b: { x: 0.7, y: 0.1 },
    real_world_distance_m: 12,
    pixels_per_meter: 80,
    configured_at: "2026-03-26T11:00:00Z"
  },
  areas: overviewResponse.map_preview.areas,
  gateways: overviewResponse.map_preview.gateways
};

const liveLocationsResponse = [
  {
    asset_tag_id: "asset-1",
    tag_identifier: "TAG-881",
    display_name: "Waiter Tag 881",
    asset_category: "staff",
    floor_id: "floor-1",
    floor_name: "Dining Hall A",
    site_id: "site-1",
    site_name: "Salvador Flagship",
    observed_at: "2026-03-26T12:00:00Z",
    location_type: "zone",
    point: null,
    zone_id: "zone-1",
    zone_name: "Cold Storage",
    confidence_level: "low",
    confidence_score: 0.41,
    source_gateway_count: 1,
    source_reading_count: 1
  }
];

describe("operations shell", () => {
  beforeEach(() => {
    cleanup();
    window.localStorage.clear();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-1",
        refreshToken: "refresh-1"
      })
    );
    vi.restoreAllMocks();
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
    Object.defineProperty(window.URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:floor-plan")
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn()
    });
  });

  it("renders the protected overview shell for a General User", async () => {
    window.history.pushState({}, "", "/operations?site_id=site-1&floor_id=floor-1");

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.endsWith("/api/me")) {
        return jsonResponse({
          id: "user-1",
          email: "ops@example.com",
          display_name: "Carlos",
          role: "General User",
          status: "active"
        });
      }
      if (url.endsWith("/api/admin/sites")) {
        return jsonResponse(sitesResponse);
      }
      if (url.includes("/api/operations/overview")) {
        return jsonResponse(overviewResponse);
      }
      if (url.endsWith("/api/admin/floors/floor-1/floor-plan/file")) {
        return new Response("png-data", {
          status: 200,
          headers: { "Content-Type": "image/png" }
        });
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Feed Degraded")).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Live Map" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument();
    expect(screen.getByText("Restricted Zone Hits")).toBeInTheDocument();
    expect(screen.getByText("Waiter Tag 881 entered a restricted zone")).toBeInTheDocument();
    expect(screen.getByText("Dining Gateway 2")).toBeInTheDocument();
  });

  it("updates the live map from WebSocket events and applies search filters", async () => {
    window.history.pushState({}, "", "/operations/live-map?site_id=site-1&floor_id=floor-1&confidence_level=low");

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.endsWith("/api/me")) {
        return jsonResponse({
          id: "user-1",
          email: "ops@example.com",
          display_name: "Carlos",
          role: "General User",
          status: "active"
        });
      }
      if (url.endsWith("/api/admin/sites")) {
        return jsonResponse(sitesResponse);
      }
      if (url.endsWith("/api/admin/floors/floor-1")) {
        return jsonResponse(floorDetailResponse);
      }
      if (url.endsWith("/api/admin/floors/floor-1/floor-plan/file")) {
        return new Response("png-data", {
          status: 200,
          headers: { "Content-Type": "image/png" }
        });
      }
      if (url.includes("/api/locations/live")) {
        return jsonResponse(liveLocationsResponse);
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Waiter Tag 881").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getAllByRole("button", { name: /Waiter Tag 881/i })[0]);
    expect(screen.getByText("Current Zone")).toBeInTheDocument();
    expect(screen.getAllByText("Cold Storage").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Search assets"), {
      target: { value: "Tray" }
    });

    await waitFor(() => {
      expect(
        fetchSpy.mock.calls.some(([input]) =>
          String(input).includes("/api/locations/live?floor_id=floor-1&search=Tray&confidence_level=low")
        )
      ).toBe(true);
    });

    const socket = MockWebSocket.instances[0];
    expect(socket).toBeDefined();
    socket.emit({
      event: "location.updated",
      location: {
        asset_tag_id: "asset-2",
        tag_identifier: "TAG-009",
        display_name: "Tray Cart 09",
        asset_category: "equipment",
        floor_id: "floor-1",
        floor_name: "Dining Hall A",
        site_id: "site-1",
        site_name: "Salvador Flagship",
        observed_at: "2026-03-26T12:01:00Z",
        location_type: "zone",
        point: null,
        zone_id: "zone-1",
        zone_name: "Cold Storage",
        confidence_level: "low",
        confidence_score: 0.38,
        source_gateway_count: 1,
        source_reading_count: 1
      }
    });

    await waitFor(() => {
      expect(screen.getAllByText("Tray Cart 09").length).toBeGreaterThan(0);
    });
  });
});
