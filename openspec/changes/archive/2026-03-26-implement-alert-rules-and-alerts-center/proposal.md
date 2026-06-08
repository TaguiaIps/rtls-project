## Why

The RTLS Analytics Platform now has canonical zone transitions, dwell history, round-trip primitives, and current table timer snapshots, but it still lacks the rule layer that turns those signals into actionable alerts for operators. This change is needed now because the delivered monitoring shell can already support triage workflows, and the product requirements for table SLA alerts, unauthorized geofence alerts, and in-app notification delivery depend on a shared alert foundation instead of ad hoc downstream logic.

## What Changes

- Add typed alert rule management for the first delivered alert types: table SLA violations and unauthorized geofence alerts.
- Add alert evaluation and durable alert persistence that consume the existing derived-event and table-timer foundations instead of reinterpreting raw telemetry.
- Add in-app notification delivery and optional email delivery preferences for supported alert rules and alert instances.
- Add Alerts Center backend read and action contracts plus a web Alerts Center route for queue, detail, filtering, acknowledgement, and resolution workflows.
- Extend the shared web operations shell with a delivered Alerts destination and unresolved-alert access point.
- Update documentation to call out the current scope boundary: this change delivers operational alerting for SLA and unauthorized geofence use cases, while maintenance alerts remain part of the later health and observability change despite broader UX sketches that mention them.
- Keep analytics reporting, overview redesign, assignment or escalation workflows, gateway maintenance alerts, exports, and premium-tier alert semantics out of scope for this change.

## Capabilities

### New Capabilities

- `alert-rules-and-notification-delivery`: Typed alert rule management, alert generation, lifecycle handling, in-app notifications, and optional email delivery for delivered operational alert types.
- `alerts-center-triage`: Alerts Center queue, detail, history, filtering, and user actions for acknowledging and resolving alerts.

### Modified Capabilities

- `web-operations-shell`: The shared operations shell gains a delivered Alerts destination and unresolved-alert access once the Alerts Center is available.

## Impact

- Affects backend models, worker-side derived-event consumers, protected API routes, audit capture, and optional notification-delivery integration in `apps/api`.
- Affects shared contracts and the React operations shell in `apps/web` where Alerts Center navigation, queue, detail, and action flows will live.
- Requires OpenSpec and documentation updates so the delivered alert scope stays aligned with the implementation plan and does not silently absorb later health-dashboard or analytics work.
