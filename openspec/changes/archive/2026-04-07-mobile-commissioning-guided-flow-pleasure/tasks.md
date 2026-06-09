## 1. Affective Foundation

- [x] 1.1 Integrate `expo-haptics` and create a `HapticService` utility for standard patterns (Impact, Notification).
- [x] 1.2 Implement the `CalibrationStepIndicator` component with segmented industrial styling.
- [x] 1.3 Create the `IndustrialCompletionOverlay` component using `react-native-reanimated` for the scanline effect.

## 2. Guided Calibration Wizard

- [x] 2.1 Refactor `CalibrationWizardScreen` to include the segmented progress indicator at the top.
- [x] 2.2 Trigger `HapticService.impact()` on every successful checkpoint coordinate capture.
- [x] 2.3 Implement transition logic to show the completion animation and success haptics when the final checkpoint is saved.
- [x] 2.4 Update micro-copy across the calibration flow to use technical-authority terminology.

## 3. Polish & Verification

- [x] 3.1 Audit animation performance on physical mobile devices to ensure no frame drops.
- [x] 3.2 Verify that the progress bar correctly reflects the percentage of checkpoints captured.
- [x] 3.3 Update `docs/ux-design.md` to reflect the new Mobile Pleasurable Interaction standards.
