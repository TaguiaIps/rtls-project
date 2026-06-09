## Why

The current mobile commissioning and calibration workflow is functional but feels tedious and lacks the "pleasure" and "meaning" layers of affective UX. Operators like Alex spend significant time walking floors to calibrate gateways; providing a more guided, satisfying, and gamified experience will reduce mental fatigue, increase accuracy, and make the task feel like an achievement rather than a chore.

## What Changes

- **Step-by-Step Progress Bar**: Implement a dynamic, industrial-style progress indicator for the Calibration Walk to set clear expectations.
- **Haptic Feedback Integration**: Use native mobile vibrations to confirm successful checkpoint captures, providing physical "pleasure" and reassurance.
- **Technical Completion Celebration**: Add a subtle, high-fidelity technical animation (e.g., a "Baseline Established" scanline effect) when a floor calibration is finished.
- **Micro-copy Refinement**: Replace generic status text with technical-authority labels (e.g., "Capturing signal density..." instead of "Saving...").

## Capabilities

### New Capabilities
- `mobile-affective-feedback`: Utility library for haptic patterns and technical animations specific to the mobile platform.

### Modified Capabilities
- `mobile-commissioning-and-calibration`: Update requirements to enforce step-by-step guidance and native haptic confirmation loops.

## Impact

- **Mobile App**: Refactor of the Calibration Wizard screen and integration of native haptic APIs.
- **User Experience**: Transformation of a repetitive task into a satisfying, gamified workflow.
- **System Trust**: Physical and visual confirmation of data capture increases the operator's confidence in the resulting radiomap.
