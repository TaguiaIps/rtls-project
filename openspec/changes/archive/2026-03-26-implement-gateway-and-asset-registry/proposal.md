## Why

The RTLS Analytics Platform now has authentication and a spatial foundation, but it still lacks the managed gateway and asset/tag registry that later ingestion, calibration, live tracking, alerts, and analytics depend on. This change is needed now because the platform cannot responsibly accept telemetry or render meaningful tracked entities until gateways, hardware tiers, and asset profiles are first-class administrative records.

## What Changes

- Add an Administrator-managed gateway registry with floor placement, stable identifiers, labels, and editable configuration metadata.
- Add explicit Economic and Premium hardware tier profiles for gateways so later positioning and ingestion flows can branch from a shared registry.
- Add an Administrator-managed asset/tag registry with asset identity, category, update-rate policy, and battery profile metadata.
- Add CSV-based bulk import for asset tags with validation, duplicate detection, and explicit confirmation before records are created.
- Add protected backend and web admin workflows for gateway placement, tier assignment, asset registry editing, and CSV import review.
- Keep QR commissioning, calibration sessions, telemetry ingestion, gateway health monitoring, and live asset rendering out of scope for this change.

## Capabilities

### New Capabilities
- `gateway-placement-and-tier-profiles`: Covers gateway registration, floor placement, placement editing, and Economic or Premium tier profile assignment.
- `asset-tag-registry`: Covers asset/tag registry management, asset metadata policies, CSV import validation, and confirmed bulk creation workflows.

### Modified Capabilities
- None.

## Impact

- Affects backend data modeling, protected admin APIs, and shared contracts for gateways and asset tags.
- Affects the web Admin setup workspace by adding Gateway Placement, Tier Profiles, and Asset Registry flows.
- Establishes the canonical gateway and asset metadata model that later ingestion, calibration, live map, alert, and analytics changes will consume.
- Aligns the implementation backlog with Wave 1 of the implementation plan without prematurely pulling in telemetry or calibration behavior.
