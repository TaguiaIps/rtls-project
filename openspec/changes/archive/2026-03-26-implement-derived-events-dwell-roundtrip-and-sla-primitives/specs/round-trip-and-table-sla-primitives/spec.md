# round-trip-and-table-sla-primitives Specification

## ADDED Requirements

### Requirement: Round-trip measurements are derived from canonical zone events
The RTLS Analytics Platform SHALL provide reusable round-trip measurement primitives that evaluate explicit origin-destination-origin cycles from canonical zone-transition history.

#### Scenario: Asset completes a round trip for a requested route
- **WHEN** a supported downstream workflow evaluates canonical zone events for a selected origin and destination and a tracked asset completes an origin-to-destination-to-origin cycle inside the requested time window
- **THEN** the system SHALL return one completed round-trip measurement with the cycle timestamps and durations for that asset

#### Scenario: Route sequence is incomplete
- **WHEN** the evaluated canonical zone events do not contain a complete origin-to-destination-to-origin sequence for a tracked asset inside the requested time window
- **THEN** the system SHALL NOT return a completed round-trip measurement for that partial sequence

### Requirement: SLA-eligible table areas maintain current timer state
The RTLS Analytics Platform SHALL maintain durable current timer state for table areas that are marked as SLA-eligible so later alerting and analytics workflows can consume a shared timing baseline.

#### Scenario: Accepted visit updates an SLA-eligible table
- **WHEN** accepted live-location processing records a qualifying visit to a spatial area that is typed as a table and marked `sla_eligible`
- **THEN** the system SHALL update durable current timer state for that table with the latest visit boundary and elapsed timing baseline

#### Scenario: Non-participating area is observed
- **WHEN** accepted live-location processing records activity for a spatial area that is not typed as a table or is not marked `sla_eligible`
- **THEN** the system SHALL NOT create or update current table timer state for that area

### Requirement: Current table timer state is readable by downstream workflows
The RTLS Analytics Platform SHALL expose the current timer state for SLA-eligible tables through a supported backend-facing read contract.

#### Scenario: Downstream workflow requests current timers
- **WHEN** an authorized backend workflow or supported query requests current timer state for SLA-eligible tables within a supported site or floor scope
- **THEN** the system SHALL return the current durable timer snapshot for the matching tables
