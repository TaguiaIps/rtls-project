# raw-reading-persistence Specification

## Purpose
Define the durable raw-reading persistence model and canonical time rules that downstream positioning, analytics, export, and debugging workflows will consume.
## Requirements
### Requirement: Canonical raw-reading persistence
The RTLS Analytics Platform SHALL persist accepted telemetry as durable raw readings linked to the publishing gateway and stamped with backend-controlled canonical time.

#### Scenario: Accepted telemetry is persisted
- **WHEN** a telemetry message from a registered gateway passes validation and duplicate checks
- **THEN** the system SHALL persist raw-reading records with the canonical broker-received timestamp and gateway linkage needed for later downstream processing

### Requirement: Gateway-provided time remains non-canonical metadata
The RTLS Analytics Platform SHALL treat gateway-provided event time as optional metadata and SHALL NOT replace canonical broker-received time with it.

#### Scenario: Telemetry includes gateway-provided time
- **WHEN** an accepted telemetry message includes a gateway-provided timestamp
- **THEN** the system SHALL preserve that timestamp as message metadata while continuing to use backend-controlled canonical time for ingestion ordering

#### Scenario: Telemetry omits gateway-provided time
- **WHEN** an accepted telemetry message does not include a gateway-provided timestamp
- **THEN** the system SHALL still persist the raw readings using canonical broker-received time

### Requirement: Raw-reading history remains available for later pipeline stages
The RTLS Analytics Platform SHALL persist raw readings in a durable form that later positioning, analytics, export, and debugging workflows can query without reparsing MQTT payloads.

#### Scenario: Later backend processing consumes raw telemetry
- **WHEN** a downstream backend workflow needs historical telemetry for a time range, gateway, or observed tag
- **THEN** the system SHALL be able to query the persisted raw-reading history directly from durable storage
