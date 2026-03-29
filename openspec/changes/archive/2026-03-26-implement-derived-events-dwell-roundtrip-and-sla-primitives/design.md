## Context

The current repository baseline already has the ingredients needed to start deriving operational meaning from location data:

- accepted raw gateway telemetry
- durable current asset location and location history
- mapped floors and typed spatial areas
- existing table-related metadata such as `sla_eligible`
- a delivered web shell that can already consume live location and overview data

What is still missing is the shared event layer that explains what happened in business terms. Alerts and analytics both need to know when an asset entered or exited a zone, how long it stayed there, whether a route completed a round trip, and how long it has been since a qualifying table visit. If each later feature computes those semantics independently, the platform will drift into inconsistent timing, duplicated logic, and harder-to-debug operational behavior.

## Goals / Non-Goals

**Goals:**

- Derive canonical zone-entry, zone-exit, and dwell records from accepted live-location updates.
- Provide reusable round-trip measurement primitives that operate on the canonical zone-event history instead of raw telemetry.
- Maintain durable current timer state for SLA-eligible table areas.
- Expose backend-facing read contracts that later alerting and analytics changes can consume without reinterpreting raw locations.
- Keep the first rollout narrow enough to fit the next backlog slice cleanly.

**Non-Goals:**

- Alert-rule configuration, notification delivery, acknowledgements, or Alerts Center UI.
- Analytics report screens, heatmaps, or trend dashboards.
- Premium-tier AoA or UWB event semantics.
- Mobile workflows or guided calibration.
- Full historical backfill from pre-existing location history in the initial rollout.

## Decisions

### 1. Derive business events from accepted live-location updates, not raw MQTT readings

The new event layer should sit downstream of the positioning baseline. That keeps one canonical interpretation of confidence, floor selection, and zone fallback. Deriving events from raw readings would duplicate location logic and create avoidable disagreement between the live map and later alerts or analytics.

Alternatives considered:

- Derive directly from raw MQTT telemetry: rejected because it duplicates positioning and would create noisy, hardware-shaped event semantics instead of business-shaped ones.
- Derive from WebSocket updates: rejected because streams are delivery mechanisms, not durable system-of-record inputs.

### 2. Persist canonical event history separately from current timer snapshots

The system needs both append-only history and fast current state:

- canonical zone-entry, zone-exit, and closed-dwell records for history and replay
- current timer state for SLA-eligible tables so later workflows can ask "what is overdue now?" without replaying the full event stream

Separating those concerns keeps the read path simple while preserving the full event history needed for later analytics work.

Alternatives considered:

- Only append history and force current-state reconstruction on every read: rejected because current SLA-style timing reads would become unnecessarily expensive and harder to reason about.
- Only store snapshots and skip history: rejected because later analytics and auditability require durable event trails.

### 3. Suppress duplicate same-zone churn and close occupancy cleanly on ambiguity

The derived-event layer should only emit transition events when the resolved zone meaning actually changes. Repeated point updates that stay in the same zone should extend the same dwell context rather than create duplicate entries. When an asset leaves mapped placement, changes floors, or no longer resolves to a zone, the previous occupancy should close cleanly instead of leaving orphaned open dwell state.

Alternatives considered:

- Emit an event for every location update: rejected because downstream alerts and analytics would have to deduplicate noisy repeats.
- Keep open dwell windows through unmapped periods: rejected because it would overstate occupancy duration and blur the difference between "still in zone" and "currently unknown."

### 4. Keep round-trip measurement route-parameterized instead of precomputing every possible pair

This change should introduce a reusable primitive, not a fully materialized analytics warehouse. The backend can evaluate completed origin-destination-origin cycles from canonical zone events for explicit route selections supplied by downstream consumers. That keeps scope tight and avoids exploding storage or compute for every possible zone pair before real reporting demand exists.

Alternatives considered:

- Precompute every possible zone-pair round trip: rejected because the combinatorics are poor and the later analytics change is better positioned to decide which route aggregates deserve materialization.
- Defer round-trip support entirely: rejected because the implementation plan calls for reusable round-trip primitives in this change.

### 5. Use existing table metadata as the participation baseline for SLA timers

The first primitive should focus on table areas that are already modeled as typed spatial areas and marked `sla_eligible`. This change should maintain the current timer state those tables need, while leaving threshold policy, notification behavior, and richer participation rules to later alerting work.

Alternatives considered:

- Introduce a full alert-policy model here: rejected because that belongs to the later alert-rules change.
- Wait for analytics or alerts to compute timers ad hoc: rejected because it would recreate the same shared-foundation problem this change is meant to solve.

## Risks / Trade-offs

- [Forward-only rollout leaves older location history without derived events] -> Mitigation: document that the first implementation starts deriving events from new updates after deployment and treat historical backfill as later work if it becomes necessary.
- [Low-confidence or unmapped periods may fragment dwell history] -> Mitigation: derive events only from accepted live-location outputs and close prior occupancy explicitly when mapped placement is lost.
- [On-demand round-trip evaluation can become expensive for broad queries] -> Mitigation: bound route evaluations by site, floor, asset cohort, and time window, and leave materialized aggregates to later analytics work.
- [Initial table-timer semantics may be broader than final restaurant workflows] -> Mitigation: keep this layer focused on timer state and avoid embedding alert thresholds or notification policy in the primitive itself.

## Migration Plan

1. Add the derived-event and timer-state persistence model alongside the existing positioning baseline.
2. Update the backend processing flow so new accepted live-location updates also maintain canonical zone events, dwell closures, round-trip evaluation inputs, and table timer state.
3. Start the derived-event layer in forward-only mode for newly processed updates.
4. Validate downstream consumers against the new event and timer contracts before any future backfill or aggregate jobs are introduced.

## Open Questions

- None at proposal stage. The remaining complexity is mainly in implementation trade-offs rather than missing product direction.
