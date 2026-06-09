# Bootstrap Follow-On Decisions

This document records decisions intentionally deferred out of the bootstrap implementation workspace change.

They should become later OpenSpec changes or design refinements instead of being expanded inside the bootstrap baseline.

## Resolved Decisions

These items were deferred from bootstrap but have since been addressed by later OpenSpec changes:

| Decision | Resolved By | Resolution |
| :--- | :--- | :--- |
| Worker service splitting | `implement-ingestion-pipeline-and-raw-readings` | Single coarse `worker` service handles ingestion, positioning, and derived events. Dedicated worker splitting remains optional. |
| Redis Streams vs Kafka | `gateway-telemetry-ingestion` | Redis Streams is sufficient for the current throughput. Kafka remains an option for enterprise-scale deployments. |
| Backend data model and migration strategy | `raw-reading-persistence`, `economic-tier-position-estimation` | PostgreSQL + TimescaleDB with hypertables for time-series data. Application-managed retention windows. |
| Identity extensions (SSO, MFA, rate limiting) | Still deferred | Not yet implemented. Local JWT auth remains the baseline. |
| Full Audit Log UI | `audit-event-recording`, `implement-health-audit-ui-and-observability` | Audit events are persisted with query-ready structure. Admin Audit workspace with filtering is implemented. |
| Expo mobile architecture | `mobile-asset-finder`, `mobile-commissioning-and-calibration` | Expo with native QR scanning, AsyncStorage for local persistence, and web handoff. |
| Realtime API surface | `live-location-query-and-streaming` | WebSocket endpoint (`/ws/locations`) remains inside the main FastAPI service. |

## Still Deferred

These decisions remain open for future implementation:

- **Production container image publishing**: Define the production container image publishing strategy and registry workflow.
- **Dedicated realtime delivery plane**: Decide whether the realtime API surface should split from the main FastAPI service into a dedicated delivery plane.
- **SSO, password reset, MFA**: Extend identity with enterprise providers, password recovery, multi-factor authentication, and login rate limiting.
- **Advanced calibration engine**: Backend radiomap generation and fingerprinting reference data for the positioning pipeline.
- **Mobile self-location blue dot**: Live device self-positioning during calibration instead of tap-driven checkpoint capture.
- **Production MQTT mTLS**: Move gateway-to-broker path to production-grade TLS with mutual authentication.

## Related OpenSpec Specifications

The following specs address the bootstrap follow-on scope:

- `user-authentication`, `role-based-access`, `audit-event-recording` — identity and audit
- `gateway-telemetry-ingestion`, `raw-reading-persistence` — ingestion and data model
- `economic-tier-position-estimation`, `premium-tier-position-estimation` — positioning
- `mobile-asset-finder`, `mobile-commissioning-and-calibration` — mobile
- `local-runtime-stack` — runtime topology
- `implementation-workspace` — repo structure and shared packages
