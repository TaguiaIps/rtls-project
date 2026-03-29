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

const alertSummaryResponse = {
  unresolved_count: 2,
  unread_count: 2,
  active_critical_count: 1,
  active_warning_count: 1,
  latest_alert_at: "2026-03-26T12:00:00Z"
};

const alertRulesResponse = [
  {
    id: "rule-1",
    name: "Dining Table SLA",
    rule_type: "table_sla",
    severity: "warning",
    enabled: true,
    site_id: "site-1",
    site_name: "Salvador Flagship",
    floor_id: "floor-1",
    floor_name: "Dining Hall A",
    config: {
      threshold_seconds: 900,
      table_area_ids: ["table-zone-1"]
    },
    delivery: {
      in_app: true,
      email: false,
      email_recipients: []
    },
    created_at: "2026-03-26T11:30:00Z",
    updated_at: "2026-03-26T11:30:00Z"
  }
];

const alertsListResponse = [
  {
    id: "alert-1",
    rule_id: "rule-1",
    rule_name: "Dining Table SLA",
    rule_type: "table_sla",
    severity: "warning",
    status: "open",
    title: "Table SLA breach · Table 12",
    summary: "Table 12 has remained active for 950 seconds against a 900 second SLA.",
    scope_key: "table:table-zone-1",
    scope_label: "Table 12",
    site_id: "site-1",
    site_name: "Salvador Flagship",
    floor_id: "floor-1",
    floor_name: "Dining Hall A",
    area_id: "table-zone-1",
    area_name: "Table 12",
    asset_tag_id: null,
    asset_label: null,
    first_triggered_at: "2026-03-26T11:50:00Z",
    last_triggered_at: "2026-03-26T12:00:00Z",
    acknowledged_at: null,
    resolved_at: null,
    cleared_at: null
  }
];

const alertDetailResponse = {
  ...alertsListResponse[0],
  condition_key: "2026-03-26T11:44:10Z",
  context: {
    threshold_seconds: 900,
    elapsed_seconds: 950,
    table_name: "Table 12"
  },
  rule: alertRulesResponse[0],
  actions: [
    {
      id: "action-1",
      action_type: "triggered",
      actor_user_id: null,
      actor_email: null,
      actor_display_name: "System",
      notes: null,
      details: { condition_key: "2026-03-26T11:44:10Z" },
      created_at: "2026-03-26T11:50:00Z"
    }
  ],
  deliveries: [
    {
      id: "delivery-1",
      channel: "in_app",
      destination: "alerts-center",
      status: "delivered",
      error_message: null,
      read_at: null,
      created_at: "2026-03-26T11:50:00Z"
    }
  ]
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
      if (url.includes("/api/alerts/summary")) {
        return jsonResponse(alertSummaryResponse);
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
      if (url.includes("/api/alerts/summary")) {
        return jsonResponse(alertSummaryResponse);
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

  it("renders Alerts Center workflows and supports triage and rule editing", async () => {
    window.history.pushState({}, "", "/operations/alerts?site_id=site-1&floor_id=floor-1");

    let mutableSummary = { ...alertSummaryResponse };
    let mutableRules = [...alertRulesResponse];
    let mutableAlertDetail = { ...alertDetailResponse };
    let mutableAlertList = [...alertsListResponse];

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = init?.method ?? "GET";

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
        return jsonResponse({
          ...floorDetailResponse,
          areas: [
            ...floorDetailResponse.areas,
            {
              id: "table-zone-1",
              floor_id: "floor-1",
              name: "Table 12",
              area_type: "table",
              points: [
                { x: 0.25, y: 0.25 },
                { x: 0.3, y: 0.25 },
                { x: 0.3, y: 0.3 }
              ],
              sla_eligible: true,
              alert_participation: true
            }
          ]
        });
      }
      if (url.includes("/api/alerts/summary")) {
        return jsonResponse(mutableSummary);
      }
      if (url.includes("/api/alerts/rules") && method === "GET") {
        return jsonResponse(mutableRules);
      }
      if (url.includes("/api/alerts/rules/rule-1") && method === "PATCH") {
        const payload = JSON.parse(String(init?.body)) as { name: string };
        mutableRules = mutableRules.map((rule) =>
          rule.id === "rule-1" ? { ...rule, name: payload.name } : rule
        );
        mutableAlertDetail = {
          ...mutableAlertDetail,
          rule: { ...mutableAlertDetail.rule, name: payload.name },
          rule_name: payload.name
        };
        return jsonResponse(mutableRules[0]);
      }
      if (url.includes("/api/alerts/alert-1/resolve") && method === "POST") {
        mutableSummary = {
          ...mutableSummary,
          unresolved_count: 0,
          unread_count: 0,
          active_warning_count: 0
        };
        mutableAlertList = mutableAlertList.map((alert) => ({
          ...alert,
          status: "resolved",
          resolved_at: "2026-03-26T12:05:00Z"
        }));
        mutableAlertDetail = {
          ...mutableAlertDetail,
          status: "resolved",
          resolved_at: "2026-03-26T12:05:00Z",
          actions: [
            ...mutableAlertDetail.actions,
            {
              id: "action-2",
              action_type: "resolved",
              actor_user_id: "user-1",
              actor_email: "ops@example.com",
              actor_display_name: "Carlos",
              notes: "Handled by floor lead",
              details: null,
              created_at: "2026-03-26T12:05:00Z"
            }
          ]
        };
        return jsonResponse(mutableAlertDetail);
      }
      if (url.includes("/api/alerts/alert-1") && method === "GET") {
        return jsonResponse(mutableAlertDetail);
      }
      if (url.includes("/api/alerts?")) {
        return jsonResponse(mutableAlertList);
      }

      throw new Error(`Unexpected fetch: ${method} ${url}`);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /Alerts/i })).toBeInTheDocument();
      expect(screen.getByText("Table SLA breach · Table 12")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Delivery")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Alert notes"), {
      target: { value: "Handled by floor lead" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Resolve" }));

    await waitFor(() => {
      expect(screen.getAllByText("resolved").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByRole("button", { name: /Dining Table SLA/i }));
    await waitFor(() => {
      expect(screen.getByLabelText("Rule name")).toHaveValue("Dining Table SLA");
    });
    fireEvent.change(screen.getByLabelText("Rule name"), {
      target: { value: "Dining Hall SLA" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Rule" }));

    await waitFor(() => {
      expect(
        fetchSpy.mock.calls.some(
          ([input, init]) =>
            String(input).includes("/api/alerts/rules/rule-1") && init?.method === "PATCH"
        )
      ).toBe(true);
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Dining Hall SLA/i })).toBeInTheDocument();
    });
  });
});
