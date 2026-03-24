# Bootstrap Follow-On Decisions

This document records decisions intentionally deferred out of the bootstrap implementation workspace change.

They should become later OpenSpec changes or design refinements instead of being expanded inside the bootstrap baseline.

## Deferred Decisions

- Split the coarse `worker` runtime into `worker-ingest`, `worker-positioning`, `worker-events`, and `worker-analytics`.
- Decide whether Redis Streams is sufficient or whether Kafka is required for internal stream processing.
- Define the full backend data model and migration strategy for operational entities and time-series data.
- Define the production container image publishing strategy and registry workflow.
- Decide whether the realtime API surface should remain inside the main FastAPI service or split into a dedicated delivery plane.
- Flesh out the Expo mobile architecture for navigation, QR scanning, blue-dot workflows, and native module requirements.
- Extend identity with SSO, password reset, MFA, login rate limiting, and hardened token transport.
- Implement the full Audit Log UI and richer audit filtering workflows.

## Related Planned Changes

- `implement-identity-rbac-and-audit-foundation`
- `implement-sites-floorplans-and-zone-editor`
- `implement-gateway-and-asset-registry`
- `implement-ingestion-pipeline-and-raw-readings`
- `implement-economic-tier-positioning-and-live-location`
- `implement-mobile-asset-finder`
- `implement-mobile-commissioning-and-calibration`
