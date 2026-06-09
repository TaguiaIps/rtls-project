## MODIFIED Requirements

### Requirement: Authorized users can inspect a floor-linked live map workspace
The RTLS Analytics Platform SHALL provide a Live Map workspace that renders the selected floor's mapped context using glassmorphism HUD overlays for floor details.

#### Scenario: User opens the Live Map for a mapped floor
- **WHEN** an authorized user opens the Live Map with a floor that has mapped spatial context
- **THEN** the workspace SHALL render the floor plan and assets with floating HUD modules using glassmorphism (backdrop blur) for metadata

### Requirement: Users can inspect a selected asset in context
The RTLS Analytics Platform SHALL provide a selected-asset drawer in the Live Map workspace that follows the high-density, no-border structural layout.

#### Scenario: User selects an asset from the map or search results
- **WHEN** the user selects a visible asset
- **THEN** the Live Map SHALL show a detail drawer with the "Deep Void" surface hierarchy and rigid geometry instead of rounded border-based containers
