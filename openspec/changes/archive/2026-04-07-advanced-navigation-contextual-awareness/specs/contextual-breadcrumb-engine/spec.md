## ADDED Requirements

### Requirement: Dynamic Hierarchical Breadcrumbs
The RTLS Analytics Platform SHALL provide a dynamic breadcrumb trail in the Operations shell that reflects the current `Site > Floor > Workspace` hierarchy.

#### Scenario: User navigates to Live Map for a specific floor
- **WHEN** an authorized user navigates to the Live Map for "Main Dining" on the "Downtown" site
- **THEN** the Top Bar SHALL render a breadcrumb trail showing "Downtown > Main Dining > Live Map"

### Requirement: Breadcrumb Context Awareness
The breadcrumb trail SHALL remain synchronized with the shell context and URL parameters.

#### Scenario: User changes floor from the dropdown
- **WHEN** the user selects a different floor from the Top Bar control
- **THEN** the breadcrumb trail SHALL immediately update the floor segment to match the new selection
