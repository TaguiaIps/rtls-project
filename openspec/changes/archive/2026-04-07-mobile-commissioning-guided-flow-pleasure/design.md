## Context

The current Mobile Calibration workflow in `apps/mobile/src` relies on a simple list of checkpoints. While it records the necessary data, it lacks the interactive polish required to guide the operator effectively through a physical environment. There is no tactile feedback when a sample is recorded, and the transition between "Calibrating" and "Finished" is abrupt.

## Goals / Non-Goals

**Goals:**
- Implement physical feedback loops using `expo-haptics`.
- Create a visual narrative of progress through an industrial step-indicator.
- Standardize technical animations for "Capture" and "Completion" states.
- Refine micro-copy to reinforce the professional nature of the tool.

**Non-Goals:**
- Changing the calibration algorithm or backend persistence.
- Redesigning the QR scanning logic (already handled by a previous change).

## Decisions

- **Haptic Patterns**: Use `Haptics.ImpactFeedbackStyle.Medium` for standard checkpoint captures and `Haptics.NotificationFeedbackType.Success` for flow completion.
  - *Rationale*: Physical confirmation reduces the need for the operator to look at the screen constantly while walking.
- **Progress Narrative**: Implement a `CalibrationStepIndicator` that uses "Segmented Progress" (fixed steps) rather than a continuous bar.
  - *Rationale*: Matches the discrete nature of calibration checkpoints and provides better "Chunking" for the user.
- **Technical Animations**: Use `react-native-reanimated` for a "Scanning Scanline" effect on completion.
  - *Rationale*: Provides a "Meaning" layer by visually representing the creation of the positioning baseline.

## Risks / Trade-offs

- **[Risk]** Excessive battery drain from complex animations.
  - **Mitigation**: Ensure animations are simple, SVG-based, and only run during active capture or completion events.
- **[Risk]** Haptic distraction in noisy/vibrating environments.
  - **Mitigation**: Haptics are a secondary cue; visual feedback must remains clear and primary.
