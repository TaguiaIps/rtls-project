# premium-tier-position-estimation Specification

## Purpose
TBD - created by archiving change add-premium-tier-aoa-uwb-support. Update Purpose after archive.
## Requirements
### Requirement: Premium-tier telemetry produces durable asset locations
The RTLS Analytics Platform SHALL derive durable asset location outputs from accepted Premium-tier AoA or UWB measurements for registered tracked assets on mapped floors.

#### Scenario: Accepted Premium measurements support an asset position update
- **WHEN** accepted Premium-tier telemetry for a registered tracked asset is available together with the mapped-floor and gateway context required for Premium estimation
- **THEN** the system SHALL produce a new Premium-tier location result for that asset instead of requiring downstream clients to interpret raw AoA or UWB measurements directly

#### Scenario: Premium telemetry lacks valid estimation context
- **WHEN** accepted Premium-tier telemetry cannot be matched to the required mapped-floor, gateway, or tracked-asset context
- **THEN** the system SHALL NOT publish a misleading new Premium-tier location result for that asset

### Requirement: Premium-tier positioning depends on valid Premium gateway geometry and calibration state
The RTLS Analytics Platform SHALL use Premium gateway geometry and current calibration state when deriving Premium-tier location outputs.

#### Scenario: Premium gateway geometry and calibration are valid
- **WHEN** the estimator receives accepted Premium measurements from gateways whose required placement geometry and calibration state are valid for the current floor context
- **THEN** the system SHALL use that Premium placement context during location estimation

#### Scenario: Premium gateway calibration is stale or invalid
- **WHEN** Premium telemetry arrives for a floor whose required Premium calibration state is stale, missing, or invalid for the relevant gateways
- **THEN** the system SHALL reject or degrade Premium estimation according to supported confidence rules instead of implying unchanged high-precision positioning

### Requirement: Premium-tier outputs include modality-aware source and precision semantics
The RTLS Analytics Platform SHALL attach modality-aware source and precision metadata to Premium-tier location outputs so downstream workflows can distinguish AoA and UWB results from Economic-tier estimates.

#### Scenario: Premium location output is produced
- **WHEN** the Premium positioning flow produces a new accepted location result
- **THEN** the location output SHALL include source-tier metadata, source-modality metadata, and precision or confidence metadata describing the supported quality of that result

#### Scenario: Premium result quality is degraded
- **WHEN** the available Premium telemetry cannot justify the best supported precision for the active modality
- **THEN** the Premium location output SHALL indicate the degraded quality state instead of implying unchanged high-precision placement

### Requirement: Canonical latest-known state prefers the best supported current result across tiers
The RTLS Analytics Platform SHALL let a fresh, higher-quality Premium result supersede a lower-precision current location result for the same tracked asset in canonical latest-known state.

#### Scenario: Premium and Economic candidates overlap for one asset
- **WHEN** the system has both a current Economic-tier location result and a fresher, higher-quality Premium-tier result for the same tracked asset
- **THEN** the canonical latest-known asset location SHALL update to the Premium-tier result while preserving both results in durable history as supported

#### Scenario: Premium result is older or less trustworthy than the current canonical result
- **WHEN** a Premium-tier candidate is older than or lower quality than the canonical current result for the same tracked asset
- **THEN** the system SHALL NOT overwrite the canonical latest-known state with the weaker Premium-tier candidate
