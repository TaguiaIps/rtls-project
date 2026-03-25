## ADDED Requirements

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
