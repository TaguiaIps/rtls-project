## 1. Contracts And Scope

- [x] 1.1 Define the protected web-shell contract, including role-aware navigation, shared top-bar context, and route expectations for delivered monitoring surfaces.
- [x] 1.2 Define the Operations Overview contract, including KPI summary fields, map-preview context, and priority-queue semantics that rely only on currently delivered live-location and health inputs.
- [x] 1.3 Define the Live Map contract, including floor selection, search and filter inputs, confidence visualization states, and selected-asset drawer content.

## 2. Backend And Shared Data Support

- [x] 2.1 Add or adjust the minimal read-only backend APIs needed to supply overview summary data to both Administrators and General Users.
- [x] 2.2 Add or update shared contracts in `packages/contracts` for overview summary data, shell state, and any new live-map request or response shapes required by the web app.
- [x] 2.3 Add regression coverage for any new backend summary or access-control behavior introduced for the operations shell.

## 3. Web Shell And Overview

- [x] 3.1 Implement the shared protected web shell in `apps/web`, including role-aware navigation, top-bar context, and route wiring for the delivered monitoring screens.
- [x] 3.2 Implement the Operations Overview screen with live KPI cards, a floor-linked map preview, a triage queue, and drill-in navigation into the Live Map.
- [x] 3.3 Add web tests covering protected shell routing, role-visible navigation, and overview loading, empty, and degraded states.

## 4. Live Map Workspace

- [x] 4.1 Implement the Live Map workspace with floor-plan rendering, zone and gateway overlays, live asset markers, and confidence-aware visual states.
- [x] 4.2 Implement search, filter, and selection behavior, including the selected-asset drawer and Overview-to-map deep-link behavior.
- [x] 4.3 Connect the map to the live-location query and streaming surfaces and add web tests for live updates, filter behavior, and confidence or fallback rendering.

## 5. Documentation And Validation

- [x] 5.1 Update the relevant system, UX, and implementation docs so the delivered web shell and live-map baseline are documented separately from later Alerts and Analytics backlog items.
- [x] 5.2 Validate the change with `openspec validate deliver-web-shell-operations-overview-and-live-map --strict`.
