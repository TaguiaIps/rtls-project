## 1. Mobile commissioning foundations

- [x] 1.1 Add the mobile helper modules needed for admin context loading, device resolution, calibration route generation, and local session summaries.
- [x] 1.2 Extend mobile local storage to preserve recent commissioning and calibration session summaries.

## 2. Commissioning workflow

- [x] 2.1 Refactor the Expo app into a small two-mode shell that preserves Asset Finder and adds a Commissioning mode.
- [x] 2.2 Implement commissioning context loading, scanner-input device resolution, and zone assignment for the selected floor.
- [x] 2.3 Implement the floor-linked blue-dot calibration walkthrough, captured-progress summary, and recent commissioning history.

## 3. Verification and docs

- [x] 3.1 Add mobile tests for device resolution, calibration-route generation, and commissioning-summary behavior.
- [x] 3.2 Update system and UX documentation to describe the delivered mobile commissioning baseline and the deferred native-auth or advanced calibration processing work.
- [x] 3.3 Validate the change with `openspec validate implement-mobile-commissioning-and-calibration --strict`, `npm run test --workspace @rtls/mobile`, and `npm run build --workspace @rtls/mobile`.
