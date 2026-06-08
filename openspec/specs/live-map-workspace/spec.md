# live-map-workspace Specification

## Purpose
TBD - created by archiving change deliver-web-shell-operations-overview-and-live-map. Update Purpose after archive.
## Requirements
### Requirement: Authorized users can inspect a floor-linked live map workspace
The RTLS Analytics Platform SHALL provide a Live Map workspace that renders the selected floor's mapped context together with current asset locations.

#### Scenario: User opens the Live Map for a mapped floor
- **WHEN** an authorized user opens the Live Map with a floor that has mapped spatial context
- **THEN** the workspace SHALL render the floor plan, operational areas, gateways, and current live asset locations for that floor

### Requirement: The Live Map supports search and filtering
The RTLS Analytics Platform SHALL allow users to narrow the visible live-map context with supported search and filter controls.

#### Scenario: User searches for an asset or applies filters
- **WHEN** the user submits a supported search term or filter set
- **THEN** the Live Map SHALL reduce the visible result set and retain the requested filter context

### Requirement: The Live Map visualizes confidence honestly
The RTLS Analytics Platform SHALL visualize live asset locations according to the confidence semantics already produced by the positioning layer.

#### Scenario: High-confidence point location is available
- **WHEN** a live asset location is returned with a credible point-level result
- **THEN** the map SHALL render a precise marker for that asset

#### Scenario: Degraded confidence or zone fallback is returned
- **WHEN** a live asset location is returned with degraded confidence or zone-level fallback
- **THEN** the map SHALL render a visibly different degraded-confidence or zone-level treatment instead of implying unchanged point precision

### Requirement: Users can inspect a selected asset in context
The RTLS Analytics Platform SHALL provide a selected-asset drawer in the Live Map workspace.

#### Scenario: User selects an asset from the map or search results
- **WHEN** the user selects a visible asset
- **THEN** the Live Map SHALL show a detail drawer with the asset's latest known location context, confidence state, and selection-preserving map context

### Requirement: The Live Map reflects live updates without a full reload
The RTLS Analytics Platform SHALL update the Live Map as new accepted live-location results arrive.

#### Scenario: A new live-location update is received for a visible asset
- **WHEN** the application receives a new accepted location result for an asset that matches the current map context
- **THEN** the workspace SHALL update the rendered map and selected-asset context without requiring a full page reload

