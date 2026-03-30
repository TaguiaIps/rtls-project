## Why

The delivered mobile commissioning baseline still relies on pasted or externally scanned identifiers, which leaves `US-ADM-03` short of a true on-device QR workflow. Native camera scanning is a small follow-on change that removes avoidable manual entry friction without waiting for the larger calibration-engine backlog.

## What Changes

- Add native camera-based QR scanning to the Expo mobile commissioning workflow.
- Preserve manual and external-scanner identifier entry as fallback for simulators and constrained-device workflows.
- Normalize supported QR payload shapes before resolving gateway or asset identifiers against the delivered registry.
- Update mobile commissioning docs and backlog planning to reflect camera scanning as delivered behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mobile-commissioning-and-calibration`: extend device-intake requirements so the mobile app supports native camera QR scanning while retaining manual fallback behavior.

## Impact

- Affected code:
  - `apps/mobile` commissioning UI, helpers, tests, and Expo app configuration
  - planning and UX docs describing commissioning behavior
- Dependencies:
  - adds `expo-camera` to the mobile workspace
- Systems:
  - mobile app permissions and native camera access
