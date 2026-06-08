## 1. Event Contracts

- [x] 1.1 Define the canonical derived-event contract for zone entry, zone exit, dwell windows, round-trip measurements, and current table timer state.
- [x] 1.2 Document the forward-only rollout assumption and the scope boundary between this event foundation and later alerting or analytics features.

## 2. Canonical Zone Events

- [x] 2.1 Add durable storage for canonical zone-transition events and closed dwell records derived from accepted live-location updates.
- [x] 2.2 Implement duplicate suppression so repeated updates inside the same resolved zone do not emit redundant transition events.
- [x] 2.3 Ensure floor changes, unmapped periods, and loss of resolved zone placement close prior occupancy cleanly instead of leaving orphaned dwell state.

## 3. Higher-Order Primitives

- [x] 3.1 Implement reusable round-trip measurement primitives that evaluate origin-destination-origin cycles from canonical zone events for supported downstream queries.
- [x] 3.2 Implement current table-service timer primitives for `sla_eligible` table areas using existing spatial metadata without adding alert rules or notification behavior.
- [x] 3.3 Add regression coverage for transition ordering, dwell closure, round-trip completion, and table timer updates.

## 4. Integration And Validation

- [x] 4.1 Add backend-facing read contracts that later alerting and analytics changes can consume for derived-event history and current timer state.
- [x] 4.2 Update system and workflow documentation to describe the new derived-event foundation and how later alerts and analytics changes build on it.
- [x] 4.3 Validate the change with `openspec validate implement-derived-events-dwell-roundtrip-and-sla-primitives --strict`.
