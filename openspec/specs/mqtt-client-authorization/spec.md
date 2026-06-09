# mqtt-client-authorization Specification

## Purpose
Enforce broker-level topic authorization through Access Control Lists that restrict publish and subscribe actions based on authenticated gateway client identity.
## Requirements
### Requirement: Broker-Enforced Topic Authorization (ACLs)
The MQTT broker SHALL enforce Access Control Lists (ACLs) to restrict publish and subscribe actions based on the authenticated client identity.

#### Scenario: Gateway attempts to publish to authorized topic
- **WHEN** an mTLS-authenticated gateway attempts to publish telemetry to a topic matching its gateway identifier (e.g., `telemetry/<gateway_id>`)
- **THEN** the broker SHALL allow the publish operation

#### Scenario: Gateway attempts to publish to unauthorized topic
- **WHEN** an mTLS-authenticated gateway attempts to publish to a topic that does not match its identity or authorized patterns
- **THEN** the broker SHALL reject the publish operation

#### Scenario: Unauthorized client attempts to subscribe to telemetry
- **WHEN** a client without the required administrative or service-level authorization attempts to subscribe to the `telemetry/#` wildcard topic
- **THEN** the broker SHALL deny the subscription request

