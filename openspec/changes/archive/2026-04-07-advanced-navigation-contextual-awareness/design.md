## Context

The current `OperationsShell.tsx` handles site and floor selection through dropdowns in the Top Bar, but it lacks a visual trail of the user's current depth in the hierarchy. Additionally, the live feed status is currently a standalone "Live Pill" that doesn't explicitly link to the connectivity of the telemetry socket in a way that feels integral to the monitoring experience.

## Goals / Non-Goals

**Goals:**
- Implement a `BreadcrumbTrail` component that automatically derives `Site > Floor > Workspace` labels from the current URL and shell context.
- Integrate the `LiveFeedHeartbeat` directly into the breadcrumb or top-bar metadata area to provide constant connectivity reassurance.
- Standardize monoline icons across the `Command Rail` to match the "Industrial Command Deck" aesthetic.
- Ensure the Top Bar height remains fixed and compact to maximize map real estate.

**Non-Goals:**
- Changing the routing logic or how site/floor state is persisted in URL parameters.
- Adding breadcrumbs to the Admin workspace (this is focused on the Operations shell).

## Decisions

- **URL-Driven Breadcrumbs**: We will use `react-router-dom`'s `useLocation` and `matchRoutes` to determine the "Workspace" part of the breadcrumb trail, while using the `selectedSite` and `selectedFloor` from the shell context for the hierarchical parts.
  - *Rationale*: Leverages existing state and routing patterns without introducing a new navigation management system.
- **Icon Set Standardization**: Adopt monoline icons (e.g., Lucide-style) with a consistent 1.5px stroke weight for all rail items.
  - *Rationale*: Aligns with the "Information Authority" requirement of the Sentinel interface.
- **Heartbeat Animation**: Use a subtle "Pulse" animation (opacity 1.0 to 0.4) for the live indicator dot when the socket is active.
  - *Rationale*: Affective interface pattern to reduce user anxiety about data freshness.

## Risks / Trade-offs

- **[Risk]** Breadcrumb labels might overflow on smaller screens or with very long site names.
  - **Mitigation**: Use CSS truncation (`text-overflow: ellipsis`) for the "Site" and "Floor" segments while keeping the "Workspace" segment fully visible.
- **[Risk]** Constant animation of the heartbeat could be distracting.
  - **Mitigation**: Keep the animation very subtle and ensure it stops or turns static red when the connection is lost.
