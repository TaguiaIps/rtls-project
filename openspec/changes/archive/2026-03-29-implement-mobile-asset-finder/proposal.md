## Why

Carlos can already search and inspect live asset locations in the web shell, but the mobile app is still only a placeholder panel. That leaves the mobile backlog item from the implementation plan unresolved even though the live-location backend and web handoff dependencies are already delivered.

This change is needed now because the mobile baseline should become a practical asset-finding tool before broader commissioning work begins. Without it, operations staff still have to fall back to the desktop shell when they need to find a missing tray cart, POS terminal, or Waiter Tag while moving through a site.

## What Changes

- Add a search-first mobile Asset Finder screen in the Expo app for authorized mobile sessions.
- Add mobile search results, a recent-search list, and a selected-asset location sheet that reuse the delivered live-location contracts.
- Add an open-in-map handoff that launches the delivered web Live Map route with site, floor, and asset context.
- Add mobile-side session handling appropriate to the current repository phase so the app can call the authorized API without waiting for the later dedicated mobile auth flow.
- Add mobile tests and documentation updates for the delivered Asset Finder baseline.
- Keep QR commissioning, mobile calibration, push notifications, native map SDKs, and offline caching out of scope for this change.

## Capabilities

### New Capabilities

- `mobile-asset-finder`: Covers mobile asset search, recent searches, selected-asset location details, and open-in-map handoff into the delivered web Live Map.

### Modified Capabilities

- None.

## Impact

- Affects the Expo mobile app, its workspace dependencies, and its local state patterns for recent searches and session input.
- Reuses the existing live-location query and search APIs rather than introducing new backend endpoints.
- Adds mobile-specific documentation to clarify what is delivered now versus what remains deferred to later mobile-auth and commissioning changes.
