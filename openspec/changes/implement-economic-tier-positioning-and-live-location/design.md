# implement-economic-tier-positioning-and-live-location Design

## Overview

This change adds the first derived-location layer on top of the existing ingestion pipeline. The minimal viable outcome is a backend service path that turns accepted economic-tier BLE telemetry into durable location outputs that other product surfaces can consume consistently.

The design stays intentionally narrow:

- Reuse the existing gateway, asset, floor, zone, and raw-reading foundations.
- Deliver backend contracts for latest location, history, search, and live updates.
- Keep premium-tier math, alerting, analytics, and mobile calibration guidance out of scope.

## Scope Boundaries

Included in this change:

- Economic-tier position estimation from accepted BLE raw readings.
- Persistence for current asset location and append-only location history.
- Confidence semantics that can represent point-level and fallback zone-level outputs.
- Authorized query and streaming interfaces for downstream consumers.

Explicitly excluded:

- Premium-tier AoA/UWB support.
- Analytics heatmaps, dwell, round-trip, or SLA derived events.
- Operator-facing live map UI implementation.
- Guided mobile calibration or commissioning workflows.

## Architectural Approach

### 1. Positioning stays downstream of raw-reading persistence

The ingestion pipeline already normalizes MQTT payloads and persists raw readings with canonical backend time. The positioning baseline should consume that durable layer instead of reparsing MQTT messages or coupling estimation directly to broker events. This preserves a clean stage boundary and keeps future replay/backfill options available.

### 2. Economic-tier output is confidence-aware

Economic-tier BLE telemetry will not always support a trustworthy point estimate. The output model therefore needs to represent:

- A floor-linked point result when the available readings support a credible estimate.
- A zone-linked fallback result when the system can place the asset only at a lower precision.
- Confidence metadata so downstream UI and analytics flows can explain certainty instead of implying precision the system does not have.

This keeps the contract honest and aligns with the existing product requirement for confidence scoring with zone fallback.

### 3. Current state and history are stored separately

Operational workflows need both "where is it now?" and "where has it been?". The design therefore assumes two durable outputs:

- A latest-known location record per tracked asset for fast current-state queries.
- An append-only history record for trajectory and replay consumers.

Keeping those concerns distinct avoids forcing every latest-location query to reconstruct state from history while preserving the timeline needed for later analytics work.

### 4. Live delivery complements, not replaces, durable queries

WebSocket updates are useful for operations screens, but they should not be the only contract. Consumers must be able to recover current state, search, and inspect history from authorized HTTP queries even if they connect after updates were emitted or temporarily lose the stream.

### 5. Calibration UX is deferred, reference data is assumed

The backlog places guided mobile calibration later than this change, but the positioning baseline still needs a source of reference data to produce economic-tier estimates. The proposal therefore assumes backend-managed reference inputs can exist before the mobile workflow is delivered. This avoids blocking the core live-location baseline while keeping the later calibration UX free to improve how those inputs are captured and maintained.

## Data and API Shape Implications

The positioning baseline will require:

- Durable position records linked to registered assets and mapped floors.
- Confidence metadata and optional zone fallback fields on location outputs.
- Query surfaces for latest location, filtered live search, and time-bounded history.
- A live-update stream that publishes newly accepted location changes for authorized consumers.

The exact transport and schema details should stay aligned with shared contracts so the later web-shell and mobile changes consume one stable surface.

## Risks and Tradeoffs

### Economic-tier precision limits

Economic-tier BLE location quality will vary with gateway density and reference-data quality. The proposal addresses this by requiring confidence-aware outputs rather than overcommitting to exact point precision in every case.

### Reference-data dependency before mobile calibration

This change depends on some form of positioning reference input before the later commissioning UX exists. That is an intentional tradeoff to keep the platform roadmap moving. The proposal should document the dependency clearly rather than silently assuming a future mobile workflow already exists.

### Streaming complexity

Adding live streaming increases backend surface area. The scope stays controlled by limiting the requirement to authorized live position updates only, without adding broader event-bus or notification concerns that belong to later changes.
