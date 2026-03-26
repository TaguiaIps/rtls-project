# live-location-query-and-streaming Specification

## Purpose
TBD - created by archiving change implement-economic-tier-positioning-and-live-location. Update Purpose after archive.
## Requirements
### Requirement: Authorized clients can query latest live locations
The RTLS Analytics Platform SHALL provide authorized query access to the latest known asset locations produced by the economic-tier positioning flow.

#### Scenario: Operations client requests current locations for a floor or site
- **WHEN** an authorized client requests latest known asset locations with supported floor, site, asset, or status filters
- **THEN** the system SHALL return the matching current location results from durable latest-known state

### Requirement: Authorized clients can search for an asset and retrieve its latest known location
The RTLS Analytics Platform SHALL provide an authorized live-search surface that resolves tracked assets to their latest known location context.

#### Scenario: User searches for a tracked asset
- **WHEN** an authorized client searches for a tracked asset using supported search fields
- **THEN** the system SHALL return matching assets together with their latest known location context and confidence metadata when available

### Requirement: Authorized clients can retrieve trajectory history
The RTLS Analytics Platform SHALL provide authorized time-bounded access to durable location history for tracked assets.

#### Scenario: User requests an asset trajectory for a time window
- **WHEN** an authorized client requests location history for a tracked asset and supported time range
- **THEN** the system SHALL return the asset's durable location history for that request window

### Requirement: Authorized clients can subscribe to live position updates
The RTLS Analytics Platform SHALL publish newly accepted location results to an authorized live-update stream for downstream operations consumers.

#### Scenario: Connected client is subscribed to live position updates
- **WHEN** the positioning flow produces a new accepted location result for a tracked asset
- **THEN** the system SHALL make that new location result available to authorized subscribers through the supported live-update stream

