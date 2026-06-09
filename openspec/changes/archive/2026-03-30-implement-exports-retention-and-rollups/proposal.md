## Why

The RTLS Analytics Platform now has interactive analytics, but Carlos still cannot request durable exports and Alex still lacks a supported lifecycle job for retention and rollup refresh. This change is needed now because the existing report surfaces will become slower and less compliant over time without a first-class export queue, explicit retention windows, and reusable acceleration data.

## What Changes

- Add async analytics export jobs that generate CSV artifacts in object storage and expose status, history, and download endpoints.
- Add lifecycle job records plus administrator-triggered retention and rollup refresh endpoints for raw telemetry, historical location data, and short-lived export artifacts.
- Add hourly analytics rollup tables and lifecycle refresh logic so heatmap and hourly SLA trend queries can prefer precomputed data when available.
- Extend the Analytics workspace with export actions and a recent export queue for authorized users.
- Extend the administrator Health workspace with lifecycle status and a manual run action for retention and rollup jobs.
- Update shared contracts, backend schemas, tests, and product documentation to describe the delivered export and lifecycle baseline.

## Capabilities

### New Capabilities
- `exports-retention-and-rollups`: Async export jobs, lifecycle run tracking, retention policy behavior, and analytics rollup refresh behavior.

### Modified Capabilities
- `analytics-workspace-and-reports`: The Analytics workspace gains export actions, recent export history, and report states that account for pending or completed exports.
- `health-audit-ui-and-observability`: The administrator Health workspace gains lifecycle-job visibility and a supported trigger for retention and rollup refresh runs.

## Impact

- Affected code spans backend models, analytics queries, object-storage usage, new API routes, shared TypeScript contracts, and the web Analytics and Admin Health views.
- New durable state is required for export jobs, lifecycle runs, and rollup tables.
- Background processing remains inside the existing FastAPI and worker-friendly baseline rather than introducing a separate queue service in this change.
