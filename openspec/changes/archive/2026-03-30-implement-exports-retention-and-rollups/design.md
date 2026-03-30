## Context

The repository already delivers authenticated analytics queries, object storage for floor plans, and an administrator Health workspace. What is still missing is the lifecycle layer that turns those foundations into operationally safe historical reporting: Carlos cannot request a durable export artifact from Analytics, and Alex cannot run or inspect a supported retention or rollup refresh job.

The current codebase also lacks a dedicated background-job service. The design therefore needs to provide async exports, retention execution, and report acceleration without introducing infrastructure the repository does not yet operate.

## Goals / Non-Goals

**Goals:**

- Provide authenticated async CSV export jobs for delivered analytics report types.
- Persist export job status, artifact metadata, ownership, and expiry windows.
- Add administrator-visible lifecycle run status plus a supported manual trigger from Health.
- Apply explicit retention policies for raw telemetry, historical location data, and export artifacts.
- Materialize hourly rollups that accelerate at least the delivered heatmap and hourly SLA trend paths.
- Keep the rollout compatible with the existing FastAPI app, object storage abstraction, and shared web shell.

**Non-Goals:**

- Adding PDF, Excel, ZIP bundles, scheduled email delivery, or cross-tenant share links.
- Introducing Celery, Temporal, or a separate queue or scheduler service.
- Reworking every analytics endpoint to depend exclusively on rollups.
- Implementing long-horizon warehouse exports or external BI connectors.

## Decisions

### 1. Use durable job records plus FastAPI background tasks for the first async export baseline

The codebase does not yet run a generalized job queue, so export requests will create an `ExportJob` row and then schedule generation with FastAPI `BackgroundTasks`. This keeps the API contract asynchronous for the client while reusing the existing process model.

Alternatives considered:

- Add Celery or another worker queue now: rejected because the repository does not yet contain queue orchestration or deployment support for that stack.
- Keep exports synchronous: rejected because larger report artifacts would block user requests and would not satisfy the async export requirement.

### 2. Generate CSV artifacts only in this rollout

CSV aligns with the current report data model, is easy to verify in tests, and reuses object storage without extra rendering dependencies. Each export job stores one artifact with a stable download path until expiry.

Alternatives considered:

- Add multiple formats immediately: rejected because it would expand serialization and testing scope without improving the first operational baseline enough.

### 3. Add one lifecycle run record that combines retention and rollup refresh

Alex needs one supported action in Health, not multiple partial maintenance knobs. A `DataLifecycleRun` record will capture requested-at, started-at, completed-at, purged counts, refreshed rollup counts, and failure state for one combined maintenance run.

Alternatives considered:

- Separate retention and rollup job types: rejected because the first UI would become more complex and the current deployment strategy already treats them as one maintenance concern.

### 4. Materialize hourly rollups for heatmap density and hourly SLA trend buckets

The current analytics workspace already exposes heatmaps and SLA trends, and those paths benefit from precomputed hourly aggregates without changing user-visible query semantics. The lifecycle run will rebuild rollups inside bounded historical windows and analytics queries will prefer them when the request shape is compatible.

Alternatives considered:

- Roll up every report type now: rejected because round-trip and arbitrary dwell exports would add more complexity than the current scope requires.
- Use database-native materialized views only: rejected because the repository currently relies on portable SQLAlchemy tables and local SQLite-backed tests.

### 5. Apply explicit retention windows in application logic

The system design calls for 30 to 90 day retention windows, but the repository does not yet provision database-native lifecycle policies in code. This change will enforce the baseline in the lifecycle runner with configurable settings:

- raw readings: 90 days
- premium raw measurements: 90 days
- asset location history: 30 days
- export artifacts and job rows: 7 days

Derived dwell history, round-trip primitives, and rollup tables remain retained so Analytics can keep serving the current report set after short-horizon raw data ages out.

Alternatives considered:

- Delete derived history as aggressively as raw telemetry: rejected because it would undercut the current analytics workspace immediately.

## Risks / Trade-offs

- [Risk] Background tasks run in-process and are not a substitute for a dedicated queue. → Mitigation: keep jobs bounded, persist status transitions, and document that the design is a first operational baseline.
- [Risk] Rollups can drift from source data if lifecycle refresh is not run. → Mitigation: expose lifecycle status in Health and keep analytics queries capable of falling back to source tables when needed.
- [Risk] Retention policies may remove data users expected to export later. → Mitigation: document the windows clearly and retain derived report primitives longer than raw telemetry.
- [Risk] Export artifacts can accumulate in object storage. → Mitigation: apply export artifact expiry and delete old files during lifecycle runs.

## Migration Plan

1. Add export-job, lifecycle-run, and rollup tables through the existing metadata-managed schema creation path.
2. Deploy the API changes so new routes and background processors exist before the UI starts requesting exports or lifecycle runs.
3. Run one lifecycle refresh in each environment to populate the first rollups and establish status metadata for Health.
4. Roll back by disabling new UI actions; existing report endpoints continue to function directly from source tables if rollups are empty.

## Open Questions

- Should the future dedicated worker process own lifecycle scheduling once the deployment strategy introduces long-running maintenance queues? For this change, the answer remains “not yet”.
