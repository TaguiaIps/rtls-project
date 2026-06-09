## MODIFIED Requirements

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

## ADDED Requirements

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
