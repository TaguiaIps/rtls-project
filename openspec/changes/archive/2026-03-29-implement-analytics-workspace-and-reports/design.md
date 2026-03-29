## Context

The RTLS Analytics Platform already has the main ingredients for historical reporting:

- a delivered protected operations shell with shared site and floor context
- durable live-location history for tracked assets
- canonical zone-transition and dwell history
- reusable round-trip primitives
- current table timer state and delivered table SLA alert rules in the current repository snapshot

What is still missing is the user-facing Analytics workspace that turns those backend foundations into repeatable operational reporting for Carlos Mendes. The analytics change crosses backend query contracts, shared TypeScript contracts, and the React monitoring shell. It also has a performance boundary: the first release needs meaningful historical reports without taking on the later exports, rollups, or long-horizon warehouse work reserved for follow-on backlog items.

## Goals / Non-Goals

**Goals:**

- Deliver a protected Analytics workspace inside the shared monitoring shell for authorized General Users and Administrators.
- Add read-only analytics query contracts for trajectory replay, heatmaps, dwell reports, round-trip reports, and SLA trend views.
- Reuse durable live-location history and derived-event data instead of recomputing business semantics from raw telemetry.
- Preserve shell context and deep-linkable report state so Analytics can participate in the same navigation model as Overview, Live Map, and Alerts Center.
- Keep the first implementation bounded enough to satisfy the reporting requirements without introducing async exports, rollups, or warehouse-specific infrastructure.

**Non-Goals:**

- Async exports, saved presets, scheduled report delivery, or share-and-collaborate workflows.
- Materialized rollups, nightly acceleration jobs, or broad retention changes that belong to the later exports and rollups change.
- Overview redesign, new alert workflows, or health-dashboard behavior outside the Analytics route itself.
- Premium-tier AoA/UWB analytics semantics or mobile analytics screens.

## Decisions

### 1. Analytics will be a shared shell destination with URL-backed report state

The Analytics workspace should be a first-class route inside the existing protected monitoring shell rather than a detached report page. The shell already owns current site and floor context, role-aware navigation, and live status treatment. Analytics should reuse that frame and keep report type, time range, selected asset, selected zones, and comparable filters in the URL where practical.

This makes report views refresh-safe, supports drill-in links from later Overview or Alerts surfaces, and avoids inventing a second state handoff model for historical workflows.

Alternatives considered:

- Keep analytics state in local component state only: rejected because reloads, deep links, and cross-route navigation become brittle for an operational tool.
- Add a separate standalone analytics shell: rejected because it would duplicate context selection and fragment the monitoring experience.

### 2. The backend should expose dedicated analytics query contracts, not a single generic report endpoint

Trajectory replay, heatmaps, dwell reports, round-trip reports, and SLA trends all consume different data shapes and visualization semantics. The backend should expose explicit analytics read contracts per report type so validation, authorization, and response structure stay precise.

That keeps the web client from stitching together low-level history and derived-event endpoints on its own and makes report-specific performance bounds easier to enforce.

Alternatives considered:

- One generic `/api/analytics/query` endpoint: rejected because it would centralize too many unrelated validation branches and produce weaker contracts.
- Client-side composition from raw history plus derived endpoints: rejected because it would duplicate aggregation logic in the web app and make report latency harder to control.

### 3. Trajectory replay and heatmaps should read durable location history, with server-side heatmap aggregation

Trajectory replay needs ordered historical points for one selected asset over a bounded window. Heatmaps need aggregated floor-scoped density data for cohorts over a bounded window. Both concerns should read accepted durable location history, but heatmaps should aggregate server-side into a grid or comparable floor-bounded density structure before returning data to the client.

This avoids shipping excessive raw points to the browser for dense cohorts and keeps visualization logic honest to the retained historical data.

Alternatives considered:

- Generate heatmaps entirely in the browser from raw points: rejected because payload size and client compute become unstable for larger windows.
- Create precomputed heatmap tables in this change: rejected because that belongs to the later exports, retention, and rollups work.

### 4. Dwell, round-trip, and SLA trend reports should consume canonical derived-event history

The analytics change should treat the derived-event layer as the source of truth for dwell and round-trip reporting. Dwell reports should aggregate closed dwell records. Round-trip reports should consume the route-parameterized round-trip primitive. SLA trend views should derive historical service timing from the same canonical visit history and apply a supported threshold baseline for the selected table scope instead of reinterpreting raw location points.

This preserves one definition of operational timing across Alerts and Analytics and keeps analytics from drifting away from the existing derived-event foundation.

Alternatives considered:

- Recompute dwell and round trips from raw history inside the analytics layer: rejected because it duplicates business semantics and creates disagreement risk.
- Depend on alert instances for historical SLA views: rejected because analytics should remain usable even when alert delivery or triage state is not the reporting source of truth.

### 5. The first release should stay synchronous and bounded by strict query limits

The first Analytics workspace should support on-demand queries only for bounded report windows. Trajectory queries should require a single asset and time range. Heatmaps should require a selected floor and bounded time range. Dwell, round-trip, and SLA trend queries should require explicit scope parameters and supported bucket sizes.

This aligns with the implementation plan boundary and keeps the change compatible with the `NFR-PER-003` expectation without prematurely introducing queue-backed report jobs.

Alternatives considered:

- Allow arbitrarily large historical windows from day one: rejected because it would push the first rollout into the territory reserved for later rollups and export acceleration.
- Implement async report jobs now: rejected because that would couple this change to the later exports and lifecycle-hardening backlog.

### 6. Empty, sparse, and unsupported-report states must be explicit

Analytics screens can easily mislead if an empty chart looks like healthy zero activity. The workspace should explicitly distinguish:

- no matching data for the selected scope
- insufficient retained history for the requested window
- unsupported parameter combinations or query sizes rejected by validation

This keeps Carlos from over-interpreting missing data as real operational calm.

Alternatives considered:

- Return blank charts with no explanation: rejected because it hides data-quality and scope issues.

## Risks / Trade-offs

- [Large historical windows can miss the performance target for heatmaps or trajectory replay] -> Mitigation: require bounded report scopes, aggregate heatmaps server-side, and reject unsupported broad queries instead of timing out silently.
- [The current SLA threshold source may be ambiguous for historical trend views] -> Mitigation: resolve one canonical threshold baseline during implementation and document whether it comes from report input, delivered alert-rule configuration, or another supported contract.
- [Different report types can drift into inconsistent filter semantics] -> Mitigation: define one shared filter vocabulary for site, floor, time range, cohort, and route scope, then layer report-specific fields on top.
- [Analytics can leak into later export or rollup scope] -> Mitigation: keep the initial delivery synchronous, read-only, and focused on interactive workspace use instead of downloadable bulk outputs.

## Migration Plan

1. Add the Analytics route contract and navigation entry to the shared monitoring shell.
2. Introduce report-specific backend query endpoints and shared request or response contracts for the delivered report set.
3. Build the React Analytics workspace around those bounded contracts, including explicit empty and degraded states.
4. Update documentation so the delivered Analytics scope, endpoint names, and deferred export or rollup work stay aligned.

## Open Questions

- Should historical SLA trend highlighting resolve its threshold baseline from delivered table SLA rule configuration, explicit report input, or another shared site-level policy contract?
