# live-map-workspace Specification

## Purpose
Render floor plans with confidence-aware asset overlays, faceted search and filtering, and interactive inspection within the protected monitoring shell.
## Requirements
### Requirement: Authorized users can inspect a floor-linked live map workspace
The RTLS Analytics Platform SHALL provide a Live Map workspace that renders the selected floor's mapped context using glassmorphism HUD overlays for floor details.

#### Scenario: User opens the Live Map for a mapped floor
- **WHEN** an authorized user opens the Live Map with a floor that has mapped spatial context
- **THEN** the workspace SHALL render the floor plan and assets with floating HUD modules using glassmorphism (backdrop blur) for metadata

### Requirement: The Live Map supports search and filtering
The RTLS Analytics Platform SHALL allow users to narrow the visible live-map context using a faceted search system that supports simultaneous combination of category, confidence, and status filters.

#### Scenario: User applies multiple filter facets
- **WHEN** an authorized user selects a specific asset category AND a specific confidence threshold in the search sidebar
- **THEN** the Live Map SHALL reduce the visible result set to only those assets satisfying BOTH facets simultaneously

### Requirement: The Live Map visualizes confidence honestly
The RTLS Analytics Platform SHALL visualize live asset locations according to the confidence semantics already produced by the positioning layer.

#### Scenario: High-confidence point location is available
- **WHEN** a live asset location is returned with a credible point-level result
- **THEN** the map SHALL render a precise marker for that asset

#### Scenario: Degraded confidence or zone fallback is returned
- **WHEN** a live asset location is returned with degraded confidence or zone-level fallback
- **THEN** the map SHALL render a visibly different degraded-confidence or zone-level treatment instead of implying unchanged point precision

### Requirement: Users can inspect a selected asset in context
The RTLS Analytics Platform SHALL provide a selected-asset drawer in the Live Map workspace that follows the high-density, no-border structural layout.

#### Scenario: User selects an asset from the map or search results
- **WHEN** the user selects a visible asset
- **THEN** the Live Map SHALL show a detail drawer with the "Deep Void" surface hierarchy and rigid geometry instead of rounded border-based containers

### Requirement: The Live Map reflects live updates without a full reload
The RTLS Analytics Platform SHALL update the Live Map as new accepted live-location results arrive.

#### Scenario: A new live-location update is received for a visible asset
- **WHEN** the application receives a new accepted location result for an asset that matches the current map context
- **THEN** the workspace SHALL update the rendered map and selected-asset context without requiring a full page reload

