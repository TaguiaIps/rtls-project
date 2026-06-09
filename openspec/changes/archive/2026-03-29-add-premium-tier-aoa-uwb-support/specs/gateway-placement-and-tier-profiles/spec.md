## ADDED Requirements

### Requirement: Premium gateways capture modality and mounting metadata
The RTLS Analytics Platform SHALL require Premium gateways to persist the modality and mounting metadata needed for Premium-tier positioning.

#### Scenario: Administrator saves a Premium gateway profile
- **WHEN** an authenticated Administrator creates or updates a Premium gateway with supported modality and mounting details for an existing floor
- **THEN** the system SHALL persist the Premium gateway profile together with the tier assignment and floor-linked placement record

#### Scenario: Premium gateway profile omits required positioning metadata
- **WHEN** an authenticated Administrator submits a Premium gateway profile without the supported modality or required mounting metadata
- **THEN** the system SHALL reject the request with a validation error instead of storing an incomplete Premium gateway profile

### Requirement: Premium calibration state is tracked against the current floor and placement geometry
The RTLS Analytics Platform SHALL track whether a Premium gateway's calibration state remains valid for the current floor context and placement geometry.

#### Scenario: Administrator records supported Premium calibration state
- **WHEN** an authenticated Administrator saves supported Premium calibration or alignment state for a placed Premium gateway
- **THEN** the system SHALL persist that calibration-state metadata with the related gateway and floor context

#### Scenario: Floor or gateway geometry changes after Premium calibration
- **WHEN** the underlying floor geometry or a Premium gateway's placement changes after Premium calibration state was recorded
- **THEN** the system SHALL mark the affected Premium calibration state stale instead of silently treating it as still valid
