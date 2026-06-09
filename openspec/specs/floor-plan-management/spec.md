# floor-plan-management Specification

## Purpose
Define floor-linked raster plan upload, retrieval, and scale calibration so the platform has a stable physical map basis for spatial administration and later tracking workflows.
## Requirements
### Requirement: Raster floor-plan upload
The RTLS Analytics Platform SHALL allow authenticated Administrators to upload one raster floor-plan image per floor using supported image formats.

#### Scenario: Administrator uploads a supported floor-plan file
- **WHEN** an authenticated Administrator uploads a valid `PNG` or `JPG` floor-plan file for a floor
- **THEN** the system SHALL store the file and persist the floor-plan metadata linked to that floor

#### Scenario: Unsupported floor-plan format is submitted
- **WHEN** an authenticated Administrator uploads an unsupported floor-plan format
- **THEN** the system SHALL reject the upload with a validation error

### Requirement: Floor scale calibration
The RTLS Analytics Platform SHALL allow authenticated Administrators to calibrate floor scale using two reference points and a real-world measured distance.

#### Scenario: Administrator confirms floor scale
- **WHEN** an authenticated Administrator submits two reference points and a valid real-world distance for a floor plan
- **THEN** the system SHALL persist the calibration inputs and mark the floor scale as configured

#### Scenario: Invalid scale input is submitted
- **WHEN** the submitted calibration points or real-world distance are invalid
- **THEN** the system SHALL reject the calibration request with a validation error

### Requirement: Floor-plan retrieval for map context
The RTLS Analytics Platform SHALL expose floor-plan metadata and retrieval information so later protected web map workflows can render the correct floor context.

#### Scenario: Authorized client requests a floor plan
- **WHEN** an authorized client requests a configured floor's floor-plan details
- **THEN** the system SHALL return the floor-plan metadata and the information required to render the associated image

### Requirement: Calibration invalidation on floor-plan change
The RTLS Analytics Platform SHALL automatically invalidate active calibration artifacts (radiomaps and offsets) for a floor whenever its plan geometry or scale calibration is modified.

#### Scenario: Administrator updates floor scale
- **WHEN** an authenticated Administrator updates the scale calibration for a floor plan
- **THEN** the system SHALL mark all existing radiomap and offset artifacts for that floor as "invalid" or "stale"

#### Scenario: Administrator uploads a new floor-plan image
- **WHEN** an authenticated Administrator uploads a new raster floor-plan image that replaces an existing one
- **THEN** the system SHALL invalidate the active calibration artifacts for that floor, necessitating a new calibration session

