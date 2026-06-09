## ADDED Requirements

### Requirement: Registered Premium gateways can publish Premium telemetry
The RTLS Analytics Platform SHALL accept supported AoA or UWB telemetry only from registered Premium gateways using the documented Premium ingestion contract.

#### Scenario: Registered Premium gateway publishes valid Premium telemetry
- **WHEN** a registered Premium gateway publishes a valid AoA or UWB telemetry message to the supported Premium ingestion contract
- **THEN** the system SHALL accept the message for ingestion processing

#### Scenario: Unsupported gateway or tier publishes Premium telemetry
- **WHEN** a telemetry message using the Premium contract is received from an unknown gateway or from a gateway not configured for Premium telemetry
- **THEN** the system SHALL reject the message and SHALL NOT treat it as accepted Premium telemetry

### Requirement: Premium telemetry preserves estimator-required measurement fidelity
The RTLS Analytics Platform SHALL persist the normalized Premium measurement fields required by Premium positioning before downstream estimation.

#### Scenario: Valid Premium telemetry is accepted
- **WHEN** a valid Premium telemetry message satisfies the supported payload contract
- **THEN** the ingestion flow SHALL persist the normalized modality, timing, quality, and measurement fields needed by the Premium estimator

#### Scenario: Premium telemetry omits required modality-specific fields
- **WHEN** a Premium telemetry message is missing modality-specific fields required for supported AoA or UWB processing
- **THEN** the system SHALL reject the message without creating Premium raw-measurement records

### Requirement: Premium telemetry preserves dedupe guarantees at higher update cadence
The RTLS Analytics Platform SHALL preserve duplicate-suppression guarantees for Premium telemetry without collapsing distinct high-frequency measurements into one accepted event.

#### Scenario: Distinct Premium measurements arrive at high rate
- **WHEN** a registered Premium gateway publishes successive Premium telemetry messages with distinct message identity inside a supported high-frequency window
- **THEN** the system SHALL treat those messages as distinct accepted telemetry instead of suppressing them as duplicates

#### Scenario: Premium telemetry message is replayed within the dedupe window
- **WHEN** the system receives a Premium telemetry message whose gateway and message identity match an already accepted Premium message within the configured dedupe window
- **THEN** the system SHALL suppress duplicate persistence for the replayed Premium message
