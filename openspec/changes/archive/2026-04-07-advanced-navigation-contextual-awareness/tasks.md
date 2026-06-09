## 1. Breadcrumb & Top Bar Refactor

- [x] 1.1 Implement the `BreadcrumbTrail` component in `OperationsShell.tsx` using `selectedSite`, `selectedFloor`, and URL matching.
- [x] 1.2 Refactor the Top Bar layout to accommodate the breadcrumb trail and contextual dropdowns.
- [x] 1.3 Add CSS styles for breadcrumb segments, including truncation for long names and industrial separators (`›`).

## 2. Command Rail & Heartbeat

- [x] 2.1 Update navigation sidebar icons to monoline 1.5px stroke versions.
- [x] 2.2 Implement the `LiveFeedHeartbeat` component with a subtle pulse animation for "Live" status.
- [x] 2.3 Integrate the heartbeat status into the breadcrumb area or top-bar metadata section.

## 3. Global Verification

- [x] 3.1 Verify that breadcrumbs correctly update when switching sites or floors across all monitoring routes.
- [x] 3.2 Ensure the Top Bar remains under 15% screen height and doesn't obscure map content.
- [x] 3.3 Audit the "Command Rail" labels for consistent all-caps formatting and industrial spacing.
