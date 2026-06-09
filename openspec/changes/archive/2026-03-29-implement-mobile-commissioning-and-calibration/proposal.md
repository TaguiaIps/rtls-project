## Why

Alex can already configure floors, zones, gateways, and assets in the web admin workspace, but the mobile app still cannot support the on-floor commissioning and calibration workflow described in the implementation plan. That leaves QR-driven setup and calibration walkthroughs stuck in desktop-only tooling even though the admin registry and floor detail APIs are already delivered.

This change is needed now because the mobile app should become useful for technical rollout work before the later observability and lifecycle changes. Without it, administrators still have to move between the web admin console and manual notes when they are scanning devices, confirming room context, and walking a calibration route on a live restaurant floor.

## What Changes

- Add a mobile commissioning workspace for authorized Administrator sessions alongside the delivered mobile Asset Finder workflow.
- Add device-intake, zone-assignment, and floor-context loading flows that reuse the delivered admin sites, floors, gateways, zones, and asset registry APIs.
- Add a guided calibration workflow with a tappable floor-plan preview, blue-dot capture, route progress, and a local session summary.
- Add mobile helper modules and storage for commissioning-session summaries and calibration progress.
- Add mobile tests and documentation updates for the delivered commissioning and calibration baseline.
- Keep dedicated mobile sign-in, native indoor positioning, radiomap generation, and automated backend calibration processing out of scope for this change.

## Capabilities

### New Capabilities

- `mobile-commissioning-and-calibration`: Covers authorized mobile commissioning intake, zone assignment, guided blue-dot calibration capture, and local session summaries for administrators.

### Modified Capabilities

- None.

## Impact

- Affects the Expo mobile app, its local storage patterns, and its session-aware use of existing admin APIs.
- Reuses existing admin sites, floor-detail, gateway, zone, and asset-registry endpoints rather than introducing new backend services.
- Adds mobile-specific documentation to clarify what is delivered now versus what remains deferred to later mobile-auth and advanced calibration processing changes.
