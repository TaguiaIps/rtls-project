import { LOCAL_STACK_SERVICES } from "@rtls/config";
import type {
  HealthRiskRecord,
  ObservabilityServiceRecord,
  ObservabilitySummaryRecord
} from "@rtls/contracts";
import { useEffect, useState } from "react";

import { useAuth } from "../auth";

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

function statusBadgeClass(value: string) {
  if (value === "critical") {
    return "status-badge status-badge--critical";
  }
  if (value === "warning") {
    return "status-badge status-badge--warning";
  }
  if (value === "healthy") {
    return "status-badge status-badge--healthy";
  }
  return "status-badge status-badge--baseline";
}

function mergeServices(
  services: ObservabilityServiceRecord[]
): Array<ObservabilityServiceRecord & { label: string; purpose: string }> {
  return LOCAL_STACK_SERVICES.map((serviceDefinition) => {
    const runtimeService = services.find((service) => service.name === serviceDefinition.name);
    return {
      name: serviceDefinition.name,
      label: serviceDefinition.label,
      purpose: serviceDefinition.purpose,
      status: runtimeService?.status ?? "baseline",
      detail: runtimeService?.detail ?? "No additional runtime detail has been published yet."
    };
  });
}

function renderRiskState(riskItems: HealthRiskRecord[]) {
  if (riskItems.length === 0) {
    return <p className="muted-text">No stale gateways or battery risks are currently surfaced.</p>;
  }

  return (
    <div className="priority-list">
      {riskItems.map((risk) => (
        <article
          key={risk.id}
          className={`priority-card priority-card--${risk.severity}`}
        >
          <div className="priority-card__meta">
            <span className={statusBadgeClass(risk.severity)}>{risk.severity}</span>
            <span>{risk.floor_name}</span>
          </div>
          <strong>{risk.display_name}</strong>
          <span className="muted-text">{risk.summary}</span>
          <div className="priority-card__meta">
            <span>{risk.gateway_identifier}</span>
            <span>
              {risk.battery_level_percent !== null
                ? `${Math.round(risk.battery_level_percent)}% battery`
                : "Battery unknown"}
            </span>
          </div>
          <span className="muted-text">Observed {formatTimestamp(risk.observed_at)}</span>
        </article>
      ))}
    </div>
  );
}

export function AdminHealthWorkspace() {
  const { fetchWithAuth } = useAuth();
  const [summary, setSummary] = useState<ObservabilitySummaryRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadSummary() {
    setLoading(true);
    try {
      const response = await fetchWithAuth("/api/admin/observability/summary");
      if (!response.ok) {
        throw new Error("Unable to load the health workspace.");
      }
      const payload = (await response.json()) as ObservabilitySummaryRecord;
      setSummary(payload);
      setError(null);
    } catch {
      setError("Unable to load the health workspace.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSummary();
  }, [fetchWithAuth]);

  const services = mergeServices(summary?.services ?? []);

  return (
    <section className="shell-page health-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Infrastructure Health</p>
          <h2>Operational readiness baseline</h2>
          <p className="muted-text">
            Review gateway liveness, telemetry flow, alert pressure, and the current observability
            contract without leaving the admin workspace.
          </p>
        </div>
        <div className="admin-inline-actions">
          <span className={statusBadgeClass(error ? "critical" : "healthy")}>
            {error ? "degraded" : "baseline ready"}
          </span>
          <button className="secondary-button" onClick={() => void loadSummary()} type="button">
            Refresh
          </button>
        </div>
      </header>

      {error ? <div className="feedback-banner feedback-banner--error">{error}</div> : null}

      <section className="overview-kpis">
        <article className="panel kpi-card kpi-card--live">
          <span className="summary-label">Gateways</span>
          <strong>{summary?.gateway_totals.total ?? 0}</strong>
          <span className="muted-text">
            {summary?.gateway_totals.healthy ?? 0} healthy, {summary?.gateway_totals.stale ?? 0} stale
          </span>
        </article>
        <article className="panel kpi-card kpi-card--warning">
          <span className="summary-label">Gateway Risks</span>
          <strong>{summary?.gateway_totals.low_battery ?? 0}</strong>
          <span className="muted-text">
            {summary?.gateway_totals.without_heartbeat ?? 0} without heartbeat
          </span>
        </article>
        <article className="panel kpi-card kpi-card--live">
          <span className="summary-label">Telemetry</span>
          <strong>{summary?.telemetry_totals.raw_readings ?? 0}</strong>
          <span className="muted-text">
            {summary?.telemetry_totals.premium_measurements ?? 0} premium measurements
          </span>
        </article>
        <article className="panel kpi-card kpi-card--critical">
          <span className="summary-label">Audit + Alerts</span>
          <strong>{summary?.alert_totals.active ?? 0}</strong>
          <span className="muted-text">
            {summary?.audit_totals.last_24h ?? 0} audit events in the last 24 hours
          </span>
        </article>
      </section>

      <div className="overview-grid">
        <section className="panel overview-map-panel">
          <div className="stack-card__header">
            <div>
              <p className="eyebrow">Gateway Risks</p>
              <h2>Needs attention</h2>
            </div>
            <span className="muted-text">
              Updated {formatTimestamp(summary?.generated_at ?? null)}
            </span>
          </div>
          {loading && !summary ? (
            <p className="muted-text">Loading health summary...</p>
          ) : (
            renderRiskState(summary?.risk_items ?? [])
          )}
        </section>

        <div className="overview-side-column">
          <section className="panel">
            <p className="eyebrow">Observability Baseline</p>
            <h2>Delivered endpoints</h2>
            <dl className="definition-list">
              <div>
                <dt>Health check</dt>
                <dd>{summary?.healthcheck_path ?? "/health"}</dd>
              </div>
              <div>
                <dt>Metrics</dt>
                <dd>{summary?.metrics_path ?? "/metrics"}</dd>
              </div>
              <div>
                <dt>Request header</dt>
                <dd>{summary?.request_id_header ?? "X-Request-ID"}</dd>
              </div>
              <div>
                <dt>Tracing status</dt>
                <dd>{summary?.tracing_status ?? "Request identifiers attach tracing context."}</dd>
              </div>
              <div>
                <dt>Latest audit event</dt>
                <dd>{formatTimestamp(summary?.audit_totals.latest_at ?? null)}</dd>
              </div>
            </dl>
          </section>

          <section className="panel">
            <p className="eyebrow">Service Coverage</p>
            <h2>Local stack baseline</h2>
            <div className="admin-service-grid">
              {services.map((service) => (
                <article key={service.name} className="priority-card">
                  <div className="priority-card__meta">
                    <strong>{service.label}</strong>
                    <span className={statusBadgeClass(service.status)}>{service.status}</span>
                  </div>
                  <span className="muted-text">{service.purpose}</span>
                  <span className="muted-text">{service.detail}</span>
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
