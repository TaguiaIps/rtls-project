# implement-economic-tier-positioning-and-live-location Proposal

## Why

The platform now ingests gateway telemetry and persists raw readings, but operators still have no durable location output to power live tracking, search, or trajectory workflows. The next backlog item needs to convert accepted economic-tier BLE telemetry into a usable position stream so later web, analytics, alerts, and mobile changes can build on one shared location foundation.

This change is needed to complete the backend portion of the live-location baseline described in the implementation plan. Without it, the system can store telemetry but cannot answer the core operational question of where a tracked asset is now or where it moved over time.

## What Changes

This proposal introduces a backend-first economic-tier positioning baseline that consumes persisted raw readings and publishes durable location results for tracked assets on mapped floors.

The change adds:

- An economic-tier position estimation capability that derives current asset location and append-only location history from accepted BLE readings.
- Confidence and fallback semantics so the platform can distinguish point-level positions from lower-confidence zone-level results.
- Authorized live-location query APIs for latest positions, asset search, and historical trajectory retrieval.
- Authorized live update streaming for downstream operational clients that need new position events as they are produced.
- Shared contracts and documentation updates that define the position output surface future web and mobile features will consume.

This change does not include premium-tier AoA/UWB positioning, alert generation, analytics reports, or the later mobile commissioning/calibration UX. It assumes the economic-tier positioning flow can rely on backend-managed reference data and mapped floor metadata without introducing the guided calibration experience planned in a later backlog item.

## Capabilities

### New Capabilities

- `economic-tier-position-estimation`
- `live-location-query-and-streaming`

### Modified Capabilities

- None.

## Impact

- A new positioning stage will be added on top of the existing ingestion and raw-reading baseline.
- The backend data model will need durable current-location and location-history records that downstream workflows can query.
- Web and mobile clients will gain a documented live-location contract without taking on UI implementation in this change.
- Operational and architecture docs will need to distinguish the delivered economic-tier baseline from later premium-tier and mobile-calibration work.
