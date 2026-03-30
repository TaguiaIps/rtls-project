import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const STORAGE_KEY = "rtls-auth-session";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

const currentUserResponse = {
  id: "user-1",
  email: "admin@example.com",
  display_name: "Alex",
  role: "Administrator",
  status: "active"
};

const observabilitySummaryResponse = {
  generated_at: "2026-03-29T15:00:00Z",
  gateway_totals: {
    total: 3,
    healthy: 1,
    stale: 2,
    low_battery: 1,
    without_heartbeat: 1
  },
  telemetry_totals: {
    raw_readings: 42,
    premium_measurements: 6,
    heartbeat_snapshots: 3
  },
  alert_totals: {
    active: 2,
    critical: 1,
    warning: 1
  },
  audit_totals: {
    total: 8,
    last_24h: 4,
    latest_at: "2026-03-29T14:50:00Z"
  },
  lifecycle: {
    policies: {
      raw_readings_days: 90,
      premium_measurements_days: 90,
      location_history_days: 30,
      exports_days: 7
    },
    latest_run: {
      id: "lifecycle-1",
      requested_by_user_id: "user-1",
      requested_by_email: "admin@example.com",
      status: "completed",
      retention_summary: {
        raw_readings_deleted: 0,
        premium_measurements_deleted: 0,
        location_history_deleted: 0,
        export_jobs_deleted: 0,
        export_files_deleted: 0
      },
      rollup_summary: {
        heatmap_rollups_refreshed: 1,
        sla_rollups_refreshed: 1
      },
      error_message: null,
      requested_at: "2026-03-29T14:55:00Z",
      started_at: "2026-03-29T14:55:02Z",
      completed_at: "2026-03-29T14:55:05Z"
    }
  },
  risk_items: [
    {
      id: "risk-1",
      kind: "stale_gateway",
      severity: "critical",
      gateway_id: "gateway-3",
      gateway_identifier: "gw-health-03",
      display_name: "Kitchen Gateway",
      floor_id: "floor-1",
      floor_name: "Dining Hall A",
      summary: "No heartbeat has been recorded for this gateway yet.",
      observed_at: null,
      battery_level_percent: null
    }
  ],
  services: [
    {
      name: "api",
      status: "healthy",
      detail: "Health summary, audit queries, and request identifiers are served by the API."
    }
  ],
  healthcheck_path: "/health",
  metrics_path: "/metrics",
  request_id_header: "X-Request-ID",
  tracing_status: "Request identifiers are attached to every API response for operational tracing."
};

const auditEventsResponse = {
  items: [
    {
      id: "audit-1",
      actor_user_id: "user-1",
      actor_email: "admin@example.com",
      actor_role: "Administrator",
      action_category: "configuration",
      action_type: "admin.gateway.updated",
      target_type: "gateway",
      target_id: "gateway-2",
      details: { changes: { display_name: "Dining Gateway 2" } },
      created_at: "2026-03-29T14:45:00Z"
    }
  ],
  total_count: 1
};

describe("Admin workspaces", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "token-123",
        refreshToken: "refresh-123"
      })
    );
    vi.restoreAllMocks();
  });

  it("renders the health workspace for administrators", async () => {
    window.history.pushState({}, "", "/admin/health");
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/me")) {
        return Promise.resolve(jsonResponse(currentUserResponse));
      }
      if (url.endsWith("/api/admin/observability/summary")) {
        return Promise.resolve(jsonResponse(observabilitySummaryResponse));
      }
      return Promise.resolve(new Response(null, { status: 404 }));
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/kitchen gateway/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("heading", { name: /operational readiness baseline/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /health/i })).toBeInTheDocument();
    expect(
      screen.getByText(/request identifiers are attached to every api response/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/90 days/i)).toBeInTheDocument();
  });

  it("renders the audit workspace and submits filters", async () => {
    window.history.pushState({}, "", "/admin/audit");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/api/me")) {
        return Promise.resolve(jsonResponse(currentUserResponse));
      }
      if (url.includes("/api/admin/audit-events")) {
        return Promise.resolve(jsonResponse(auditEventsResponse));
      }
      return Promise.resolve(new Response(null, { status: 404 }));
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /configuration history/i })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/actor email/i), {
      target: { value: "admin@example.com" }
    });
    fireEvent.click(screen.getByRole("button", { name: /apply filters/i }));

    await waitFor(() => {
      expect(screen.getByText(/admin.gateway.updated/i)).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/audit-events?limit=50&actor_email=admin%40example.com"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token-123"
        })
      })
    );
  });
});
