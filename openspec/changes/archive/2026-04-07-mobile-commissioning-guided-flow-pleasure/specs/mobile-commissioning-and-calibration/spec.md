## MODIFIED Requirements

### Requirement: Mobile commissioning provides a guided blue-dot calibration workflow
The RTLS Analytics Platform SHALL provide a guided calibration walkthrough that renders floor-linked checkpoints, updates a visible tap-driven blue-dot position, and provides a segmented progress indicator as the operator captures progress through the route.

#### Scenario: Administrator starts a calibration walk
- **WHEN** the Administrator starts calibration for a selected floor and commissioning target with supported context loaded
- **THEN** the mobile app SHALL show a floor-linked route, the current checkpoint state, a segmented progress bar, and a visible tap-driven blue-dot position
