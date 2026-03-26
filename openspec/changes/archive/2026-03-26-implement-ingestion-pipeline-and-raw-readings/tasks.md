## 1. Ingestion Contract And Persistence Foundation

- [x] 1.1 Define the MQTT telemetry and heartbeat contracts, accepted gateway identity rules, and duplicate-delivery behavior for the Wave 2 ingestion baseline
- [x] 1.2 Define the raw-reading and latest-heartbeat persistence structures, including canonical broker-received time and gateway linkage
- [x] 1.3 Define the worker runtime and environment configuration needed for MQTT connectivity, Redis dedupe, and database persistence

## 2. Backend Ingestion Worker

- [x] 2.1 Extend the existing worker baseline to subscribe to the documented MQTT topics and validate telemetry plus heartbeat payloads from registered gateways
- [x] 2.2 Add duplicate protection and explicit rejection handling for malformed, replayed, or unknown-gateway messages before any durable writes occur
- [x] 2.3 Persist canonical raw readings and update the latest gateway heartbeat state without introducing positioning or alert-generation behavior
- [x] 2.4 Add backend support for querying the latest gateway health feed needed by later operational workflows

## 3. Verification And Documentation

- [x] 3.1 Add integration and worker-level tests covering valid telemetry ingestion, malformed payload rejection, unknown gateways, duplicate delivery, and heartbeat updates
- [x] 3.2 Document the ingestion contracts, runtime configuration, and Stage B deployment expectations in the system and operational docs
- [x] 3.3 Verify that positioning, live-map delivery, health dashboards, alerts, analytics, and premium-tier telemetry remain explicitly out of scope for this change
- [x] 3.4 Run `openspec validate implement-ingestion-pipeline-and-raw-readings --strict` before implementation begins and again after the proposal artifacts are updated
