## Why

The RTLS Analytics Platform now has authentication, mapped floors, registered assets and gateways, gateway health signals, and live asset-location APIs, but the web application still stops at sign-in plus a narrow administrator setup workspace. The next backlog item needs to turn those backend foundations into a usable operations surface so Carlos and Alex can actually monitor live service activity from the web.

This change is needed now because later alerting, analytics, and mobile workflows all assume there is already a shared web shell and a map-first operational workspace. Without that baseline, the platform has live location data but no operator-facing place to consume it.

## What Changes

- Add a protected web operations shell with role-aware navigation, shared top-bar context, and routes for the currently delivered monitoring surfaces.
- Add an Operations Overview experience that summarizes live service state using currently available live-location and infrastructure-health data, with direct drill-in actions into the Live Map.
- Add a Live Map workspace that renders floor plans, zones, gateways, live asset markers, confidence states, search/filter controls, and a selected-asset drawer.
- Add the minimal read-only backend and shared-contract support needed for overview summaries and non-admin consumption of operational snapshot data.
- Update system, UX, and implementation docs so the delivered shell and map behavior are clearly separated from later alert-center, analytics, and derived-event backlog items.
- Keep full Alerts Center workflows, derived SLA and dwell metrics, historical analytics screens, and premium-tier visualization out of scope for this change.

## Capabilities

### New Capabilities

- `web-operations-shell`: Covers the protected React shell, role-aware navigation, shared site or floor context, and top-bar operational status chrome.
- `operations-overview-dashboard`: Covers the overview landing experience, KPI and triage summary behavior, map preview, and overview drill-in actions.
- `live-map-workspace`: Covers the interactive live map, search and filter behavior, confidence visualization, asset selection, and live-update handling.

### Modified Capabilities

- None.

## Impact

- Affects `apps/web` routing, layout, state management, and the first non-admin monitoring screens.
- Affects `packages/contracts` and likely small backend read-only APIs so the web shell can consume overview and operational snapshot data without admin-only coupling.
- Reuses and surfaces existing foundations from authentication, spatial management, live locations, and gateway health rather than introducing a second monitoring data model.
- Requires documentation updates in `docs/` and new OpenSpec capability definitions so the backlog distinction between current web monitoring, later alerts, and later analytics stays explicit.
