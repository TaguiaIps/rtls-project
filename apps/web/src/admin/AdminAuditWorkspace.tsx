import type { AuditEventListRecord, AuditEventRecord } from "@rtls/contracts";
import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

import { useAuth } from "../auth";

type AuditFilters = {
  actorEmail: string;
  actionCategory: string;
  actionType: string;
  targetType: string;
};

const DEFAULT_FILTERS: AuditFilters = {
  actorEmail: "",
  actionCategory: "",
  actionType: "",
  targetType: ""
};

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

function renderDetails(event: AuditEventRecord) {
  if (!event.details) {
    return null;
  }

  return <pre className="audit-row__details">{JSON.stringify(event.details, null, 2)}</pre>;
}

export function AdminAuditWorkspace() {
  const { fetchWithAuth } = useAuth();
  const [filters, setFilters] = useState<AuditFilters>(DEFAULT_FILTERS);
  const [auditEvents, setAuditEvents] = useState<AuditEventListRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function updateFilter(event: ChangeEvent<HTMLInputElement>) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function loadAuditEvents(nextFilters: AuditFilters) {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "50");
      if (nextFilters.actorEmail) {
        params.set("actor_email", nextFilters.actorEmail);
      }
      if (nextFilters.actionCategory) {
        params.set("action_category", nextFilters.actionCategory);
      }
      if (nextFilters.actionType) {
        params.set("action_type", nextFilters.actionType);
      }
      if (nextFilters.targetType) {
        params.set("target_type", nextFilters.targetType);
      }

      const response = await fetchWithAuth(`/api/admin/audit-events?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Unable to load audit events.");
      }
      const payload = (await response.json()) as AuditEventListRecord;
      setAuditEvents(payload);
      setError(null);
    } catch {
      setError("Unable to load audit events.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAuditEvents(DEFAULT_FILTERS);
  }, [fetchWithAuth]);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadAuditEvents(filters);
  }

  function clearFilters() {
    setFilters(DEFAULT_FILTERS);
    void loadAuditEvents(DEFAULT_FILTERS);
  }

  return (
    <section className="shell-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Audit Log</p>
          <h2>Configuration history</h2>
          <p className="muted-text">
            Filter recent administrative changes by actor, category, action type, or target and
            inspect the persisted change payload for traceability.
          </p>
        </div>
        <div className="admin-inline-actions">
          <span className="status-badge status-badge--baseline">
            {auditEvents?.total_count ?? 0} matching events
          </span>
          <button className="secondary-button" onClick={() => void loadAuditEvents(filters)} type="button">
            Refresh
          </button>
        </div>
      </header>

      <form className="panel audit-filter-grid" onSubmit={onSubmit}>
        <label>
          <span>Actor Email</span>
          <input
            name="actorEmail"
            onChange={updateFilter}
            placeholder="admin@example.com"
            value={filters.actorEmail}
          />
        </label>
        <label>
          <span>Category</span>
          <input
            name="actionCategory"
            onChange={updateFilter}
            placeholder="configuration"
            value={filters.actionCategory}
          />
        </label>
        <label>
          <span>Action Type</span>
          <input
            name="actionType"
            onChange={updateFilter}
            placeholder="admin.gateway.updated"
            value={filters.actionType}
          />
        </label>
        <label>
          <span>Target Type</span>
          <input
            name="targetType"
            onChange={updateFilter}
            placeholder="gateway"
            value={filters.targetType}
          />
        </label>
        <div className="audit-filter-actions">
          <button className="primary-button" type="submit">
            Apply Filters
          </button>
          <button className="secondary-button" onClick={clearFilters} type="button">
            Clear
          </button>
        </div>
      </form>

      {error ? <div className="feedback-banner feedback-banner--error">{error}</div> : null}

      <section className="panel">
        {loading && !auditEvents ? (
          <p className="muted-text">Loading audit events...</p>
        ) : auditEvents?.items.length ? (
          <div className="audit-list">
            {auditEvents.items.map((event) => (
              <article key={event.id} className="audit-row">
                <div className="audit-row__meta">
                  <span className="status-badge status-badge--healthy">{event.action_category}</span>
                  <span>{formatTimestamp(event.created_at)}</span>
                </div>
                <div className="audit-row__meta">
                  <strong>{event.action_type}</strong>
                  <span>{event.actor_email ?? "System"}</span>
                </div>
                <span className="muted-text">
                  Target {event.target_type ?? "n/a"} · {event.target_id ?? "n/a"}
                </span>
                {renderDetails(event)}
              </article>
            ))}
          </div>
        ) : (
          <div className="admin-empty-state">
            <strong>No audit events match the current filters.</strong>
            <span className="muted-text">
              Widen the filters or refresh after more admin activity has been recorded.
            </span>
          </div>
        )}
      </section>
    </section>
  );
}
