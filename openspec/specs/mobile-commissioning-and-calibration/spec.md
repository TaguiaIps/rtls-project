# mobile-commissioning-and-calibration Specification

## Purpose

Guide authorized administrators through device intake workflows including camera-based QR scanning, gateway and asset registry resolution, zone assignment, and calibration sessions.

## Requirements

### Requirement: Authorized administrators can load mobile commissioning context

The RTLS Analytics Platform SHALL provide a mobile commissioning workflow that lets an authorized Administrator load site, floor, gateway, zone, and asset context from the delivered admin APIs.

#### Scenario: Administrator loads commissioning context

- **WHEN** an authorized Administrator opens the mobile commissioning workflow with a valid session and requests admin context
- **THEN** the mobile app SHALL retrieve the available sites, floors, and supporting registry data needed to start commissioning on a selected floor

#### Scenario: Commissioning context request is unauthorized

- **WHEN** the mobile commissioning workflow uses an invalid or non-administrator session
- **THEN** the app SHALL show an explicit authorization error instead of presenting stale or partial admin data as valid context

### Requirement: Mobile commissioning resolves scanned device identifiers

The RTLS Analytics Platform SHALL let an authorized Administrator resolve a native camera-scanned, externally scanned, or manually entered device identifier against the delivered gateway and asset registries.

#### Scenario: Camera-scanned identifier matches a known gateway or asset tag

- **WHEN** the Administrator scans a supported QR payload with the mobile camera and the normalized identifier matches an existing gateway identifier or asset tag identifier
- **THEN** the mobile app SHALL classify the scanned device, show its known identity, and preserve that selection for the commissioning session

#### Scenario: Camera-scanned identifier is unknown

- **WHEN** the Administrator scans a supported QR payload and the normalized identifier does not match a known gateway identifier or asset tag identifier
- **THEN** the mobile app SHALL show an explicit unknown-device state instead of silently pretending that commissioning can proceed against a registered record

#### Scenario: Manual fallback uses the same registry resolution path

- **WHEN** the Administrator enters or externally scans a supported identifier into the fallback input field
- **THEN** the mobile app SHALL normalize that payload and resolve it against the same delivered gateway and asset registries used by camera scanning

### Requirement: Mobile commissioning supports zone assignment and floor-linked context

The RTLS Analytics Platform SHALL let an authorized Administrator assign the selected commissioning target to a supported zone or room on the selected floor before calibration begins.

#### Scenario: Administrator assigns the selected device to a zone

- **WHEN** the Administrator selects a supported zone or room for the active commissioning target
- **THEN** the mobile app SHALL show the selected floor, zone, and target context together in the commissioning detail view

### Requirement: Mobile commissioning provides a guided blue-dot calibration workflow

The RTLS Analytics Platform SHALL provide a guided calibration walkthrough that supports both live self-location blue-dot tracking and manual tap-driven fallback for capturing progress through the route.

#### Scenario: Administrator starts a live blue-dot calibration walk

- **WHEN** the Administrator starts calibration for a selected floor and chooses "Live Tracking" mode
- **THEN** the mobile app SHALL establish a self-location stream and render a continuously updated blue dot along the floor-linked route

#### Scenario: Administrator captures progress in live mode

- **WHEN** the Administrator is in "Live Tracking" mode during a calibration walk
- **THEN** the mobile app SHALL automatically associate signal samples with the current live blue-dot position and update the progress indicator

#### Scenario: Administrator falls back to manual tap mode

- **WHEN** live tracking is unavailable, degraded, or explicitly disabled by the Administrator
- **THEN** the mobile app SHALL allow the Administrator to capture progress using manual floor taps as checkpoints

#### Scenario: Administrator captures calibration progress (Manual Fallback)

- **WHEN** the Administrator records a supported blue-dot capture during the calibration walk in manual mode
- **THEN** the app SHALL update the calibration progress and sample count from the selected floor tap instead of leaving the session state unchanged

### Requirement: Mobile commissioning preserves local session summaries

The RTLS Analytics Platform SHALL preserve recent commissioning and calibration session summaries on the mobile device for later review.

#### Scenario: Administrator completes a commissioning session

- **WHEN** the Administrator completes a mobile commissioning or calibration workflow
- **THEN** the app SHALL store a session summary with target identity, selected floor and zone context, elapsed timing, and captured progress metrics

#### Scenario: Commissioning session already exists in local history

- **WHEN** a later commissioning summary refers to the same target on the same floor
- **THEN** the app SHALL keep the most recent summary at the top of the local session history instead of duplicating stale entries

### Requirement: Mobile commissioning handles camera scanning availability explicitly

The RTLS Analytics Platform SHALL provide explicit permission, availability, and retry states for native camera scanning without blocking fallback commissioning entry paths.

#### Scenario: Camera permission is not yet granted

- **WHEN** the Administrator opens the native camera scanner before camera permission has been granted
- **THEN** the mobile app SHALL request camera access or show a clear permission action instead of presenting a blank scanning surface

#### Scenario: Camera scanning is unavailable or unsuitable for the current device

- **WHEN** the Administrator cannot use native camera scanning because of device limitations, denied permissions, or simulator constraints
- **THEN** the mobile app SHALL keep manual or external-scanner identifier entry available for the same commissioning workflow

#### Scenario: Operator wants to rescan a QR code

- **WHEN** the Administrator completes one QR scan and chooses to scan again
- **THEN** the mobile app SHALL let the operator re-arm scanning explicitly instead of requiring a full workflow reset

### Requirement: Calibration session submission and backend handshake

The mobile commissioning workflow SHALL support the submission of completed calibration sessions to the backend and provide status updates on processing.

#### Scenario: Mobile app submits a calibration session

- **WHEN** the Administrator completes a calibration walk and submits the session to the backend
- **THEN** the app SHALL show a "Processing" status while the backend calibration engine generates the new radiomap and offsets

#### Scenario: Backend processing completes

- **WHEN** the backend calibration engine successfully processes a submitted session
- **THEN** the mobile app SHALL update the session summary to indicate that the calibration is "Active" on the floor
