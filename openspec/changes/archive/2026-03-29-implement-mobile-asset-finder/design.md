## Context

The repository already has the backend live-location APIs, trajectory history surface, and a delivered web Live Map route. The mobile app at `apps/mobile` is still only a baseline Expo screen, so this change can stay entirely within the mobile workspace as long as it consumes the existing authorized APIs and web handoff route.

Constraints:

- dedicated mobile authentication UX is still deferred, but the backend search and live-location APIs are authorized
- the current mobile baseline has no navigation library, native map SDK, or storage dependency beyond Expo defaults
- the handoff target should use the delivered web route and query-param semantics instead of inventing a separate mobile-only deep link contract

Stakeholders:

- Carlos Mendes needs fast one-handed search and orientation while moving through a restaurant or catering site
- Alex still needs the mobile app preserved as an Expo baseline for later commissioning and calibration work

## Goals / Non-Goals

**Goals:**

- turn the Expo baseline into a working mobile Asset Finder
- support search, recent searches, selected-asset details, and open-in-map handoff
- reuse the existing live-location contracts and web Live Map route
- keep the code testable with pure helpers for search history and handoff URL generation
- avoid blocking on the later mobile auth and commissioning changes

**Non-Goals:**

- QR scanning, infrastructure commissioning, or calibration workflows
- a native indoor map renderer inside the mobile app
- offline-first sync, push notifications, or background location polling
- replacing the delivered web Live Map experience

## Decisions

### 1. The first mobile delivery will be a single-screen search workflow instead of full mobile navigation

The current app baseline has no router and does not need one for this backlog item. A single-screen Asset Finder keeps the implementation narrow and matches the UX requirement: search, identify, orient, move.

Alternative considered:
- introducing mobile navigation now was rejected because it adds architectural weight before the app has more than one delivered workflow.

### 2. The app will use manual access-token session entry until the later mobile auth change lands

The backend endpoints are protected today, but the repository does not yet include a delivered mobile auth UX. The least risky bridge is a small session panel where the operator pastes a current access token and API base URL if needed.

Alternative considered:
- making live-location endpoints anonymous was rejected because it would weaken the delivered authorization boundary.
- building the full mobile auth flow inside this change was rejected because it exceeds the implementation-plan scope for the Asset Finder item.

### 3. Recent searches should persist locally with AsyncStorage

Recent searches are core to the requested workflow and should survive app restarts. AsyncStorage is the smallest practical addition for that requirement and does not constrain the later commissioning flows.

Alternative considered:
- keeping recent searches only in memory was rejected because it would fail the “recent searches” part of the backlog in day-to-day usage.

### 4. Open-in-map handoff should target the delivered web Live Map route with query params

The web shell already supports `/operations/live-map` with `site_id`, `floor_id`, and `asset_tag_id`. The mobile app should generate a handoff URL against that route and launch it with the platform browser instead of creating a new backend or navigation contract.

Alternative considered:
- adding a new mobile-specific deep link endpoint was rejected because it duplicates an already delivered route surface.

## Risks / Trade-offs

- [Risk] Manual token entry is less polished than a real mobile sign-in flow. → Mitigation: keep the session panel explicit in the UI and document it as a bridge until the later auth-focused mobile change.
- [Risk] AsyncStorage adds one more mobile dependency. → Mitigation: confine it to recent-search persistence and keep the storage shape simple.
- [Risk] Web handoff may still require login in the browser. → Mitigation: preserve asset, site, and floor context in the generated URL so the handoff remains useful once the operator is signed in on the web side.

## Migration Plan

1. Add mobile workspace dependencies needed for shared contracts and local recent-search persistence.
2. Implement the Asset Finder screen and pure helper modules.
3. Wire the screen to the existing `/api/locations/search` and `/api/locations/live` surfaces.
4. Add tests for recent-search ordering, handoff URL generation, and session-aware search behavior.
5. Update docs and mark the OpenSpec tasks complete.

## Open Questions

- Should the later dedicated mobile auth change preserve the manual token entry panel as a diagnostic fallback, or remove it entirely?
