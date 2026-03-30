## Context

The repository already has the core backend state needed for an administrative health and audit surface: audit events are persisted for authentication and configuration mutations, gateway heartbeats are projected into latest-known state, and alert instances and ingestion tables exist for operational summaries. The web app, however, still routes administrators only into the spatial workspace, and the backend has no dedicated audit-query or observability-summary APIs.

Constraints:

- the repo has no external Prometheus, Grafana, or tracing collector dependency today
- existing audit records are append-only and already normalized for later filtering
- gateway-health data is latest-known state, not a full uptime analytics history
- the delivered web shell should preserve existing admin and monitoring behavior instead of being replaced wholesale

Stakeholders:

- Alex needs one protected place to review stale or low-battery gateways, recent alert pressure, runtime service posture, and configuration or authentication audit history
- future lifecycle and export work needs a stable observability baseline and an audit-review surface before adding more operational complexity

## Goals / Non-Goals

**Goals:**

- add a dedicated administrator shell for Spatial, Health, and Audit views
- expose filterable audit-event history through a supported backend API
- expose a compact observability summary driven by existing audit, heartbeat, alert, and ingestion data
- add a lightweight `/metrics` text endpoint and request-id response header baseline
- keep contracts shared across backend and web so the admin UI is strongly typed

**Non-Goals:**

- full distributed tracing export, OpenTelemetry collectors, or external dashboard provisioning
- long-term heartbeat trend analytics or packet-loss reconstruction from raw telemetry
- replacing the delivered Alerts Center or Operations Overview for general users
- adding a separate monitoring database or metrics service inside this repo

## Decisions

### 1. The admin experience will become a small route-aware shell instead of another isolated screen

Administrators already have one substantial workspace. Adding Health and Audit as sibling views under the `/admin` area keeps the experience coherent and avoids duplicating auth or layout code.

Alternative considered:
- keeping Health and Audit as disconnected pages was rejected because it would fragment the administrator workflow and repeat shared context.

### 2. Observability summary should be derived from existing latest-known tables and recent events

The repo already has enough durable state to answer the first operational questions: how many gateways are stale, which batteries are low, how much telemetry has been accepted, how many open alerts exist, and what recent audit activity occurred. Reusing that data keeps the change small and credible.

Alternative considered:
- adding a new monitoring projection service was rejected because it would create a second source of truth before the current admin UI is even delivered.

### 3. The metrics baseline should be a simple text exposition endpoint plus request-id headers

The implementation plan calls for a metrics and tracing baseline, but the repo does not yet include a full tracing stack. A `/metrics` endpoint with key counts and gauges, combined with an `X-Request-ID` response header, is enough to make local verification and future exporter integration concrete without new infrastructure.

Alternative considered:
- adding Prometheus or OpenTelemetry dependencies now was rejected because it would inflate the scope and operational surface of this change.

### 4. Audit review should use server-side filtering instead of downloading all events into the browser

Audit events will keep growing, and the existing audit-event spec explicitly anticipates filtering by actor, category, target, and time window. The UI should pass filters to the backend query surface and render a bounded result set.

Alternative considered:
- loading all audit events client-side was rejected because it would become inefficient and would sidestep the delivered query-ready audit model.

## Risks / Trade-offs

- [Risk] The metrics baseline is intentionally lightweight and not a substitute for production telemetry pipelines. → Mitigation: document it as a baseline and expose stable paths and headers that later exporters can build on.
- [Risk] Gateway health remains latest-known state and may miss deeper historical failure patterns. → Mitigation: present it honestly as a current health snapshot rather than a full uptime report.
- [Risk] Audit-event filtering could become expensive if the result set grows without indexes or bounds. → Mitigation: keep filters server-side, use descending time order, and cap page sizes in the delivered API.

## Migration Plan

1. Add shared audit and observability contracts plus backend schemas.
2. Implement backend admin APIs for audit-event query, observability summary, metrics exposition, and request-id headers.
3. Refactor the web admin route into a small shell and add Health and Audit views.
4. Add backend and web regression tests.
5. Update docs, validate the change, sync specs, and archive it.

## Open Questions

- Should a later change extend the metrics baseline with per-endpoint latency histograms, or keep this repo-level `/metrics` endpoint focused on coarse operational gauges only?
