## 1. Contracts and backend surfaces

- [x] 1.1 Add shared contracts and backend schemas for audit-log records, observability summaries, and health risk cards.
- [x] 1.2 Implement backend admin APIs for audit-event querying, observability summary retrieval, metrics exposition, and request-id response headers.

## 2. Admin health and audit UI

- [x] 2.1 Refactor the web admin area into a small route-aware shell that preserves Spatial and adds Health and Audit views.
- [x] 2.2 Implement the Health workspace with summary cards, gateway-risk panels, and observability baseline details.
- [x] 2.3 Implement the Audit Log workspace with filter controls and recent-event results.

## 3. Verification and docs

- [x] 3.1 Add backend and web regression tests for the new health, audit, and observability behavior.
- [x] 3.2 Update system and UX documentation to describe the delivered Health and Audit admin baseline and the deferred external observability stack work.
- [x] 3.3 Validate the change with `uv run --project apps/api --active python -m pytest apps/api/tests/test_observability.py apps/api/tests/test_auth_flow.py apps/api/tests/test_ingestion.py`, `npm run test --workspace @rtls/web`, and `openspec validate implement-health-audit-ui-and-observability --strict`.
