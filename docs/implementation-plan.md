# Implementation Plan

This document captures the recommended phased implementation plan for the RTLS Analytics Platform and the proposed segmentation into future OpenSpec changes.

It is intended as a planning artifact only. It does not create any OpenSpec changes by itself.

## Planning Rules

- Start with one repo/bootstrap change before any feature change. Right now there is no implementation baseline.
- Keep each change responsible for one bounded concern: auth, spatial model, asset registry, ingestion, positioning, alerts, analytics, mobile, or observability.
- Build shared backend primitives once, then reuse them. The key shared primitive is a derived event layer for zone entry/exit, dwell, round-trip, and SLA timers.
- Do not open too many active changes at once. Before the live platform exists, keep 1 active change at a time; after core services exist, at most 2 parallel changes.
- Treat performance, security, reliability, and UX consistency as acceptance gates inside changes, not as one giant later cleanup.

## Recommended Change Backlog

### 1. `bootstrap-implementation-workspace`

Establish repo structure, backend/web/mobile skeletons, shared contracts package, local Docker Compose stack, lint/test/format tooling, CI baseline, and environment conventions.

- Depends on: none
- Maps to: enabling change only

### 2. `implement-identity-rbac-and-audit-foundation`

Implement user model, JWT auth, refresh flow, role guards, login shell, and audit actor context.

- Depends on: `bootstrap-implementation-workspace`
- Maps to:
  - `FR-SEC-001`
  - `FR-SEC-002`
  - groundwork for `FR-SEC-003`

### 3. `implement-sites-floorplans-and-zone-editor`

Implement site/floor hierarchy, floor plan upload, real-world scale setup, zone/POI/table model, and drawing/editing APIs and admin UI.

Initial scope should start with raster floor-plan upload and editing workflows. CAD/PDF parsing should be treated as a later extension after the floor, scale, and zone data model is stable.

- Depends on:
  - `bootstrap-implementation-workspace`
  - ideally `implement-identity-rbac-and-audit-foundation`
- Maps to:
  - `FR-ADM-001`
  - `FR-ANL-001`
  - `FR-VIS-001`
  - `NFR-USA-001`

### 4. `implement-gateway-and-asset-registry`

Implement gateway CRUD, gateway placement on mapped floors, tier profile metadata, asset/tag registry, and CSV import.

- Depends on:
  - `implement-sites-floorplans-and-zone-editor`
- Maps to:
  - `FR-ADM-002`
  - metadata side of `FR-ADM-004`
  - `FR-ADM-005`

### 5. `implement-ingestion-pipeline-and-raw-readings`

Implement MQTT broker integration, payload validation, dedupe, raw readings persistence, heartbeat ingestion, and gateway health feed.

- Depends on:
  - `bootstrap-implementation-workspace`
  - `implement-gateway-and-asset-registry`
- Maps to:
  - `NFR-SEC-001`
  - partial `NFR-REL-001`
  - partial `NFR-PER-001`
  - partial `NFR-PER-002`

### 6. `implement-economic-tier-positioning-and-live-location`

Implement the BLE fingerprinting path, location history, confidence scoring, WebSocket updates, and live-search APIs.

- Depends on:
  - `implement-ingestion-pipeline-and-raw-readings`
  - `implement-sites-floorplans-and-zone-editor`
  - `implement-gateway-and-asset-registry`
- Maps to:
  - `FR-VIS-002`
  - `FR-VIS-003`
  - backend basis for `FR-VIS-004`
  - backend basis for `FR-ANL-005`

### 7. `deliver-web-shell-operations-overview-and-live-map`

Implement the React shell, role-aware routing, Operations Overview, Live Map workspace, search/filter UI, asset drawer, and confidence visualization.

Delivered baseline note:

- The implemented Overview is intentionally driven by currently available live-location and gateway-health signals.
- Full Alerts Center behavior, SLA trend cards, and analytics workspaces remain deferred to later backlog items even though the shell now provides the navigation and layout foundation they will plug into.

- Depends on:
  - `implement-identity-rbac-and-audit-foundation`
  - `implement-sites-floorplans-and-zone-editor`
  - `implement-gateway-and-asset-registry`
  - `implement-economic-tier-positioning-and-live-location`
- Maps to:
  - `US-GEN-01`
  - `US-GEN-02`
  - `US-GEN-03`
  - `FR-VIS-001`
  - `FR-VIS-004`

### 8. `implement-derived-events-dwell-roundtrip-and-sla-primitives`

Implement the reusable event engine for zone entry/exit, dwell accumulation, round-trip measurement, and table SLA timers.

- Depends on:
  - `implement-sites-floorplans-and-zone-editor`
  - `implement-gateway-and-asset-registry`
  - `implement-economic-tier-positioning-and-live-location`
- Maps to foundation for:
  - `FR-ANL-003`
  - `FR-ANL-004`
  - `FR-ANL-006`
  - `FR-NOT-001`
  - `FR-NOT-002`

### 9. `implement-alert-rules-and-alerts-center`

Implement rules configuration, alert generation, persistence, in-app notifications, optional email integration, and Alerts Center UI.

- Depends on:
  - `implement-identity-rbac-and-audit-foundation`
  - `deliver-web-shell-operations-overview-and-live-map`
  - `implement-derived-events-dwell-roundtrip-and-sla-primitives`
- Maps to:
  - `FR-NOT-001`
  - `FR-NOT-002`
  - `FR-NOT-003`

### 10. `implement-analytics-workspace-and-reports`

Implement trajectory replay, heatmaps, dwell reports, round-trip reports, and SLA trend views.

- Depends on:
  - `deliver-web-shell-operations-overview-and-live-map`
  - `implement-derived-events-dwell-roundtrip-and-sla-primitives`
- Maps to:
  - `FR-ANL-002`
  - `FR-ANL-003`
  - `FR-ANL-004`
  - `FR-ANL-005`
  - `FR-ANL-006`

### 11. `add-premium-tier-aoa-uwb-support`

Extend gateway profiles, telemetry contracts, positioning pipeline, and confidence semantics for premium tier hardware.

- Depends on:
  - `implement-gateway-and-asset-registry`
  - `implement-ingestion-pipeline-and-raw-readings`
  - `implement-economic-tier-positioning-and-live-location`
- Maps to:
  - execution side of `FR-ADM-004`
  - `NFR-PER-001`
  - `NFR-PER-002`

### 12. `implement-mobile-asset-finder`

Implement mobile search, recent searches, asset location sheet, and open-in-map handoff.

- Depends on:
  - `implement-economic-tier-positioning-and-live-location`
  - `deliver-web-shell-operations-overview-and-live-map`
- Maps to:
  - `US-MOB-01`

### 13. `implement-mobile-commissioning-and-calibration`

Implement QR scanner, assign zone/room flow, guided calibration mode, blue-dot calibration workflow, and session summary.

- Depends on:
  - `implement-sites-floorplans-and-zone-editor`
  - `implement-gateway-and-asset-registry`
  - `implement-ingestion-pipeline-and-raw-readings`
  - `implement-economic-tier-positioning-and-live-location`
- Maps to:
  - `FR-ADM-003`
  - `US-MOB-02`
  - `NFR-USA-002`

### 14. `implement-health-audit-ui-and-observability`

Implement infrastructure health dashboard, gateway offline/battery alerts, audit log UI, metrics/tracing baseline, and operational dashboards.

- Depends on:
  - `implement-identity-rbac-and-audit-foundation`
  - `implement-ingestion-pipeline-and-raw-readings`
  - `implement-economic-tier-positioning-and-live-location`
  - `implement-alert-rules-and-alerts-center`
- Maps to:
  - `FR-SEC-003`
  - `NFR-REL-001`
  - `NFR-REL-002`
  - observability parts of the technical spec

### 15. `implement-exports-retention-and-rollups`

Implement async exports, retention policies, rollup tables, and report acceleration jobs.

- Depends on:
  - `implement-ingestion-pipeline-and-raw-readings`
  - `implement-derived-events-dwell-roundtrip-and-sla-primitives`
  - `implement-analytics-workspace-and-reports`
  - `implement-health-audit-ui-and-observability`
- Maps to:
  - `NFR-PER-003`
  - data lifecycle items from the system design

## Why This Split Avoids Rework

- Spatial ownership lives in change 3 only. Later changes consume sites/floors/zones instead of redefining them.
- Floor-plan ingestion should stabilize image upload, scale calibration, and polygon editing before adding CAD/PDF parsing complexity.
- Gateway and asset ownership live in change 4 only. Positioning, alerts, analytics, and mobile all reuse that registry.
- Raw telemetry ingestion lives in change 5 only. No later change should parse MQTT payloads again.
- Derived operational meaning lives in change 8 only. Alerts and analytics both consume the same event layer instead of recomputing dwell, SLA, or round-trip separately.
- Web shell and map UX live in change 7 only. Alerts and analytics should plug into that shell, not rebuild navigation or token usage.
- Premium tier support is isolated in change 11 so the project can ship an Economic Tier baseline first without blocking the whole roadmap.

## Recommended Waves

### Wave 1

- `bootstrap-implementation-workspace`
- `implement-identity-rbac-and-audit-foundation`
- `implement-sites-floorplans-and-zone-editor`
- `implement-gateway-and-asset-registry`

This creates a real implementation baseline and stable admin/domain contracts.

### Wave 2

- `implement-ingestion-pipeline-and-raw-readings`
- `implement-economic-tier-positioning-and-live-location`
- `deliver-web-shell-operations-overview-and-live-map`

This gets live tracking working end to end.

### Wave 3

- `implement-derived-events-dwell-roundtrip-and-sla-primitives`
- `implement-alert-rules-and-alerts-center`
- `implement-analytics-workspace-and-reports`

This adds the operational intelligence layer.

### Wave 4

- `add-premium-tier-aoa-uwb-support`
- `implement-mobile-asset-finder`
- `implement-mobile-commissioning-and-calibration`
- `implement-health-audit-ui-and-observability`
- `implement-exports-retention-and-rollups`

This adds premium precision, mobile flows, observability, and lifecycle hardening.

## Recommended OpenSpec Creation Order

Create only the first change initially:

1. `bootstrap-implementation-workspace`

After that is approved, create:

2. `implement-identity-rbac-and-audit-foundation`
3. `implement-sites-floorplans-and-zone-editor`

Do not create all 15 changes at once unless you intentionally want a large backlog tree. It is more manageable to create the next change only after the current foundation is settled.
