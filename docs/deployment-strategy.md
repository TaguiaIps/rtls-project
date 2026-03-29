# Deployment Strategy

This document defines the recommended deployment strategy for the RTLS Analytics Platform.

It exists to answer a different question than the implementation plan:

- [implementation-plan.md](/home/hugo/Documents/taguia/rtls_project/docs/implementation-plan.md) explains how the work should be segmented and implemented over time.
- This document explains how the runtime system should be packaged, deployed, operated, and evolved across environments.

## 1. Purpose

The project already assumes Docker-based services and a Kubernetes-oriented architecture in:

- [system-design.md](/home/hugo/Documents/taguia/rtls_project/docs/system-design.md)
- [technical-specification-document.md](/home/hugo/Documents/taguia/rtls_project/docs/technical-specification-document.md)

Those documents are directionally correct, but they do not yet define:

- which logical modules are separate deployable units
- which services should stay combined at first
- how local, pilot, and production deployments differ
- when a simple Docker deployment is still adequate
- when orchestration becomes necessary

This document fills that gap.

## 2. Deployment Principles

- Start with a containerized baseline that is simple enough to run locally and in CI.
- Keep the number of deployable services low until runtime boundaries are proven useful.
- Separate stateful infrastructure from stateless application services.
- Prefer one source of truth for telemetry ingestion, derived events, and analytics instead of duplicated pipelines.
- Design the deployment model to support both cloud-hosted and on-prem or edge-adjacent installations.
- Treat observability, backups, and secret management as part of deployment, not as later cleanup.

## 3. Logical Modules vs Deployable Units

Not every implementation module should be deployed as its own service.

The implementation plan intentionally splits work into bounded changes such as auth, spatial modeling, ingestion, positioning, and analytics. Those are logical implementation concerns. The runtime topology should be coarser at first.

### 3.1 Recommended initial deployable units

For the first implementation baseline, the runtime should be packaged as these units:

| Deployable Unit | Responsibility | Initial Runtime Form |
| --- | --- | --- |
| `web` | Serves the React web app and static assets | One container |
| `api` | REST API, WebSocket endpoints, auth, admin, asset, zone, alert, analytics query endpoints | One container |
| `worker` | Background jobs for ingestion-adjacent tasks, positioning, derived events, alert generation, exports, scheduled rollups | One container initially |
| `mqtt-broker` | Receives gateway telemetry over MQTT with TLS and ACLs | One container |
| `redis` | Dedupe cache, ephemeral coordination, optional streams, session revocation | One container |
| `timescaledb` | Primary operational and time-series database | One container or managed service |
| `object-storage` | Floor plans, calibration artifacts, export files | One container in dev, managed S3-compatible service in production |
| `reverse-proxy` | TLS termination, routing, static caching, websocket proxying | One container or ingress controller |

### 3.2 Services that should stay combined at first

The following concerns should initially live inside the `api` or `worker` containers instead of being split into separate deployables:

- auth and RBAC
- audit actor capture
- spatial CRUD APIs
- gateway and asset registry APIs
- alert rules management APIs
- analytics query APIs
- positioning jobs
- derived event processing
- inline alert evaluation and in-app notification persistence for delivered operational rules
- export generation
- scheduled data retention and rollups

This avoids premature service fragmentation while the codebase is still being established.

For the current derived-event foundation, keep the projection inline with accepted live-location processing inside the shared worker. Split it into a dedicated `worker-events` process only after throughput, retry isolation, or ownership pressure justifies the extra boundary.

### 3.3 Services that may be split later

Split the initial `worker` into dedicated deployables only when throughput, fault isolation, or team ownership requires it:

- `worker-ingest`
- `worker-positioning`
- `worker-events`
- `worker-analytics`

Likewise, split the `api` service only if the control plane and real-time plane need independent scaling:

- `api-rest`
- `api-realtime`

## 4. Environment Strategy

The project should use three deployment profiles.

### 4.1 Local development

Use Docker Compose.

This is the correct baseline for:

- day-to-day development
- contract validation
- integration tests
- initial demo environments

Local development should start with:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Recommended characteristics:

- bind mounts only where local iteration speed matters
- seeded sample data
- fake or replayable telemetry source for predictable demos
- local TLS optional
- production-like environment variables and service names

### 4.2 Pilot or small production deployment

A small set of Docker containers is still adequate for the first real deployment if all of these are true:

- one customer or one site at a time
- modest asset count and event volume
- acceptable maintenance windows
- no hard multi-region or HA requirement
- operational staff can tolerate node replacement or controlled downtime

Recommended pilot shape:

- one VM or a small pair of VMs
- containers managed with Docker Compose, systemd, or a lightweight orchestrator
- external reverse proxy
- persistent volumes for database and object storage
- automated backups
- basic monitoring and alerting

This is appropriate for early adoption, demos, staging, and first customer pilots.

### 4.3 Scaled production deployment

For multi-site production, stronger uptime expectations, or higher telemetry volume, use `k3s` or Kubernetes.

Recommended characteristics:

- at least a small cluster
- replicated stateless services
- rolling deployments
- centralized secrets management
- ingress controller
- dedicated observability stack
- backup and restore automation

This is the default target once the platform becomes operationally important for more than a single pilot environment.

## 5. Recommended Runtime Topology by Stage

### 5.1 Stage A: Bootstrap and early implementation

Topology:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Use this stage for implementation plan changes:

- `bootstrap-implementation-workspace`
- `implement-identity-rbac-and-audit-foundation`
- `implement-sites-floorplans-and-zone-editor`
- `implement-gateway-and-asset-registry`

Reasoning:

- lowest operational complexity
- easiest onboarding for coding agents and developers
- no premature queue topology decisions

### 5.2 Stage B: Live telemetry and positioning baseline

Topology:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Optional internal split if pressure appears:

- `worker-ingest`
- `worker-positioning`

Use this stage for:

- `implement-ingestion-pipeline-and-raw-readings`
- `implement-economic-tier-positioning-and-live-location`
- `deliver-web-shell-operations-overview-and-live-map`

Reasoning:

- preserves simple deployment while live data pipelines mature
- keeps failure analysis manageable
- avoids repeating ingestion contracts across multiple services

Stage B runtime contract:

- the shared `worker` subscribes to `rtls/data/+` and `rtls/heartbeat/+`
- accepted messages must resolve to a registered gateway before durable writes
- Redis stores `(gateway_id, message_id)` dedupe keys for the short replay window
- TimescaleDB persists append-only raw readings plus the latest gateway heartbeat snapshot
- the same worker computes economic-tier latest-location state and append-only location history from recent raw readings on mapped floors
- the same worker can also project forward-only canonical zone transitions, dwell closures, current table timer snapshots, and the first delivered alert lifecycle for table-SLA and unauthorized-geofence rules without adding a second event pipeline
- the API serves authorized latest-location queries, time-bounded history, derived-event read contracts, and `/ws/locations` updates from durable state
- the API also serves `/api/alerts/*` rule, queue, detail, acknowledgement, resolution, and shell-summary contracts from durable state
- maintenance alerts, analytics rollups, premium-tier telemetry, and guided mobile calibration stay out of scope until later changes

### 5.3 Stage C: Operational intelligence baseline

Topology:

- `web`
- `api`
- `worker-ingest`
- `worker-positioning`
- `worker-events`
- optional `worker-analytics`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Use this stage for:

- `implement-derived-events-dwell-roundtrip-and-sla-primitives`
- `implement-alert-rules-and-alerts-center`
- `implement-analytics-workspace-and-reports`

Reasoning:

- derived events and alerting now exist as a delivered product concern, but the first rollout still runs inline on the shared worker path for simplicity
- split `worker-events` only after throughput, retry isolation, or ownership pressure justifies the extra boundary
- analytics jobs should not delay real-time event processing

### 5.4 Stage D: Hardened production platform

Topology:

- `web`
- `api-rest`
- optional `api-realtime`
- `worker-ingest`
- `worker-positioning`
- `worker-events`
- `worker-analytics`
- `mqtt-broker`
- `redis`
- `timescaledb`
- managed or hardened `object-storage`
- ingress controller
- observability stack

Use this stage for:

- `add-premium-tier-aoa-uwb-support`
- `implement-mobile-asset-finder`
- `implement-mobile-commissioning-and-calibration`
- `implement-health-audit-ui-and-observability`
- `implement-exports-retention-and-rollups`

Reasoning:

- premium telemetry and production operations justify finer-grained scaling
- exports and historical workloads should not interfere with real-time flows

## 6. Detailed Deployment Model

### 6.1 `web`

- Build artifact: static SPA bundle
- Packaging: Nginx or similar lightweight static server
- Scaling: horizontal if needed
- State: stateless
- Notes: keep runtime config injection simple so deployments do not require recompiling for each environment

### 6.2 `api`

- Build artifact: FastAPI application
- Responsibilities:
  - auth
  - REST APIs
  - WebSocket push
  - role checks
  - admin CRUD
  - alert query and acknowledgement endpoints
  - analytics read APIs
- Scaling: horizontal after externalizing sessions and shared state
- State: stateless except for external dependencies
- Notes: Redis should hold revocation/session state, not the API container

### 6.3 `worker`

- Build artifact: Python worker process or worker image family
- Responsibilities:
  - MQTT telemetry and heartbeat subscription
  - gateway identity validation
  - duplicate suppression with Redis
  - raw-reading persistence
  - latest-heartbeat projection
  - positioning jobs
  - derived event generation
- alert generation
- in-app notification persistence and optional email-delivery attempts for delivered alert rules
- exports
- retention and rollup jobs
- Scaling: vertical first, then horizontal per specialized worker type
- State: stateless workers with durable state in TimescaleDB and object storage
- Required runtime settings for the ingestion baseline:
  - `RTLS_MQTT_BROKER_HOST`
  - `RTLS_MQTT_BROKER_PORT`
  - `RTLS_MQTT_USERNAME`
  - `RTLS_MQTT_PASSWORD`
  - `RTLS_MQTT_KEEPALIVE_SECONDS`
  - `RTLS_MQTT_TOPIC_PREFIX`
  - `RTLS_INGESTION_DEDUPE_KEY_PREFIX`
  - `RTLS_INGESTION_DEDUPE_TTL_SECONDS`
  - `RTLS_GATEWAY_HEARTBEAT_STALE_AFTER_SECONDS`

### 6.4 `mqtt-broker`

- Recommended choices:
  - Mosquitto for initial simplicity
  - EMQX if advanced broker observability and scale become necessary
- Responsibilities:
  - accept gateway telemetry
  - enforce TLS
  - enforce topic ACLs
- State: low persistence needs for the initial QoS=1 flow, but production config and credentials must be durable

### 6.5 `redis`

- Responsibilities:
  - dedupe keys
  - short-lived coordination
  - session revocation
  - optional streams
- Notes:
  - keep Redis ephemeral in dev
  - use persistence only when operationally justified
  - do not treat Redis as the system of record

### 6.6 `timescaledb`

- Responsibilities:
  - operational entities
  - raw readings
  - location history
  - derived business events
  - analytics rollups
- Notes:
  - this is the primary system of record
  - production requires scheduled backups and tested restore procedures
  - storage sizing must account for telemetry retention and rollups

### 6.7 `object-storage`

- Responsibilities:
  - floor plan images
  - exports
  - calibration and import artifacts
- Recommended choices:
  - MinIO in local and pilot environments
  - S3-compatible managed storage where available in production

## 7. Networking and Security

### 7.1 External entry points

Expose only the required public surfaces:

- HTTPS for web and REST
- secure WebSocket endpoint
- MQTT over TLS for gateways

Do not expose Redis, TimescaleDB, or internal worker ports publicly.

### 7.2 TLS and identity

- Terminate HTTPS at the reverse proxy or ingress
- Use TLS for MQTT gateway connections
- Prefer client certificates for gateways where feasible
- Use short-lived access tokens and rotated refresh tokens for users
- Store secrets outside application images

### 7.3 Network segmentation

Separate at least these logical zones:

- public ingress
- application services
- stateful infrastructure
- observability

In Kubernetes, implement this with namespaces and network policies. In simpler Docker deployments, approximate it with internal networks and firewall rules.

## 8. Stateful Services, Persistence, and Backups

### 8.1 Source of truth

Treat these as persistent data stores:

- `timescaledb`
- `object-storage`

Redis and MQTT are operational infrastructure, not long-term source-of-truth stores.

### 8.2 Backup policy

Minimum baseline:

- daily full database backup
- periodic transaction-log or WAL-aware backup strategy
- regular object storage backup or replication
- documented restore drills

### 8.3 Retention and archival

- retain high-volume raw readings for the configured short-term period
- roll up to hourly and daily summaries
- archive exports and artifacts with lifecycle policies
- do not let analytical retention requirements quietly overload the operational cluster

## 9. Observability and Operations

The deployment is incomplete without operational visibility.

Minimum observability baseline:

- container health checks
- structured application logs
- Prometheus metrics
- Grafana dashboards
- alerting on gateway disconnect rate, ingest lag, worker lag, API latency, DB saturation, and websocket fan-out issues

Recommended later additions:

- OpenTelemetry traces across ingest, positioning, event generation, and API delivery
- SLO dashboards
- audit log review workflows

## 10. CI/CD and Release Strategy

### 10.1 Build pipeline

Each deployable unit should produce a versioned container image.

Baseline pipeline:

- lint
- unit tests
- integration tests for service contracts
- container build
- image scan
- publish to registry

### 10.2 Promotion path

Recommended path:

1. local Compose
2. shared dev environment
3. staging or pilot
4. production

### 10.3 Rollout style

- use rolling updates for stateless services
- use controlled migrations for database schema changes
- gate risky telemetry pipeline changes behind configuration flags where practical
- keep the mobile app release cadence independent from backend container rollout

## 11. When a Simple Docker Deployment Is Adequate

A straightforward Docker-based deployment is adequate when:

- the system serves one environment or a small number of sites
- throughput is moderate
- downtime risk is acceptable during maintenance
- on-call maturity is still limited
- the team needs a simple platform to reach the first production baseline

It becomes inadequate when:

- one host becomes a single unacceptable point of failure
- real-time and analytics workloads compete heavily
- deployment frequency increases
- rollback needs become operationally important
- multi-site scale or premium-tier throughput materially increases load

## 12. Recommended Decision for This Project

The recommended deployment path is:

1. Define `Docker Compose` as the mandatory local and CI integration baseline.
2. Implement the first production-capable runtime as a small set of containers, not as many microservices.
3. Defer service splitting until the ingestion, positioning, and event boundaries are exercised by real telemetry.
4. Move to `k3s` or Kubernetes once pilot success justifies stronger uptime and scaling guarantees.

This keeps the platform aligned with the architecture documents while avoiding needless infrastructure complexity before the first implementation baseline exists.

## 13. Relationship to Future OpenSpec Changes

This document should influence future OpenSpec work as follows:

- `bootstrap-implementation-workspace`
  - must define the initial Docker Compose stack
  - must define image naming, environment conventions, and local startup flow
- `implement-ingestion-pipeline-and-raw-readings`
  - must define MQTT broker integration and worker runtime behavior
- `implement-economic-tier-positioning-and-live-location`
  - must validate whether `worker` remains combined or should split
- `implement-health-audit-ui-and-observability`
  - must add the production observability baseline
- `implement-exports-retention-and-rollups`
  - must refine storage, retention, and long-running job deployment behavior

OpenSpec design artifacts for those changes should reference this document instead of redefining the full deployment topology from scratch.

## 14. Open Questions to Revisit Later

These do not block the current strategy, but they should be revisited when implementation begins:

- whether Redis Streams is sufficient or Kafka becomes necessary
- whether the broker should remain Mosquitto or move to EMQX
- whether TimescaleDB stays self-hosted or becomes managed
- whether the first production target is cloud-hosted, on-prem, or hybrid
- whether premium-tier telemetry volume requires a separate real-time API plane
