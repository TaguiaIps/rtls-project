## Why

The RTLS Analytics Platform now has the live monitoring shell, durable location history, and reusable derived-event primitives, but Carlos Mendes still lacks the dedicated Analytics workspace promised by the implementation plan. This change is needed now because trajectory replay, heatmaps, dwell reporting, round-trip analysis, and SLA trend views are the user-facing workflows that turn the existing location and derived-event foundations into operational intelligence instead of leaving them as backend-only building blocks.

## What Changes

- Add a delivered Analytics workspace in the protected web monitoring experience for authorized operations and administrator users.
- Add analytics read contracts and UI flows for the first report set: trajectory replay, heatmap generation, dwell-time reporting, round-trip reporting, and table SLA trend views.
- Reuse existing live-location history, zone-transition, dwell, round-trip, and current table timer foundations instead of recomputing analytics semantics from raw telemetry.
- Define filtering and scope rules for site, floor, time range, zone, route, and asset cohort selections so reports stay aligned with restaurant and catering operations terminology.
- Add explicit empty, degraded, and no-results states for analytics workflows so historical gaps do not read as healthy or complete operational coverage.
- Extend the shared web operations shell so Analytics becomes a delivered navigation destination once this change is implemented.
- Update architecture and planning documentation so the boundary stays clear: this change delivers interactive analytics reports and visualizations, while exports, rollups, long-horizon acceleration jobs, Overview redesign, and premium-tier analytics semantics remain later backlog items.

## Capabilities

### New Capabilities

- `analytics-workspace-and-reports`: Authorized Analytics workspace behavior, report filters, trajectory replay, heatmap visualization, dwell reporting, round-trip reporting, and SLA trend views.

### Modified Capabilities

- `web-operations-shell`: The shared monitoring shell gains a delivered Analytics destination once the Analytics workspace route exists.

## Impact

- Affects protected backend analytics query surfaces, derived-event readers, and supporting schemas in `apps/api`.
- Affects shared contracts and the React monitoring shell in `apps/web`, including Analytics navigation, route context, filters, charts, and map-based report views.
- Requires OpenSpec and documentation updates so this change consumes the existing live-location and derived-event foundations without silently taking on exports, observability, or later data-rollup work.
