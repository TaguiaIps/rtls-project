# zone-and-poi-editor Specification

## Purpose
Define the typed operational area editor that lets Administrators create reusable floor-linked zones, tables, restricted areas, and POIs for later map, alerting, and analytics features.

## Requirements
### Requirement: Polygonal operational area editing
The RTLS Analytics Platform SHALL allow authenticated Administrators to create and edit polygonal operational areas on a floor plan.

#### Scenario: Administrator creates a polygonal area
- **WHEN** an authenticated Administrator submits a valid polygon on a configured floor
- **THEN** the system SHALL persist the area geometry and associate it with that floor

#### Scenario: Invalid polygon is submitted
- **WHEN** an authenticated Administrator submits an invalid polygon geometry
- **THEN** the system SHALL reject the request with a validation error

### Requirement: Typed operational areas
The RTLS Analytics Platform SHALL support typed operational areas for at least `zone`, `table`, `restricted zone`, and `POI`.

#### Scenario: Administrator defines a typed area
- **WHEN** an authenticated Administrator creates or edits an operational area
- **THEN** the system SHALL require one supported area type and persist that type with the geometry

#### Scenario: Unsupported area type is requested
- **WHEN** an authenticated Administrator submits an unsupported area type
- **THEN** the system SHALL reject the request with a validation error

### Requirement: Operational area metadata for later features
The RTLS Analytics Platform SHALL persist enough metadata on zones and POIs for later alerting, analytics, and live map rendering.

#### Scenario: Authorized client requests floor areas
- **WHEN** an authorized client retrieves the operational areas for a floor
- **THEN** the system SHALL return the stored geometry and business metadata needed for map display and later feature configuration
