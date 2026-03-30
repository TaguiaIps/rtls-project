# RTLS API

Bootstrap FastAPI service for the RTLS Analytics Platform.

This package provides:

- the initial API application
- the worker entrypoint used by the local Compose stack
- the identity, RBAC, and audit foundation for the first protected web flows
- the inline derived-event foundation for canonical zone transitions, dwell history, round-trip evaluation, and table timer snapshots
- authenticated backend-facing read endpoints under `/api/derived/*` for downstream event-history and timer queries
- protected `/api/analytics/*` report endpoints for trajectory replay, heatmaps, dwell reports, round-trip reports, and table SLA trends
- premium gateway profile metadata, `rtls/premium/{gateway_id}` ingestion, normalized AoA or UWB measurement persistence, and Premium-aware canonical live-location outputs
- typed alert rule management plus protected `/api/alerts/*` contracts for queue, detail, acknowledgement, resolution, and shell summary workflows
- durable in-app notification records and optional email-delivery attempt tracking for delivered table-SLA and unauthorized-geofence alerts
- inline alert evaluation that reuses the derived-event and table-timer foundation instead of reparsing raw telemetry
- async `/api/analytics/exports*` workflows that generate durable CSV artifacts for supported report scopes
- administrator-triggered lifecycle runs that apply retention windows and refresh hourly heatmap and SLA rollups
- an explicit scope boundary where scheduled delivery, richer report presets, vendor-specific Premium provisioning, and maintenance alerts remain deferred to later changes
- the backend lint, test, and build baseline for future OpenSpec changes

Bootstrap the first Administrator account with:

```bash
python -m rtls_api.bootstrap_admin --email admin@example.com --password StrongPass123 --display-name "Platform Admin"
```
