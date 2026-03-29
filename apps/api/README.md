# RTLS API

Bootstrap FastAPI service for the RTLS Analytics Platform.

This package provides:

- the initial API application
- the worker entrypoint used by the local Compose stack
- the identity, RBAC, and audit foundation for the first protected web flows
- the inline derived-event foundation for canonical zone transitions, dwell history, round-trip evaluation, and table timer snapshots
- authenticated backend-facing read endpoints under `/api/derived/*` for downstream event-history and timer queries
- typed alert rule management plus protected `/api/alerts/*` contracts for queue, detail, acknowledgement, resolution, and shell summary workflows
- durable in-app notification records and optional email-delivery attempt tracking for delivered table-SLA and unauthorized-geofence alerts
- inline alert evaluation that reuses the derived-event and table-timer foundation instead of reparsing raw telemetry
- an explicit scope boundary where maintenance alerts remain deferred to the later health and observability change
- the backend lint, test, and build baseline for future OpenSpec changes

Bootstrap the first Administrator account with:

```bash
python -m rtls_api.bootstrap_admin --email admin@example.com --password StrongPass123 --display-name "Platform Admin"
```
