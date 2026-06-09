## ADDED Requirements

### Requirement: Calibration invalidation on floor-plan change
The RTLS Analytics Platform SHALL automatically invalidate active calibration artifacts (radiomaps and offsets) for a floor whenever its plan geometry or scale calibration is modified.

#### Scenario: Administrator updates floor scale
- **WHEN** an authenticated Administrator updates the scale calibration for a floor plan
- **THEN** the system SHALL mark all existing radiomap and offset artifacts for that floor as "invalid" or "stale"

#### Scenario: Administrator uploads a new floor-plan image
- **WHEN** an authenticated Administrator uploads a new raster floor-plan image that replaces an existing one
- **THEN** the system SHALL invalidate the active calibration artifacts for that floor, necessitating a new calibration session
