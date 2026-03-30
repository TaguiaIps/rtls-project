import type {
  AlertDetailRecord,
  AlertListItemRecord,
  AlertNotificationSummaryRecord,
  AlertRuleRecord,
  AlertRuleType,
  AlertRuleUpsertPayload,
  FloorDetail,
  SpatialAreaRecord,
  UnauthorizedGeofenceTrigger
} from "@rtls/contracts";
import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import { useOperationsShell } from "./OperationsShell";

type RuleDraft = {
  name: string;
  ruleType: AlertRuleType;
  enabled: boolean;
  thresholdSeconds: string;
  tableAreaIds: string[];
  areaIds: string[];
  triggerOn: UnauthorizedGeofenceTrigger;
  assetCategory: string;
  notifyEmail: boolean;
  emailRecipients: string;
};

const DEFAULT_RULE_DRAFT: RuleDraft = {
  name: "",
  ruleType: "table_sla",
  enabled: true,
  thresholdSeconds: "900",
  tableAreaIds: [],
  areaIds: [],
  triggerOn: "entry",
  assetCategory: "",
  notifyEmail: false,
  emailRecipients: ""
};

export function AlertsCenterPage() {
  const {
    fetchWithAuth,
    refreshAlertSummary,
    selectedFloor,
    selectedSite,
    setSearchParam,
    setShellFeed,
    shellSearchParams
  } = useOperationsShell();
  const [summary, setSummary] = useState<AlertNotificationSummaryRecord | null>(null);
  const [alerts, setAlerts] = useState<AlertListItemRecord[]>([]);
  const [rules, setRules] = useState<AlertRuleRecord[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AlertDetailRecord | null>(null);
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionSubmitting, setActionSubmitting] = useState<"acknowledge" | "resolve" | null>(null);
  const [actionNotes, setActionNotes] = useState("");
  const [ruleSaveError, setRuleSaveError] = useState<string | null>(null);
  const [ruleSaving, setRuleSaving] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string>("new");
  const [ruleDraft, setRuleDraft] = useState<RuleDraft>(DEFAULT_RULE_DRAFT);
  const [searchInput, setSearchInput] = useState(shellSearchParams.get("alert_query") ?? "");
  const deferredSearch = useDeferredValue(searchInput);
  const selectedAlertId = shellSearchParams.get("alert_id");
  const statusFilter = shellSearchParams.get("alert_status") ?? "";
  const typeFilter = shellSearchParams.get("alert_type") ?? "";
  const severityFilter = shellSearchParams.get("alert_severity") ?? "";
  const rangeFilter = shellSearchParams.get("alert_range") ?? "24h";

  const selectedRule = useMemo(
    () => rules.find((rule) => rule.id === editingRuleId) ?? null,
    [editingRuleId, rules]
  );
  const tableAreas = useMemo(
    () =>
      (floorDetail?.areas ?? []).filter(
        (area) => area.area_type === "table" && area.sla_eligible
      ),
    [floorDetail?.areas]
  );
  const restrictedAreas = useMemo(
    () =>
      (floorDetail?.areas ?? []).filter(
        (area) => area.area_type === "restricted_zone" && area.alert_participation
      ),
    [floorDetail?.areas]
  );

  useEffect(() => {
    setSearchInput(shellSearchParams.get("alert_query") ?? "");
  }, [shellSearchParams]);

  useEffect(() => {
    if ((shellSearchParams.get("alert_query") ?? "") === deferredSearch) {
      return;
    }
    setSearchParam("alert_query", deferredSearch || null);
  }, [deferredSearch, setSearchParam, shellSearchParams]);

  useEffect(() => {
    if (!selectedFloor?.id) {
      setFloorDetail(null);
      return;
    }

    let cancelled = false;
    async function loadFloor() {
      try {
        const response = await fetchWithAuth(`/api/admin/floors/${selectedFloor.id}`);
        if (!response.ok) {
          throw new Error("Unable to load floor detail");
        }
        const payload = (await response.json()) as FloorDetail;
        if (!cancelled) {
          setFloorDetail(payload);
        }
      } catch {
        if (!cancelled) {
          setFloorDetail(null);
        }
      }
    }

    void loadFloor();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth, selectedFloor?.id]);

  useEffect(() => {
    let cancelled = false;

    async function loadAlertsPage() {
      setLoading(true);
      try {
        const summaryPath = buildSummaryPath({
          floorId: selectedFloor?.id ?? null,
          siteId: selectedSite?.id ?? null
        });
        const alertsPath = buildAlertsPath({
          floorId: selectedFloor?.id ?? null,
          siteId: selectedSite?.id ?? null,
          search: deferredSearch,
          severity: severityFilter || null,
          statusValue: statusFilter || null,
          ruleType: typeFilter || null,
          range: rangeFilter
        });
        const rulesPath = buildRulesPath({
          floorId: selectedFloor?.id ?? null,
          siteId: selectedSite?.id ?? null
        });

        const [summaryResponse, alertsResponse, rulesResponse] = await Promise.all([
          fetchWithAuth(summaryPath),
          fetchWithAuth(alertsPath),
          fetchWithAuth(rulesPath)
        ]);
        if (!summaryResponse.ok || !alertsResponse.ok || !rulesResponse.ok) {
          throw new Error("Unable to load alerts");
        }

        const [summaryPayload, alertsPayload, rulesPayload] = (await Promise.all([
          summaryResponse.json(),
          alertsResponse.json(),
          rulesResponse.json()
        ])) as [AlertNotificationSummaryRecord, AlertListItemRecord[], AlertRuleRecord[]];

        if (!cancelled) {
          setSummary(summaryPayload);
          setAlerts(alertsPayload);
          setRules(rulesPayload);
          setError(null);
          setShellFeed(summaryPayload.latest_alert_at ? "live" : "empty", summaryPayload.latest_alert_at);
          if (!selectedAlertId && alertsPayload[0]) {
            startTransition(() => {
              setSearchParam("alert_id", alertsPayload[0].id);
            });
          }
        }
      } catch {
        if (!cancelled) {
          setSummary(null);
          setAlerts([]);
          setRules([]);
          setError("Unable to load Alerts Center.");
          setShellFeed("degraded", null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadAlertsPage();
    return () => {
      cancelled = true;
    };
  }, [
    deferredSearch,
    fetchWithAuth,
    rangeFilter,
    selectedAlertId,
    selectedFloor?.id,
    selectedSite?.id,
    setSearchParam,
    setShellFeed,
    severityFilter,
    statusFilter,
    typeFilter
  ]);

  useEffect(() => {
    if (!selectedAlertId) {
      setSelectedAlert(null);
      return;
    }

    let cancelled = false;
    async function loadAlertDetail() {
      setDetailLoading(true);
      try {
        const response = await fetchWithAuth(`/api/alerts/${selectedAlertId}`);
        if (!response.ok) {
          throw new Error("Unable to load alert detail");
        }
        const payload = (await response.json()) as AlertDetailRecord;
        if (!cancelled) {
          setSelectedAlert(payload);
          setActionNotes("");
        }
      } catch {
        if (!cancelled) {
          setSelectedAlert(null);
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    void loadAlertDetail();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth, selectedAlertId]);

  useEffect(() => {
    if (!selectedRule) {
      setRuleDraft(DEFAULT_RULE_DRAFT);
      return;
    }

    if (selectedRule.rule_type === "table_sla") {
      setRuleDraft({
        name: selectedRule.name,
        ruleType: selectedRule.rule_type,
        enabled: selectedRule.enabled,
        thresholdSeconds: String((selectedRule.config as { threshold_seconds: number }).threshold_seconds),
        tableAreaIds: [...(selectedRule.config as { table_area_ids: string[] }).table_area_ids],
        areaIds: [],
        triggerOn: "entry",
        assetCategory: "",
        notifyEmail: selectedRule.delivery.email,
        emailRecipients: selectedRule.delivery.email_recipients.join(", ")
      });
      return;
    }

    const geofenceConfig = selectedRule.config as {
      area_ids: string[];
      trigger_on: UnauthorizedGeofenceTrigger;
      asset_category: string | null;
    };
    setRuleDraft({
      name: selectedRule.name,
      ruleType: selectedRule.rule_type,
      enabled: selectedRule.enabled,
      thresholdSeconds: DEFAULT_RULE_DRAFT.thresholdSeconds,
      tableAreaIds: [],
      areaIds: [...geofenceConfig.area_ids],
      triggerOn: geofenceConfig.trigger_on,
      assetCategory: geofenceConfig.asset_category ?? "",
      notifyEmail: selectedRule.delivery.email,
      emailRecipients: selectedRule.delivery.email_recipients.join(", ")
    });
  }, [selectedRule]);

  const unresolvedCount = summary?.unresolved_count ?? 0;

  async function refreshAlertsData() {
    await Promise.all([
      refreshAlertSummary(),
      (async () => {
        const summaryResponse = await fetchWithAuth(
          buildSummaryPath({
            floorId: selectedFloor?.id ?? null,
            siteId: selectedSite?.id ?? null
          })
        );
        const alertsResponse = await fetchWithAuth(
          buildAlertsPath({
            floorId: selectedFloor?.id ?? null,
            siteId: selectedSite?.id ?? null,
            search: deferredSearch,
            severity: severityFilter || null,
            statusValue: statusFilter || null,
            ruleType: typeFilter || null,
            range: rangeFilter
          })
        );
        const rulesResponse = await fetchWithAuth(
          buildRulesPath({
            floorId: selectedFloor?.id ?? null,
            siteId: selectedSite?.id ?? null
          })
        );
        if (!summaryResponse.ok || !alertsResponse.ok || !rulesResponse.ok) {
          return;
        }
        setSummary((await summaryResponse.json()) as AlertNotificationSummaryRecord);
        setAlerts((await alertsResponse.json()) as AlertListItemRecord[]);
        setRules((await rulesResponse.json()) as AlertRuleRecord[]);
      })()
    ]);
  }

  async function submitAlertAction(action: "acknowledge" | "resolve") {
    if (!selectedAlert) {
      return;
    }
    setActionSubmitting(action);
    try {
      const response = await fetchWithAuth(`/api/alerts/${selectedAlert.id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: actionNotes || null })
      });
      if (!response.ok) {
        throw new Error("Unable to update alert");
      }
      const payload = (await response.json()) as AlertDetailRecord;
      setSelectedAlert(payload);
      setActionNotes("");
      await refreshAlertsData();
    } finally {
      setActionSubmitting(null);
    }
  }

  async function saveRule() {
    setRuleSaving(true);
    setRuleSaveError(null);
    try {
      const payload = buildRulePayload(ruleDraft);
      const path = editingRuleId === "new" ? "/api/alerts/rules" : `/api/alerts/rules/${editingRuleId}`;
      const method = editingRuleId === "new" ? "POST" : "PATCH";
      const response = await fetchWithAuth(path, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const errorBody = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(errorBody?.detail ?? "Unable to save alert rule");
      }
      const savedRule = (await response.json()) as AlertRuleRecord;
      setEditingRuleId(savedRule.id);
      await refreshAlertsData();
    } catch (saveError) {
      setRuleSaveError((saveError as Error).message);
    } finally {
      setRuleSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Alerts Center</p>
        <h2>Loading alerts</h2>
        <p className="muted-text">Pulling current alerts, rule definitions, and notification state.</p>
      </section>
    );
  }

  return (
    <div className="alerts-layout">
      <header className="panel alerts-header">
        <div>
          <p className="eyebrow">Alerts Center</p>
          <h2>{selectedFloor?.name ?? selectedSite?.name ?? "Operational alerts"}</h2>
          <p className="muted-text">
            Triage SLA, geofence, and maintenance alerts without leaving the delivered operations shell.
          </p>
        </div>
        <div className="alerts-header__meta">
          <div className="shell-status-card">
            <p className="shell-status-card__label">Active queue</p>
            <strong>{unresolvedCount}</strong>
            <span>Unresolved or acknowledged alerts</span>
          </div>
        </div>
      </header>

      {error ? <p className="feedback-banner feedback-banner--error">{error}</p> : null}

      <section className="alert-summary-grid">
        <article className="panel kpi-card kpi-card--critical">
          <p className="eyebrow">Critical</p>
          <strong>{summary?.active_critical_count ?? 0}</strong>
        </article>
        <article className="panel kpi-card kpi-card--warning">
          <p className="eyebrow">Warning</p>
          <strong>{summary?.active_warning_count ?? 0}</strong>
        </article>
        <article className="panel kpi-card kpi-card--live">
          <p className="eyebrow">Unread Signals</p>
          <strong>{summary?.unread_count ?? 0}</strong>
        </article>
        <article className="panel kpi-card">
          <p className="eyebrow">Rules</p>
          <strong>{rules.length}</strong>
        </article>
      </section>

      <section className="panel alerts-filters">
        <input
          aria-label="Search alerts"
          placeholder="Search alert title or scope"
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
        />
        <select
          aria-label="Alert status"
          value={statusFilter}
          onChange={(event) => setSearchParam("alert_status", event.target.value || null)}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
          <option value="cleared">Cleared</option>
        </select>
        <select
          aria-label="Alert type"
          value={typeFilter}
          onChange={(event) => setSearchParam("alert_type", event.target.value || null)}
        >
          <option value="">All alert types</option>
          <option value="table_sla">Table SLA</option>
          <option value="unauthorized_geofence">Unauthorized geofence</option>
          <option value="gateway_stale">Gateway offline</option>
          <option value="gateway_low_battery">Gateway low battery</option>
        </select>
        <select
          aria-label="Alert severity"
          value={severityFilter}
          onChange={(event) => setSearchParam("alert_severity", event.target.value || null)}
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
        </select>
        <select
          aria-label="Alert timeframe"
          value={rangeFilter}
          onChange={(event) => setSearchParam("alert_range", event.target.value || null)}
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </section>

      <div className="alerts-grid">
        <section className="panel alert-queue-panel">
          <div className="stack-card__header">
            <div>
              <p className="eyebrow">Queue</p>
              <h2>Current and recent alerts</h2>
            </div>
          </div>
          {alerts.length === 0 ? (
            <p className="empty-copy">No alerts match the current filters.</p>
          ) : (
            <div className="alert-list">
              {alerts.map((alert) => (
                <button
                  key={alert.id}
                  className={
                    alert.id === selectedAlertId
                      ? "alert-row alert-row--selected"
                      : "alert-row"
                  }
                  onClick={() => setSearchParam("alert_id", alert.id)}
                  type="button"
                >
                  <div className="alert-row__content">
                    <div>
                      <strong>{alert.title}</strong>
                      <p className="muted-text">{alert.summary}</p>
                    </div>
                    <span className={`status-badge status-badge--${alert.severity}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <div className="alert-row__meta">
                    <span>{alert.scope_label}</span>
                    <span>{relativeTime(alert.last_triggered_at)}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <div className="alerts-side-column">
          <section className="panel alert-detail-panel">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Detail</p>
                <h2>{selectedAlert?.title ?? "Select an alert"}</h2>
              </div>
            </div>
            {detailLoading ? (
              <p className="muted-text">Loading alert detail...</p>
            ) : selectedAlert ? (
              <>
                <dl className="definition-list">
                  <div>
                    <dt>Status</dt>
                    <dd>{selectedAlert.status}</dd>
                  </div>
                  <div>
                    <dt>Scope</dt>
                    <dd>{selectedAlert.scope_label}</dd>
                  </div>
                  <div>
                    <dt>Rule</dt>
                    <dd>{selectedAlert.rule.name}</dd>
                  </div>
                  <div>
                    <dt>Triggered</dt>
                    <dd>{relativeTime(selectedAlert.first_triggered_at)}</dd>
                  </div>
                </dl>

                <textarea
                  aria-label="Alert notes"
                  className="alert-notes"
                  placeholder="Add triage context before acknowledging or resolving"
                  value={actionNotes}
                  onChange={(event) => setActionNotes(event.target.value)}
                />

                <div className="alert-detail-actions">
                  <button
                    className="secondary-button"
                    disabled={
                      selectedAlert.status === "resolved" ||
                      selectedAlert.status === "cleared" ||
                      actionSubmitting !== null
                    }
                    onClick={() => void submitAlertAction("acknowledge")}
                    type="button"
                  >
                    {actionSubmitting === "acknowledge" ? "Saving..." : "Acknowledge"}
                  </button>
                  <button
                    className="primary-button"
                    disabled={selectedAlert.status === "cleared" || actionSubmitting !== null}
                    onClick={() => void submitAlertAction("resolve")}
                    type="button"
                  >
                    {actionSubmitting === "resolve" ? "Saving..." : "Resolve"}
                  </button>
                </div>

                <div className="alert-detail-section">
                  <p className="eyebrow">Delivery</p>
                  <div className="activity-list">
                    {selectedAlert.deliveries.map((delivery) => (
                      <div key={delivery.id} className="activity-row activity-row--static">
                        <div>
                          <strong>{delivery.channel}</strong>
                          <span>{delivery.destination}</span>
                        </div>
                        <span className={`status-badge status-badge--${delivery.status}`}>
                          {delivery.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="alert-detail-section">
                  <p className="eyebrow">Timeline</p>
                  <div className="activity-list">
                    {selectedAlert.actions.map((action) => (
                      <div key={action.id} className="activity-row activity-row--static">
                        <div>
                          <strong>{action.action_type}</strong>
                          <span>{action.actor_display_name ?? action.actor_email ?? "System"}</span>
                        </div>
                        <span>{relativeTime(action.created_at)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="empty-copy">Choose an alert from the queue to inspect detail and triage actions.</p>
            )}
          </section>

          <section className="panel alert-rule-panel">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Rules</p>
                <h2>Delivered rule management</h2>
              </div>
              <button
                className="secondary-button"
                onClick={() => {
                  setEditingRuleId("new");
                  setRuleDraft(DEFAULT_RULE_DRAFT);
                }}
                type="button"
              >
                New Rule
              </button>
            </div>

            <div className="alert-rule-list">
              {rules.map((rule) => (
                <button
                  key={rule.id}
                  className={
                    rule.id === editingRuleId
                      ? "activity-row activity-row--active"
                      : "activity-row activity-row--static"
                  }
                  onClick={() => setEditingRuleId(rule.id)}
                  type="button"
                >
                  <div>
                    <strong>{rule.name}</strong>
                    <span>{rule.rule_type}</span>
                  </div>
                  <span className={`status-badge status-badge--${rule.enabled ? "high" : "warning"}`}>
                    {rule.enabled ? "enabled" : "disabled"}
                  </span>
                </button>
              ))}
            </div>

            <div className="alert-rule-form">
              <label>
                <span>Rule name</span>
                <input
                  aria-label="Rule name"
                  type="text"
                  value={ruleDraft.name}
                  onChange={(event) =>
                    setRuleDraft((current) => ({ ...current, name: event.target.value }))
                  }
                />
              </label>

              <label>
                <span>Rule type</span>
                <select
                  aria-label="Rule type editor"
                  value={ruleDraft.ruleType}
                  onChange={(event) =>
                    setRuleDraft((current) => ({
                      ...current,
                      ruleType: event.target.value as AlertRuleType,
                      tableAreaIds: [],
                      areaIds: []
                    }))
                  }
                >
                  <option value="table_sla">Table SLA</option>
                  <option value="unauthorized_geofence">Unauthorized geofence</option>
                </select>
              </label>

              <label className="alert-rule-toggle">
                <input
                  checked={ruleDraft.enabled}
                  type="checkbox"
                  onChange={(event) =>
                    setRuleDraft((current) => ({ ...current, enabled: event.target.checked }))
                  }
                />
                <span>Rule enabled</span>
              </label>

              {ruleDraft.ruleType === "table_sla" ? (
                <>
                  <label>
                    <span>Threshold seconds</span>
                    <input
                      aria-label="Threshold seconds"
                      type="number"
                      value={ruleDraft.thresholdSeconds}
                      onChange={(event) =>
                        setRuleDraft((current) => ({
                          ...current,
                          thresholdSeconds: event.target.value
                        }))
                      }
                    />
                  </label>
                  <AreaSelector
                    areas={tableAreas}
                    label="SLA tables"
                    selectedIds={ruleDraft.tableAreaIds}
                    onToggle={(areaId) =>
                      setRuleDraft((current) => ({
                        ...current,
                        tableAreaIds: toggleSelection(current.tableAreaIds, areaId)
                      }))
                    }
                  />
                </>
              ) : (
                <>
                  <label>
                    <span>Trigger on</span>
                    <select
                      aria-label="Trigger on"
                      value={ruleDraft.triggerOn}
                      onChange={(event) =>
                        setRuleDraft((current) => ({
                          ...current,
                          triggerOn: event.target.value as UnauthorizedGeofenceTrigger
                        }))
                      }
                    >
                      <option value="entry">Entry</option>
                      <option value="exit">Exit</option>
                    </select>
                  </label>
                  <label>
                    <span>Asset category filter</span>
                    <input
                      aria-label="Asset category filter"
                      placeholder="Optional"
                      type="text"
                      value={ruleDraft.assetCategory}
                      onChange={(event) =>
                        setRuleDraft((current) => ({
                          ...current,
                          assetCategory: event.target.value
                        }))
                      }
                    />
                  </label>
                  <AreaSelector
                    areas={restrictedAreas}
                    label="Restricted zones"
                    selectedIds={ruleDraft.areaIds}
                    onToggle={(areaId) =>
                      setRuleDraft((current) => ({
                        ...current,
                        areaIds: toggleSelection(current.areaIds, areaId)
                      }))
                    }
                  />
                </>
              )}

              <label className="alert-rule-toggle">
                <input
                  checked={ruleDraft.notifyEmail}
                  type="checkbox"
                  onChange={(event) =>
                    setRuleDraft((current) => ({
                      ...current,
                      notifyEmail: event.target.checked
                    }))
                  }
                />
                <span>Attempt email delivery</span>
              </label>

              <label>
                <span>Email recipients</span>
                <input
                  aria-label="Email recipients"
                  placeholder="ops@example.com, lead@example.com"
                  type="text"
                  value={ruleDraft.emailRecipients}
                  onChange={(event) =>
                    setRuleDraft((current) => ({
                      ...current,
                      emailRecipients: event.target.value
                    }))
                  }
                />
              </label>

              {ruleSaveError ? <p className="form-error">{ruleSaveError}</p> : null}

              <button
                className="primary-button"
                disabled={ruleSaving}
                onClick={() => void saveRule()}
                type="button"
              >
                {ruleSaving ? "Saving..." : editingRuleId === "new" ? "Create Rule" : "Save Rule"}
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function AreaSelector({
  areas,
  label,
  selectedIds,
  onToggle
}: {
  areas: SpatialAreaRecord[];
  label: string;
  selectedIds: string[];
  onToggle: (areaId: string) => void;
}) {
  return (
    <fieldset className="alert-area-selector">
      <legend>{label}</legend>
      {areas.length === 0 ? <p className="empty-copy">No eligible areas on the selected floor.</p> : null}
      {areas.map((area) => (
        <label key={area.id} className="alert-rule-toggle">
          <input
            checked={selectedIds.includes(area.id)}
            type="checkbox"
            onChange={() => onToggle(area.id)}
          />
          <span>{area.name}</span>
        </label>
      ))}
    </fieldset>
  );
}

function buildSummaryPath({
  floorId,
  siteId
}: {
  floorId: string | null;
  siteId: string | null;
}) {
  const params = new URLSearchParams();
  if (siteId) {
    params.set("site_id", siteId);
  }
  if (floorId) {
    params.set("floor_id", floorId);
  }
  return `/api/alerts/summary?${params.toString()}`;
}

function buildRulesPath({
  floorId,
  siteId
}: {
  floorId: string | null;
  siteId: string | null;
}) {
  const params = new URLSearchParams();
  if (siteId) {
    params.set("site_id", siteId);
  }
  if (floorId) {
    params.set("floor_id", floorId);
  }
  return `/api/alerts/rules?${params.toString()}`;
}

function buildAlertsPath({
  floorId,
  siteId,
  search,
  severity,
  statusValue,
  ruleType,
  range
}: {
  floorId: string | null;
  siteId: string | null;
  search: string;
  severity: string | null;
  statusValue: string | null;
  ruleType: string | null;
  range: string;
}) {
  const params = new URLSearchParams();
  if (siteId) {
    params.set("site_id", siteId);
  }
  if (floorId) {
    params.set("floor_id", floorId);
  }
  if (search) {
    params.set("search", search);
  }
  if (severity) {
    params.set("severity", severity);
  }
  if (statusValue) {
    params.set("status_value", statusValue);
  }
  if (ruleType) {
    params.set("rule_type", ruleType);
  }
  const rangeStart = timeRangeStart(range);
  if (rangeStart) {
    params.set("start_at", rangeStart);
  }
  return `/api/alerts?${params.toString()}`;
}

function buildRulePayload(draft: RuleDraft): AlertRuleUpsertPayload {
  const basePayload = {
    name: draft.name.trim(),
    rule_type: draft.ruleType,
    enabled: draft.enabled,
    notify_in_app: true,
    notify_email: draft.notifyEmail,
    email_recipients: parseEmailRecipients(draft.emailRecipients)
  };
  if (draft.ruleType === "table_sla") {
    return {
      ...basePayload,
      threshold_seconds: Number(draft.thresholdSeconds),
      table_area_ids: draft.tableAreaIds
    };
  }
  return {
    ...basePayload,
    area_ids: draft.areaIds,
    trigger_on: draft.triggerOn,
    asset_category: draft.assetCategory.trim() || null
  };
}

function parseEmailRecipients(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toggleSelection(values: string[], nextValue: string) {
  return values.includes(nextValue)
    ? values.filter((value) => value !== nextValue)
    : [...values, nextValue];
}

function relativeTime(value: string) {
  const deltaMs = Date.now() - Date.parse(value);
  const deltaMinutes = Math.round(deltaMs / 60000);
  if (Math.abs(deltaMinutes) < 1) {
    return "just now";
  }
  if (Math.abs(deltaMinutes) < 60) {
    return `${Math.abs(deltaMinutes)} min ago`;
  }
  const deltaHours = Math.round(deltaMinutes / 60);
  if (Math.abs(deltaHours) < 24) {
    return `${Math.abs(deltaHours)} h ago`;
  }
  const deltaDays = Math.round(deltaHours / 24);
  return `${Math.abs(deltaDays)} d ago`;
}

function timeRangeStart(range: string) {
  const now = new Date();
  if (range === "24h") {
    return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
  }
  if (range === "7d") {
    return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
  }
  if (range === "30d") {
    return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
  }
  return null;
}
