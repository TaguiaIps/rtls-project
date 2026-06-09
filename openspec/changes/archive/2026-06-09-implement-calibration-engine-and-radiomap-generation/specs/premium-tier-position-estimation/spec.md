## MODIFIED Requirements

### Requirement: Premium-tier positioning depends on valid Premium gateway geometry and calibration state
The RTLS Analytics Platform SHALL use Premium gateway geometry and current calibration artifacts (radiomaps and offsets) when deriving Premium-tier location outputs.

#### Scenario: Premium gateway geometry and calibration artifacts are valid
- **WHEN** the estimator receives accepted Premium measurements from gateways whose required placement geometry and active calibration artifacts (radiomap and offsets) are valid for the current floor context
- **THEN** the system SHALL use that Premium placement and calibration context during location estimation

#### Scenario: Premium gateway calibration artifact is stale or missing
- **WHEN** Premium telemetry arrives for a floor whose required active radiomap or gateway offset artifact is stale, missing, or invalid
- **THEN** the system SHALL reject or degrade Premium estimation according to supported confidence rules instead of implying unchanged high-precision positioning
