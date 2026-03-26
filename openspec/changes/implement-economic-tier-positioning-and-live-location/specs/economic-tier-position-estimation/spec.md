# economic-tier-position-estimation Specification

## ADDED Requirements

### Requirement: Economic-tier telemetry produces durable asset locations
The RTLS Analytics Platform SHALL derive durable asset location outputs from accepted economic-tier BLE raw readings for registered tracked assets on mapped floors.

#### Scenario: Accepted raw readings support an asset position update
- **WHEN** accepted raw readings for a registered tracked asset are available with the mapped-floor and registry context needed for economic-tier positioning
- **THEN** the system SHALL produce a new location result for that asset instead of requiring downstream clients to interpret raw readings directly

### Requirement: Current asset location and location history are both preserved
The RTLS Analytics Platform SHALL preserve both the latest known location state and append-only location history for positioned assets.

#### Scenario: A new location result is produced
- **WHEN** the positioning flow accepts a newer location result for a tracked asset
- **THEN** the system SHALL update the asset's latest known location state and SHALL append the result to durable location history

#### Scenario: A downstream workflow needs prior movements
- **WHEN** an authorized backend or client workflow requests a tracked asset's prior movements
- **THEN** the system SHALL be able to retrieve the asset's location history without reconstructing it from raw MQTT payloads

### Requirement: Location outputs include confidence semantics
The RTLS Analytics Platform SHALL attach confidence metadata to economic-tier location outputs so downstream workflows can distinguish credible point estimates from degraded results.

#### Scenario: A credible point estimate is available
- **WHEN** the positioning flow determines that the available economic-tier telemetry supports a credible point-level result
- **THEN** the location output SHALL include confidence metadata describing that result

#### Scenario: Confidence is degraded
- **WHEN** the available telemetry does not support the same precision as a credible point-level result
- **THEN** the location output SHALL still indicate the degraded confidence state instead of implying unchanged point precision

### Requirement: Low-confidence results fall back to zone-level placement
The RTLS Analytics Platform SHALL prefer an explicit zone-level fallback over misleading point precision when economic-tier confidence is insufficient.

#### Scenario: Zone fallback is required
- **WHEN** the positioning flow can place an asset within a known mapped zone but cannot justify point-level precision
- **THEN** the system SHALL emit a zone-level location result with the associated degraded confidence state

#### Scenario: No valid mapped placement can be derived
- **WHEN** the positioning flow lacks the information required to derive either a point-level or zone-level mapped placement
- **THEN** the system SHALL NOT publish a misleading new location result for that asset
