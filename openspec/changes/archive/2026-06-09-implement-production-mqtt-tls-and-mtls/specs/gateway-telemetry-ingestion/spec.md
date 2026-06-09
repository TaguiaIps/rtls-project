## MODIFIED Requirements

### Requirement: Registered gateway telemetry ingestion
The RTLS Analytics Platform SHALL accept MQTT telemetry only from registered gateways using the documented ingestion topic contract, provided they establish a secure mTLS connection.

#### Scenario: Registered gateway publishes valid telemetry over mTLS
- **WHEN** a registered gateway establishes a valid mTLS connection and publishes a valid telemetry message to the supported ingestion topic
- **THEN** the system SHALL accept the message for ingestion processing

#### Scenario: Registered gateway attempts to publish without mTLS
- **WHEN** a registered gateway attempts to publish telemetry over an unencrypted or non-mTLS connection
- **THEN** the broker SHALL refuse the connection and the message SHALL NOT be accepted

#### Scenario: Unknown gateway publishes telemetry
- **WHEN** a telemetry message is received for a gateway identifier that is not present in the gateway registry
- **THEN** the system SHALL reject the message and SHALL NOT treat it as accepted telemetry
