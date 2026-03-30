## ADDED Requirements

### Requirement: Authorized administrators can load mobile commissioning context
The RTLS Analytics Platform SHALL provide a mobile commissioning workflow that lets an authorized Administrator load site, floor, gateway, zone, and asset context from the delivered admin APIs.

#### Scenario: Administrator loads commissioning context
- **WHEN** an authorized Administrator opens the mobile commissioning workflow with a valid session and requests admin context
- **THEN** the mobile app SHALL retrieve the available sites, floors, and supporting registry data needed to start commissioning on a selected floor

#### Scenario: Commissioning context request is unauthorized
- **WHEN** the mobile commissioning workflow uses an invalid or non-administrator session
- **THEN** the app SHALL show an explicit authorization error instead of presenting stale or partial admin data as valid context

### Requirement: Mobile commissioning resolves scanned device identifiers
The RTLS Analytics Platform SHALL let an authorized Administrator resolve a scanned or entered device identifier against the delivered gateway and asset registries.

#### Scenario: Scanned identifier matches a known gateway or asset tag
- **WHEN** the Administrator submits a supported scanner or QR payload that matches an existing gateway identifier or asset tag identifier
- **THEN** the mobile app SHALL classify the scanned device, show its known identity, and preserve that selection for the commissioning session

#### Scenario: Scanned identifier is unknown
- **WHEN** the Administrator submits a scanner or QR payload that does not match a known gateway identifier or asset tag identifier
- **THEN** the mobile app SHALL show an explicit unknown-device state instead of silently pretending that commissioning can proceed against a registered record

### Requirement: Mobile commissioning supports zone assignment and floor-linked context
The RTLS Analytics Platform SHALL let an authorized Administrator assign the selected commissioning target to a supported zone or room on the selected floor before calibration begins.

#### Scenario: Administrator assigns the selected device to a zone
- **WHEN** the Administrator selects a supported zone or room for the active commissioning target
- **THEN** the mobile app SHALL show the selected floor, zone, and target context together in the commissioning detail view

### Requirement: Mobile commissioning provides a guided blue-dot calibration workflow
The RTLS Analytics Platform SHALL provide a guided calibration walkthrough that renders floor-linked checkpoints and updates a visible blue-dot position as the operator captures progress through the route.

#### Scenario: Administrator starts a calibration walk
- **WHEN** the Administrator starts calibration for a selected floor and commissioning target with supported context loaded
- **THEN** the mobile app SHALL show a floor-linked route, the current checkpoint state, and a visible blue-dot position for the active sample capture

#### Scenario: Administrator captures calibration progress
- **WHEN** the Administrator records a supported blue-dot capture during the calibration walk
- **THEN** the app SHALL update the calibration progress and sample count instead of leaving the session state unchanged

### Requirement: Mobile commissioning preserves local session summaries
The RTLS Analytics Platform SHALL preserve recent commissioning and calibration session summaries on the mobile device for later review.

#### Scenario: Administrator completes a commissioning session
- **WHEN** the Administrator completes a mobile commissioning or calibration workflow
- **THEN** the app SHALL store a session summary with target identity, selected floor and zone context, elapsed timing, and captured progress metrics

#### Scenario: Commissioning session already exists in local history
- **WHEN** a later commissioning summary refers to the same target on the same floor
- **THEN** the app SHALL keep the most recent summary at the top of the local session history instead of duplicating stale entries
