## ADDED Requirements

### Requirement: Registered gateway telemetry ingestion
The RTLS Analytics Platform SHALL accept MQTT telemetry only from registered gateways using the documented ingestion topic contract.

#### Scenario: Registered gateway publishes valid telemetry
- **WHEN** a registered gateway publishes a valid telemetry message to the supported ingestion topic
- **THEN** the system SHALL accept the message for ingestion processing

#### Scenario: Unknown gateway publishes telemetry
- **WHEN** a telemetry message is received for a gateway identifier that is not present in the gateway registry
- **THEN** the system SHALL reject the message and SHALL NOT treat it as accepted telemetry

### Requirement: Telemetry payload validation before durable writes
The RTLS Analytics Platform SHALL validate telemetry payload structure and required fields before it persists raw-ingestion state.

#### Scenario: Malformed telemetry payload is received
- **WHEN** a telemetry message is missing required fields or violates the supported payload contract
- **THEN** the system SHALL reject the message without creating raw-reading records

#### Scenario: Valid telemetry payload is received
- **WHEN** a telemetry message satisfies the supported payload contract
- **THEN** the system SHALL continue the message through duplicate checking and persistence processing

### Requirement: Duplicate-delivery protection for MQTT retries
The RTLS Analytics Platform SHALL protect the ingestion path from duplicate telemetry delivery caused by MQTT replay or retry behavior.

#### Scenario: Duplicate telemetry message is replayed within the dedupe window
- **WHEN** the system receives a telemetry message whose gateway and message identity match an already accepted message within the configured dedupe window
- **THEN** the system SHALL suppress duplicate persistence for the replayed message

### Requirement: Heartbeat ingestion for gateway health state
The RTLS Analytics Platform SHALL ingest gateway heartbeat messages and maintain a latest-known heartbeat state for backend health feeds.

#### Scenario: Registered gateway publishes a valid heartbeat
- **WHEN** a registered gateway publishes a valid heartbeat message to the supported heartbeat contract
- **THEN** the system SHALL update that gateway's latest-known heartbeat state

#### Scenario: Authorized client requests the gateway health feed
- **WHEN** an authorized backend consumer requests the gateway health feed
- **THEN** the system SHALL return the latest-known heartbeat state for registered gateways that have reported health data
