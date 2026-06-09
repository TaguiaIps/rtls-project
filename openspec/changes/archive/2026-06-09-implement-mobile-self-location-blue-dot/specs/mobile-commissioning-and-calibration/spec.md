## MODIFIED Requirements

### Requirement: Mobile commissioning provides a guided blue-dot calibration workflow
The RTLS Analytics Platform SHALL provide a guided calibration walkthrough that supports both live self-location blue-dot tracking and manual tap-driven fallback for capturing progress through the route.

#### Scenario: Administrator starts a live blue-dot calibration walk
- **WHEN** the Administrator starts calibration for a selected floor and chooses "Live Tracking" mode
- **THEN** the mobile app SHALL establish a self-location stream and render a continuously updated blue dot along the floor-linked route

#### Scenario: Administrator captures progress in live mode
- **WHEN** the Administrator is in "Live Tracking" mode during a calibration walk
- **THEN** the mobile app SHALL automatically associate signal samples with the current live blue-dot position and update the progress indicator

#### Scenario: Administrator falls back to manual tap mode
- **WHEN** live tracking is unavailable, degraded, or explicitly disabled by the Administrator
- **THEN** the mobile app SHALL allow the Administrator to capture progress using manual floor taps as checkpoints

#### Scenario: Administrator captures calibration progress (Manual Fallback)
- **WHEN** the Administrator records a supported blue-dot capture during the calibration walk in manual mode
- **THEN** the app SHALL update the calibration progress and sample count from the selected floor tap instead of leaving the session state unchanged
