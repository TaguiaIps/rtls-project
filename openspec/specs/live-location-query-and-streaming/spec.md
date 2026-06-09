# live-location-query-and-streaming Specification

## Purpose
Expose real-time asset locations, search, trajectory history, and WebSocket streaming to authorized clients across all positioning tiers.
## Requirements
### Requirement: Authorized clients can query latest live locations
The RTLS Analytics Platform SHALL provide authorized query access to the latest known asset locations produced by the supported Economic-tier and Premium-tier positioning flows.

#### Scenario: Operations client requests current locations for a floor or site
- **WHEN** an authorized client requests latest known asset locations with supported floor, site, asset, or status filters
- **THEN** the system SHALL return the matching current location results from durable latest-known state together with source-tier and confidence or precision metadata when available

### Requirement: Authorized clients can search for an asset and retrieve its latest known location
The RTLS Analytics Platform SHALL provide an authorized live-search surface that resolves tracked assets to their latest known location context across the supported positioning tiers.

#### Scenario: User searches for a tracked asset
- **WHEN** an authorized client searches for a tracked asset using supported search fields
- **THEN** the system SHALL return matching assets together with their latest known location context, source-tier metadata, and confidence or precision metadata when available

### Requirement: Authorized clients can retrieve trajectory history
The RTLS Analytics Platform SHALL provide authorized time-bounded access to durable location history for tracked assets across the supported positioning tiers.

#### Scenario: User requests an asset trajectory for a time window
- **WHEN** an authorized client requests location history for a tracked asset and supported time range
- **THEN** the system SHALL return the asset's durable location history for that request window together with source-tier metadata for each supported history entry

### Requirement: Authorized clients can subscribe to live position updates
The RTLS Analytics Platform SHALL publish newly accepted location results from the supported positioning tiers to an authorized live-update stream for downstream operations consumers.

#### Scenario: Connected client is subscribed to live position updates
- **WHEN** the positioning flow produces a new accepted location result for a tracked asset
- **THEN** the system SHALL make that new location result available to authorized subscribers through the supported live-update stream together with source-tier and confidence or precision metadata
