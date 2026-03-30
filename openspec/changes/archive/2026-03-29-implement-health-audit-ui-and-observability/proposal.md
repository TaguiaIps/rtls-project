## Why

The repository already records audit events, projects gateway heartbeat health, and derives alert signals, but administrators still have no delivered screen for reviewing system health, investigating configuration changes, or confirming the current observability baseline. That leaves a major operational gap in the implementation plan even though the underlying data is already present.

This change is needed now because later export, retention, and lifecycle work depends on a trustworthy administrative operations surface. Without it, Alex still has to infer gateway outages and audit history from raw API responses or database inspection instead of using a supported Health and Audit experience inside the product.

## What Changes

- Add a protected administrator health and observability workspace in the web app alongside the delivered spatial admin workspace.
- Add a protected administrator audit-log workspace with filterable audit-event review.
- Add backend admin APIs for audit-event querying and observability summary retrieval.
- Add a minimal `/metrics` baseline and request-level observability metadata suitable for local development and operational verification.
- Add shared contracts, tests, and documentation updates for the delivered Health and Audit baseline.
- Keep full distributed tracing export pipelines, packet-loss analytics, and external dashboard provisioning out of scope for this change.

## Capabilities

### New Capabilities

- `health-audit-ui-and-observability`: Covers administrator health dashboards, audit-log review, and the delivered metrics or request-tracing baseline.

### Modified Capabilities

- None.

## Impact

- Affects FastAPI admin APIs, shared contracts, the protected web admin shell, and admin-focused tests.
- Reuses persisted audit events, gateway heartbeats, alerts, and ingestion tables rather than adding a separate monitoring datastore.
- Adds a local metrics endpoint and request observability baseline without introducing a full external observability vendor dependency.
