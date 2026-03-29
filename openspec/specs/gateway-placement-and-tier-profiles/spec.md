# gateway-placement-and-tier-profiles Specification

## Purpose
Define the Administrator-managed gateway registry, floor-linked placement model, and supported hardware tiers used by later ingestion and positioning workflows.
## Requirements
### Requirement: Administrator-managed gateway registry
The RTLS Analytics Platform SHALL allow authenticated Administrators to register and manage gateway records with stable identifiers and editable administrative metadata.

#### Scenario: Administrator registers a gateway
- **WHEN** an authenticated Administrator submits valid gateway details for an existing floor
- **THEN** the system SHALL persist a gateway record linked to that floor

#### Scenario: General User attempts to manage a gateway
- **WHEN** a General User requests a gateway-management action
- **THEN** the system SHALL deny the request with an authorization error

### Requirement: Floor-linked gateway placement
The RTLS Analytics Platform SHALL allow authenticated Administrators to place gateways on a floor using floor-relative coordinates.

#### Scenario: Administrator places a gateway on a floor plan
- **WHEN** an authenticated Administrator saves a gateway placement with valid floor-relative coordinates for an existing floor
- **THEN** the system SHALL persist the placement coordinates with the gateway record

#### Scenario: Placement is requested for a floor
- **WHEN** an authorized client requests the gateways assigned to a floor
- **THEN** the system SHALL return the stored placement coordinates and display metadata needed to render gateway markers

### Requirement: Economic and Premium tier assignment
The RTLS Analytics Platform SHALL support explicit gateway tier assignment for at least `Economic` and `Premium` hardware profiles.

#### Scenario: Administrator assigns a supported tier
- **WHEN** an authenticated Administrator creates or updates a gateway with a supported hardware tier
- **THEN** the system SHALL persist the selected tier with the gateway record

#### Scenario: Unsupported gateway tier is submitted
- **WHEN** an authenticated Administrator submits an unsupported hardware tier
- **THEN** the system SHALL reject the request with a validation error

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
