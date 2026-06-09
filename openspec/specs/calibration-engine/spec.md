# calibration-engine Specification

## Purpose
Consume mobile calibration session data to generate normalized radiomap and gateway offset artifacts that improve positioning accuracy across the deployment.
## Requirements
### Requirement: Calibration session processing pipeline
The RTLS Analytics Platform SHALL provide a backend processing pipeline that consumes mobile calibration session data and generates normalized positioning artifacts.

#### Scenario: Valid calibration session is submitted for processing
- **WHEN** the system receives a completed mobile calibration session with valid floor context, checkpoint data, and gateway/tag readings
- **THEN** the calibration engine SHALL initiate an asynchronous processing task to generate a new radiomap and gateway offsets

#### Scenario: Calibration session data is malformed or incomplete
- **WHEN** a submitted calibration session is missing required checkpoint data or signal samples
- **THEN** the engine SHALL reject the session and log a detailed validation error for the Administrator

### Requirement: Radiomap and gateway offset generation
The calibration engine SHALL perform geometric and signal-strength analysis to produce environmental radiomaps and per-gateway coordinate/signal offsets.

#### Scenario: Processing task completes successfully
- **WHEN** the calibration processing task finishes its calculations for a specific floor and gateway set
- **THEN** the system SHALL generate a new versioned radiomap artifact and update the gateway registry with calculated offsets

#### Scenario: Processing task fails due to inconsistent data
- **WHEN** the calibration engine detects physical inconsistencies or insufficient signal coverage during processing
- **THEN** the system SHALL mark the session as failed and notify the Administrator (Alex) to recalibrate specific areas

