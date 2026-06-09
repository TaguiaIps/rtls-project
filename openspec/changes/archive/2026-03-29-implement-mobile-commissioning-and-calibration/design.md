## Context

The repository already contains the admin spatial workflow, the gateway and asset registry, floor-detail retrieval, floor-plan download, and the initial mobile Asset Finder. The mobile app still has no commissioning workflow, no mobile admin context loader, and no delivered calibration capture flow, so this change needs to stay inside the mobile workspace while reusing the existing authorized admin APIs.

Constraints:

- dedicated mobile authentication UX is still deferred, so the mobile app still needs the existing manual session panel
- the current repository does not yet have a backend radiomap-processing service or a mobile-native indoor positioning stack
- the delivered backend can return sites, floors, areas, gateways, assets, and floor-plan files, but it does not yet expose a dedicated calibration-session API

Stakeholders:

- Alex needs to scan or enter device identifiers while moving through a restaurant or catering site and confirm the correct room or zone without walking back to the desktop admin console
- the rollout workflow needs a calibration assistant that can guide a floor walk and preserve a defensible session summary even before full automated radiomap processing lands

## Goals / Non-Goals

**Goals:**

- add a mobile commissioning mode without regressing the delivered Asset Finder
- load admin site and floor context from existing authorized APIs
- resolve scanned or entered gateway and asset identifiers against the delivered registries
- support zone assignment, floor preview, blue-dot calibration capture, and local session summaries
- keep the new workflow testable through pure helper modules for identifier resolution, waypoint generation, and session summaries

**Non-Goals:**

- dedicated mobile login or token refresh handling
- native camera-only scanning, BLE trilateration, GPS-to-floor transforms, or a production indoor positioning SDK
- automated radiomap generation, backend calibration persistence, or offset calculation services
- replacing the existing web admin workspace for full gateway editing or asset-registry management

## Decisions

### 1. The mobile app will become a two-mode workspace instead of replacing the delivered Asset Finder

The app already has a useful on-floor operator workflow, so the commissioning change should add an Administrator-focused mode switch rather than replace or bury Asset Finder. This keeps both delivered mobile capabilities reachable in one Expo baseline without introducing a router.

Alternative considered:
- adding a full mobile navigation library was rejected because the app still has only two delivered workflows and does not need deeper route architecture yet.

### 2. Commissioning will reuse existing admin endpoints and keep calibration state local to the device

The backend can already provide sites, floors, areas, gateways, assets, and floor-plan imagery. That is enough to support a meaningful commissioning assistant without inventing a partial calibration backend that would need new tables, APIs, and archival rules immediately.

Alternative considered:
- introducing a backend calibration-session service in this change was rejected because the current repository has no delivered processing pipeline behind it and the mobile workflow can still provide operational value with local session capture first.

### 3. Device intake will resolve QR payloads or scanner-entered identifiers against delivered gateway and asset registries

The workflow should treat the scanned value as a stable identifier and classify it as a known gateway, known asset tag, or unknown device. This supports QR-based commissioning while staying compatible with the current API surface and without assuming every operator device has a native camera scanner configured.

Alternative considered:
- requiring a camera-native scanner dependency now was rejected because the delivered workflow can already support connected scanners or pasted QR payloads, while native camera capture can land later without changing the session model.

### 4. Blue-dot calibration will use operator-tapped floor-plan checkpoints instead of claiming automatic indoor location

The repository does not yet include a mobile indoor-position engine. The honest baseline is a guided walk in which the operator taps their current floor-plan position as they move, and the app visualizes that captured point as the active blue dot while tracking route progress and summary metrics.

Alternative considered:
- mocking automatic blue-dot movement was rejected because it would imply location confidence the current product does not have.
- mapping GPS to floor-relative coordinates was rejected because the repository has no georeferencing model and indoor GPS would be misleading in restaurant environments.

### 5. Commissioning summaries should persist locally with AsyncStorage

Alex needs to preserve the last few commissioning or calibration sessions across app restarts. AsyncStorage is already available in the mobile workspace and is the smallest practical way to keep a local session history without adding more infrastructure.

Alternative considered:
- keeping session summaries only in memory was rejected because operators would lose the calibration recap if the app closed mid-rollout.

## Risks / Trade-offs

- [Risk] Manual token entry remains less polished than a real mobile sign-in flow. → Mitigation: keep the session panel explicit and document it as a bridge until the dedicated mobile-auth change lands.
- [Risk] Local-only calibration summaries do not yet feed backend radiomap processing. → Mitigation: make the summary explicit about being a capture baseline and preserve enough floor, zone, and sample metadata for later evolution.
- [Risk] Scanner-input intake is less seamless than camera-native scanning on some devices. → Mitigation: design the identifier intake around QR payloads and connected scanner keyboards so the workflow remains operational now.
- [Risk] Tapped blue-dot capture depends on operator discipline. → Mitigation: show waypoint progress, visible checkpoints, elapsed time, and sample counts so the workflow stays structured instead of ad hoc.

## Migration Plan

1. Extend the mobile workspace with commissioning helpers, local storage keys, and shared admin-fetch utilities.
2. Refactor the mobile app into a small two-mode shell that preserves Asset Finder and adds Commissioning.
3. Implement commissioning context loading, scanner-input device resolution, zone assignment, floor preview, and blue-dot calibration capture.
4. Add tests for device resolution, route generation, and session-summary behavior.
5. Update documentation, validate the change, sync specs, and archive it.

## Open Questions

- Should the later advanced calibration change ingest these local session summaries as seed input, or replace them with a fully server-backed calibration session model?
