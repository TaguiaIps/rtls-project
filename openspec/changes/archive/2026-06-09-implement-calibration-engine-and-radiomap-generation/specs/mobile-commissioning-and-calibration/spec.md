## ADDED Requirements

### Requirement: Calibration session submission and backend handshake
The mobile commissioning workflow SHALL support the submission of completed calibration sessions to the backend and provide status updates on processing.

#### Scenario: Mobile app submits a calibration session
- **WHEN** the Administrator completes a calibration walk and submits the session to the backend
- **THEN** the app SHALL show a "Processing" status while the backend calibration engine generates the new radiomap and offsets

#### Scenario: Backend processing completes
- **WHEN** the backend calibration engine successfully processes a submitted session
- **THEN** the mobile app SHALL update the session summary to indicate that the calibration is "Active" on the floor
