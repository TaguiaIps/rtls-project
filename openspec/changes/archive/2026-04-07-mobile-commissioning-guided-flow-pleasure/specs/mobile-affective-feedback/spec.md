## ADDED Requirements

### Requirement: Native Haptic Confirmation Loops
The mobile application SHALL provide native haptic feedback for critical capture and completion events in the commissioning workflow.

#### Scenario: Operator captures a calibration point
- **WHEN** the operator successfully records a signal sample at a designated checkpoint
- **THEN** the mobile app SHALL trigger a medium-impact haptic vibration to provide tactile confirmation

### Requirement: Technical Calibration Completion Animation
The mobile application SHALL render a high-fidelity technical animation when a floor calibration workflow is successfully completed.

#### Scenario: Floor calibration finishes
- **WHEN** the operator completes all required checkpoints for a floor
- **THEN** the mobile app SHALL render a "Scanning Scanline" or similar industrial animation to visually communicate that the baseline is being established
