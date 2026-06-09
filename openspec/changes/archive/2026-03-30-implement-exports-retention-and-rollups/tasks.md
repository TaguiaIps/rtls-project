## 1. Export and lifecycle foundations

- [x] 1.1 Add shared contracts, backend schemas, and database models for export jobs, lifecycle runs, and supported rollup records.
- [x] 1.2 Add export artifact generation and object-storage helpers for CSV analytics exports.

## 2. Backend APIs and jobs

- [x] 2.1 Implement analytics export creation, listing, detail, and file-download endpoints with async job processing.
- [x] 2.2 Implement administrator lifecycle status and manual-run endpoints with retention and rollup refresh execution.
- [x] 2.3 Update compatible analytics queries to prefer refreshed rollups when available.

## 3. Web workflows

- [x] 3.1 Extend the Analytics workspace with export actions and a recent export queue.
- [x] 3.2 Extend the administrator Health workspace with lifecycle status and a manual run action.

## 4. Verification and docs

- [x] 4.1 Add backend and web regression tests for exports, lifecycle runs, retention behavior, and rollup-backed analytics queries.
- [x] 4.2 Update system, UX, and backend documentation to describe the delivered export, retention, and rollup baseline.
- [x] 4.3 Validate the change with `uv run --project apps/api --active python -m ruff check apps/api`, `uv run --project apps/api --active python -m pytest apps/api/tests/test_analytics.py apps/api/tests/test_observability.py`, `npm run test --workspace @rtls/web`, and `openspec validate implement-exports-retention-and-rollups --strict`.
