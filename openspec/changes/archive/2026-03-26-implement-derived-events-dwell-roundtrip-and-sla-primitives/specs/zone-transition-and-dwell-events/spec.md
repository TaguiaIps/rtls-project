# zone-transition-and-dwell-events Specification

## ADDED Requirements

### Requirement: Accepted live-location updates produce canonical zone transition events
The RTLS Analytics Platform SHALL derive canonical zone-entry and zone-exit events from accepted live-location updates when the resolved zone meaning for a tracked asset changes.

#### Scenario: Asset enters a resolved zone
- **WHEN** an accepted live-location update places a tracked asset in a resolved mapped zone after the asset was previously outside any resolved zone on that floor
- **THEN** the system SHALL persist a canonical zone-entry event for that asset and zone

#### Scenario: Asset moves from one resolved zone to another
- **WHEN** an accepted live-location update changes a tracked asset from one resolved zone to a different resolved zone
- **THEN** the system SHALL persist a canonical zone-exit event for the prior zone and a canonical zone-entry event for the new zone in the same transition boundary

#### Scenario: Asset remains in the same resolved zone
- **WHEN** subsequent accepted live-location updates keep a tracked asset in the same resolved zone
- **THEN** the system SHALL NOT emit duplicate zone-entry or zone-exit events for unchanged zone presence

### Requirement: Zone occupancy produces durable dwell records
The RTLS Analytics Platform SHALL derive durable dwell records from the occupancy window between canonical zone entry and the matching zone exit or occupancy closure.

#### Scenario: Asset exits a resolved zone
- **WHEN** a tracked asset leaves a resolved zone after a previously accepted entry
- **THEN** the system SHALL close the occupancy window and persist a dwell record with the zone, asset, start time, end time, and elapsed duration

#### Scenario: Resolved placement is lost
- **WHEN** an asset changes floors, loses resolved mapped placement, or otherwise no longer has a valid resolved zone after previously occupying one
- **THEN** the system SHALL close the prior occupancy window instead of leaving an open dwell record indefinitely

### Requirement: Derived zone events remain reusable for downstream workflows
The RTLS Analytics Platform SHALL preserve derived zone-transition and dwell history in a durable form that downstream workflows can query without reinterpreting raw locations.

#### Scenario: Downstream workflow requests prior zone visits
- **WHEN** an authorized backend workflow or supported query requests derived zone events by asset, floor, zone, or time range
- **THEN** the system SHALL return the matching canonical transition and dwell records from durable derived-event storage
