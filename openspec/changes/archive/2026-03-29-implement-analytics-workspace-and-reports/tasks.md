## 1. Analytics Contracts And Scope

- [x] 1.1 Define the shared Analytics request and response contracts for trajectory replay, heatmaps, dwell reports, round-trip reports, and SLA trend views.
- [x] 1.2 Resolve and document the supported SLA threshold baseline for historical trend highlighting so Analytics does not diverge from other table-SLA workflows.
- [x] 1.3 Document the scope boundary between this interactive Analytics delivery and the later exports, rollups, and long-horizon acceleration work.

## 2. Backend Analytics Query Layer

- [x] 2.1 Add protected backend query endpoints for trajectory replay and floor-scoped heatmap generation using durable location history.
- [x] 2.2 Add protected backend query endpoints for dwell reports, round-trip reports, and table SLA trend views using canonical derived-event history.
- [x] 2.3 Enforce validation and bounded query limits for floor scope, time range, asset or cohort selection, route filters, and supported reporting buckets.
- [x] 2.4 Add regression coverage for analytics authorization, validation, empty-result handling, and report query correctness.

## 3. Web Analytics Workspace

- [x] 3.1 Extend the shared monitoring shell with a delivered Analytics destination and preserved site or floor context when navigating into the workspace.
- [x] 3.2 Implement the Analytics workspace route with report switching, shared parameter controls, and explicit empty or degraded report states.
- [x] 3.3 Implement trajectory replay and heatmap visualization flows that align with the delivered backend contracts.
- [x] 3.4 Implement dwell, round-trip, and SLA trend report views with summary metrics, detailed context, and threshold-aware highlighting where supported.
- [x] 3.5 Add or update shared contracts and web tests for Analytics navigation, filter behavior, and report rendering.

## 4. Documentation And Validation

- [x] 4.1 Update architecture, requirements-alignment, and UX-facing documentation so delivered Analytics behavior and deferred export or rollup work remain explicit.
- [x] 4.2 Validate the change with `openspec validate implement-analytics-workspace-and-reports --strict`.
