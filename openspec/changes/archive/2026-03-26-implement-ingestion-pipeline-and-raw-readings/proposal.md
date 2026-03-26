## Why

The RTLS Analytics Platform now has the implementation workspace, identity foundation, spatial setup flows, and the gateway and asset registry, but it still cannot accept real telemetry from deployed gateways. This change is needed now because Wave 2 depends on a single normalized ingestion path for MQTT payloads, dedupe, heartbeat handling, and raw-readings persistence before positioning, live maps, alerts, or analytics can be built safely on top.

## What Changes

- Add MQTT-based gateway telemetry ingestion to the existing backend worker baseline using registered gateway identifiers as the canonical source of gateway identity.
- Add payload validation, duplicate-delivery protection, canonical broker-received timestamps, and explicit rejection handling for malformed or unknown-gateway telemetry.
- Add durable raw-readings persistence for later positioning, analytics, and operational debugging workflows.
- Add heartbeat ingestion and a backend gateway health feed that reports the latest heartbeat state without introducing the full health dashboard yet.
- Add the runtime and configuration contracts needed for the broker, worker, Redis dedupe keys, and TimescaleDB persistence boundaries.
- Keep live positioning, WebSocket fan-out, derived events, alerts, analytics workspaces, and mobile commissioning out of scope for this change.

## Capabilities

### New Capabilities
- `gateway-telemetry-ingestion`: Covers MQTT topic handling, payload validation, duplicate protection, heartbeat ingestion, and gateway health-feed generation.
- `raw-reading-persistence`: Covers canonical raw-readings storage, registered-gateway linkage, broker timestamping, and query-ready persistence for later positioning and analytics changes.

### Modified Capabilities
- None.

## Impact

- Affects backend worker responsibilities, ingestion-side persistence models, Redis coordination, and database schema for raw telemetry records.
- Affects runtime and deployment contracts for MQTT broker connectivity, worker behavior, and telemetry-oriented configuration.
- Establishes the single ingestion contract that later positioning, live map, alerts, analytics, and mobile changes will consume instead of redefining telemetry parsing.
- Formalizes the Wave 2 entry point described in `docs/implementation-plan.md` without prematurely pulling in location computation or user-facing live-tracking UX.
