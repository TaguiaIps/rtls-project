## Context

The RTLS Analytics Platform now has the implementation workspace, identity and audit foundations, spatial administration flows, and the gateway plus asset registry. The next planned dependency in `docs/implementation-plan.md` is the ingestion baseline that can accept real telemetry from deployed gateways and persist it in a form that later positioning, alerts, analytics, and mobile workflows can reuse.

The supporting system documents already describe the intended runtime direction:

- `docs/system-design.md` defines MQTT as the gateway transport, `message_id`-based dedupe in Redis, `broker_received_timestamp` as the canonical timestamp, and TimescaleDB-backed raw readings.
- `docs/deployment-strategy.md` places this work in Stage B while keeping ingestion inside the existing `worker` deployable at first.
- `docs/technical-specification-document.md` expects continuous heartbeat reporting and time-series persistence without requiring the full health dashboard yet.

This change should establish one ingestion contract and one raw-telemetry persistence model. It must not pull in position estimation, WebSocket fan-out, alert evaluation, or analytics rollups.

## Goals / Non-Goals

**Goals:**

- Introduce a worker-hosted MQTT ingestion path for registered gateways.
- Validate telemetry and heartbeat payloads before any durable state changes.
- Add duplicate-delivery protection so QoS=1 retries do not create duplicate raw readings.
- Persist canonical raw readings with broker-received time and gateway linkage for later downstream consumers.
- Persist the latest heartbeat-derived health snapshot needed for backend health feeds.
- Define the runtime and configuration expectations for broker connectivity, Redis dedupe, and ingestion-oriented database persistence.

**Non-Goals:**

- Implement economic-tier positioning, confidence scoring, or location history.
- Implement live-map APIs, WebSocket updates, or user-facing operations dashboards.
- Implement the full health dashboard, packet-loss analytics, battery trend views, or offline alerts.
- Split the initial `worker` into separate `worker-ingest` and `worker-positioning` deployables.
- Introduce premium-tier AoA or UWB telemetry handling in this change.

## Decisions

### 1. Run ingestion inside the existing worker baseline first

The first implementation should extend the current `worker` responsibility instead of introducing a separate ingestion deployable immediately. The deployment strategy already recommends keeping Stage B ingestion and positioning concerns in the shared `worker` runtime until throughput or failure isolation proves that a split is necessary.

Rationale:

- It matches the current deployment guidance and keeps the runtime simple while the ingestion contract is still stabilizing.
- It avoids early coordination overhead between a new service and the rest of the backend.
- It still leaves room to split into `worker-ingest` later without redefining the MQTT or persistence contracts.

Alternatives considered:

- Introduce a dedicated ingestion service now: too much operational complexity for the first live-telemetry baseline.
- Handle MQTT directly in the API service: creates an avoidable coupling between request handling and long-running ingestion work.

### 2. Accept telemetry only from registered gateways and documented MQTT topics

The ingestion path should treat the gateway registry as the source of truth for which devices may publish telemetry. The canonical data topic remains `rtls/data/{gateway_id}` as described in `docs/system-design.md`, and the first heartbeat contract should use a dedicated heartbeat topic so liveness messages do not have to be inferred from beacon payloads.

Rationale:

- It reuses the gateway registry introduced in the previous change instead of allowing anonymous or ad hoc telemetry producers.
- It keeps ingestion troubleshooting and operational ownership clear because every accepted message maps to a known gateway.
- A dedicated heartbeat topic keeps the first telemetry and liveness contracts simple and explicit.

Alternatives considered:

- Accept any topic payload that self-declares a `gateway_id`: too weak for trust, supportability, and later ACL enforcement.
- Infer heartbeat only from data traffic: unreliable when gateways are online but temporarily not observing tags.

### 3. Use broker-received time as canonical and keep gateway time as metadata only

Every accepted ingestion event should be stamped with a backend-controlled `broker_received_timestamp`, and that timestamp becomes the canonical ordering and persistence time. Gateway-supplied timestamps remain optional metadata for diagnostics and future skew analysis.

Rationale:

- It follows the current system design and avoids trusting edge clocks for canonical ordering.
- It gives later positioning and analytics changes a single stable time basis.
- It allows inconsistent or missing gateway clocks without blocking ingestion.

Alternatives considered:

- Trust gateway timestamps as canonical: too fragile when devices drift or misconfigure time.
- Drop gateway timestamps entirely: removes useful debugging context for later diagnostics.

### 4. Deduplicate on ingestion before raw persistence

The first ingestion baseline should treat MQTT QoS=1 replay as expected behavior and perform duplicate detection before persisting raw telemetry. Redis is already part of the baseline runtime and should hold short-lived dedupe keys keyed by gateway and message identity.

Rationale:

- It prevents duplicate raw readings without requiring heavyweight idempotency logic in the database first.
- It aligns with the current system design that already calls for Redis-backed `message_id` dedupe.
- It preserves the option to harden with additional database uniqueness later if production traffic requires it.

Alternatives considered:

- Deduplicate only with a database uniqueness constraint: workable, but slower and noisier for the expected QoS=1 retry path.
- Do not deduplicate until positioning exists: would pollute the raw-readings baseline and complicate all later consumers.

### 5. Persist raw telemetry in a query-ready form and keep health state separate

This change should persist raw readings in a durable time-series store for later downstream use, while heartbeat-derived gateway health remains a separate current-state view. Raw telemetry and health snapshots serve different access patterns and should not be collapsed into one table or one API concern.

Rationale:

- Raw readings are append-only historical facts, while gateway health is a latest-known-state concern.
- Later positioning, exports, and analytics need historical telemetry without being coupled to liveness semantics.
- The first gateway health feed can remain small and focused without pretending to be a full observability feature.

Alternatives considered:

- Store health only by querying the raw-readings history: too indirect for a simple latest-state feed.
- Store all telemetry as opaque blobs only: too weak for later query patterns and debugging workflows.

## Risks / Trade-offs

- [The first telemetry schema may not cover every gateway vendor nuance] -> Mitigation: keep the initial contract narrow around the documented economic-tier payload and add premium-tier extensions in a later change.
- [Redis-only dedupe windows can miss very-late replays] -> Mitigation: define the replay window explicitly and leave longer-term hardening to later observability and scaling work.
- [A combined worker runtime can mix ingestion faults with other background responsibilities] -> Mitigation: keep the contract and runtime boundaries explicit so the worker can be split later without reworking the spec.
- [Gateway health feed scope can creep toward a full monitoring product] -> Mitigation: constrain this change to latest heartbeat state only and defer alerts, packet-loss metrics, and dashboards.

## Migration Plan

1. Define the ingestion topic contracts, payload rules, dedupe behavior, and gateway-registration preconditions for accepted telemetry.
2. Add persistence structures for raw telemetry history and latest gateway heartbeat state.
3. Extend the worker runtime and configuration model to connect to MQTT, Redis, and the database using the existing Stage B topology.
4. Add backend-facing health-feed and ingestion support contracts so later positioning and health UI changes can consume stable shapes.
5. Validate the ingestion baseline with integration coverage for valid telemetry, malformed payloads, unknown gateways, duplicate delivery, and heartbeat updates.

Rollback strategy:

- If the ingestion contract proves unstable, disable MQTT subscription and leave the existing gateway registry intact rather than partially consuming live traffic.
- If heartbeat-state persistence proves noisy, keep raw telemetry ingestion enabled and temporarily disable the health-feed projection until the contract is corrected.

## Open Questions

- Whether the first accepted telemetry payload should require a gateway-supplied timestamp or allow it to remain optional from day one.
- Whether the first gateway health feed should expose only `last_seen_at` style data or also include simple status labels such as healthy versus stale.
- Whether unknown observed tag identifiers should always be persisted as raw facts even when no asset-tag registry match exists yet.
