## Why

The RTLS Analytics Platform can now ingest telemetry, derive live positions, and power the web monitoring baseline, but it still lacks the canonical business-event layer that turns movement into operational meaning. This change is needed now because later Alerts, Analytics, and Health work all depend on one shared source of truth for zone visits, dwell windows, round trips, and table-service timers instead of recomputing those semantics independently.

## What Changes

- Add a reusable derived-event foundation that turns accepted live-location updates into canonical zone-entry, zone-exit, and dwell records.
- Add round-trip measurement primitives that evaluate origin-destination-origin cycles from canonical zone events without forcing each downstream feature to reinterpret raw location history.
- Add table-service SLA timer primitives for SLA-eligible table areas so later alerting and analytics changes can consume one shared timer state.
- Add durable storage and backend-facing read contracts for downstream workflows that need derived-event history and current timer snapshots.
- Update architecture and workflow documentation so this backend event foundation is clearly separated from later Alerts Center, analytics UI, exports, and notification-delivery work.
- Keep alert rules management, notifications, report screens, exports and rollups, and premium-tier logic out of scope for this change.

## Capabilities

### New Capabilities

- `zone-transition-and-dwell-events`: Canonical zone-entry, zone-exit, and dwell semantics derived from accepted live-location updates.
- `round-trip-and-table-sla-primitives`: Reusable round-trip measurement and table-service timer state built on top of canonical derived zone events.

### Modified Capabilities

- None.

## Impact

- Affects backend models, services, and worker flow in `apps/api` where accepted live-location updates are already produced.
- Adds the reusable event and timer foundation that later alerting and analytics changes will consume, without requiring those changes to parse raw MQTT payloads or raw location history again.
- Requires documentation updates in `docs/` and new OpenSpec capability definitions so the boundary between derived-event primitives, later alerting, and later analytics stays explicit.
