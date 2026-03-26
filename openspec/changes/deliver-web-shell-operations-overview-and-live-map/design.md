## Context

The current web application already supports local sign-in, role-based redirects, and an administrator-focused spatial workspace, but it does not yet provide the operational shell promised in the implementation plan. The repository also already contains backend building blocks the shell should consume: authenticated current-user context, site and floor metadata, floor-plan retrieval, zone and gateway geometry, live location queries, live location streaming, and gateway heartbeat health.

This change spans multiple layers:

- `apps/web` needs a real shell, route structure, overview page, and map workspace.
- `packages/contracts` needs client-facing shapes for overview snapshots and shell state where the current contracts are insufficient.
- `apps/api` may need a narrow read-only operations summary surface because the current live-location and floor-detail APIs are useful but do not directly provide a safe overview aggregate for both Administrators and General Users.

The main constraint is sequencing. This backlog item comes before the derived-event engine, alert rules, and analytics workspace, so the web shell cannot pretend those later data products already exist. It needs to deliver a credible operations experience using only the live-location, floor, and health data that already exist or can be added with minimal read-only support.

## Goals / Non-Goals

**Goals:**

- Deliver a protected web shell that supports the currently implemented monitoring surfaces for both Administrators and General Users.
- Provide an Operations Overview that helps a user understand live operational state quickly using currently available location and health signals.
- Provide a Live Map workspace that is map-first, supports floor selection, and accurately communicates location confidence.
- Reuse existing live-location and spatial APIs wherever possible, adding only the smallest extra read-only backend surface needed for overview summaries.
- Keep navigation, naming, and visual intent aligned with `docs/ux-design.md` and the normalized prototype guidance.

**Non-Goals:**

- Implement the later Alerts Center, alert acknowledgement flow, or alert rule engine.
- Implement analytics pages, trajectory replay workspace, SLA trend reports, or dwell and round-trip computations.
- Implement premium-tier AoA or UWB map behavior.
- Redesign the administrator spatial editor delivered in earlier backlog items.

## Decisions

### 1. The web shell will be a shared protected frame, not page-local chrome

The shell should become the single protected frame for web monitoring areas, with the rail, top bar, and user context rendered once around the page content. That keeps navigation, sign-out, current-user context, and live connection treatment consistent between Overview and Live Map.

This change extends the existing role-aware routing instead of replacing it. Administrators keep access to Admin and also gain the shared monitoring shell, while General Users see only the operations destinations they are allowed to open.

Alternative considered:

- Keep each page self-contained with repeated headers and navigation. This is simpler short-term but creates duplicated state and makes later Alerts, Analytics, Health, and Audit Log pages harder to add consistently.

### 2. The overview will use a dedicated read-only summary contract

The current backend already exposes live locations, floor detail, and gateway health, but the Overview needs a combined snapshot for KPI cards, a map preview, and a small priority queue. Building that purely as client-side fan-out would force the web app to coordinate multiple requests and would also reuse an admin-only gateway health endpoint for a screen that General Users must be able to open.

The design therefore prefers a narrow operations-summary contract authorized for both roles. That summary can aggregate only the data the Overview needs now:

- current site and floor context
- live connection or feed freshness status
- current operational KPI counts derived from live locations and gateway health
- a short priority queue derived from available degraded-confidence, stale-location, or gateway-health conditions
- compact map-preview context for the selected floor

Alternative considered:

- Compose the Overview entirely from existing endpoints and broaden `gateway-health` access. That keeps the backend smaller but leaks admin-shaped health data into general monitoring and makes the web app own more cross-endpoint aggregation logic than it should.

### 3. The Live Map will reuse the existing spatial and live-location surfaces

The Live Map does not need a new map-specific backend bundle if it can combine:

- floor detail for floor plan, areas, and gateways
- latest live locations for current markers
- live-update streaming for incremental changes

This keeps the backend change tightly scoped. The main additional backend need is overview aggregation, not a second map query model.

Alternative considered:

- Add a single map bootstrap endpoint that returns floor detail plus current locations together. That can be revisited later if web composition becomes a measurable performance problem, but it is unnecessary complexity for the first delivered map workspace.

### 4. Confidence visualization must mirror the delivered location contract exactly

The map should render only the confidence semantics that the positioning layer already produces:

- high-confidence point markers
- degraded point states with a visible radius or caution treatment
- low-confidence zone fallback wash when only zone-level placement is available

The UI must not imply more spatial precision than the backend can justify. This keeps the interface honest and matches the existing product requirement for confidence-aware location visibility.

Alternative considered:

- Smooth or interpolate positions for aesthetic continuity. That would look polished but would misrepresent the actual certainty of economic-tier positioning.

### 5. Route and filter state should live in the URL

The shell and Live Map should preserve site, floor, search, and selection state in URL parameters where practical. This supports refresh-safe behavior, direct linking from Overview to Live Map, and future cross-links from alerts or analytics without inventing a second state handoff mechanism.

Alternative considered:

- Keep all UI state in component-local state only. That is simpler to start but makes drill-in links and page refresh behavior weaker for an operational tool.

### 6. Not-yet-built alerts and analytics remain explicit follow-on work

The shell can reserve navigation structure for future pages, but this change should only promise working destinations backed by currently implemented behavior. The Overview will therefore summarize currently available operational and health signals rather than fake future SLA or alert engines.

Alternative considered:

- Ship empty placeholder pages for Alerts, Analytics, Health, or Audit Log. That adds UI noise without delivering user value and weakens the backlog boundary.

## Risks / Trade-offs

- **Overview expectations may drift toward alerting and analytics behavior** -> Keep the spec language explicit that overview triage is derived only from live-location and health signals available in this phase, and defer richer incident logic to later changes.
- **General User access to health information could overshare admin detail** -> Limit the overview summary contract to operationally relevant counts and brief issue context instead of exposing full admin diagnostics.
- **Combining multiple live data sources can create inconsistent freshness windows** -> Define one shell-level freshness treatment so the Overview and Live Map can communicate stale or degraded feeds consistently.
- **Map rendering complexity can grow quickly on a dense floor** -> Keep the first version focused on one selected floor, contract-backed filters, and a lightweight asset drawer rather than clustering, replay, or advanced overlays.
