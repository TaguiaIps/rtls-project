## Context

The repository now has the baseline pieces needed for operational alerting:

- authenticated users and role-aware web routing
- audit-event capture for protected mutations
- mapped spatial areas with `sla_eligible` and `alert_participation` metadata
- canonical zone-entry and zone-exit history plus closed dwell records
- current timer snapshots for SLA-eligible tables
- a delivered shared operations shell with Overview and Live Map routes

What is still missing is the rule engine and triage layer that convert those derived operational signals into durable alerts and user-facing action flows. The implementation plan names `implement-alert-rules-and-alerts-center` as the next bounded change after the derived-event foundation. The source material is slightly inconsistent about scope: broader UX sketches mention maintenance alerts, but the implementation plan and functional requirements for this change are centered on table SLA alerts, unauthorized geofence alerts, and in-app or optional email notification delivery. This design keeps that narrower scope explicit.

## Goals / Non-Goals

**Goals:**

- Deliver typed alert rule management for table SLA and unauthorized geofence use cases.
- Evaluate alert conditions from the canonical derived-event and table-timer foundations that already exist in the backend.
- Persist alert instances, lifecycle state, user actions, and notification-delivery attempts in durable backend storage.
- Deliver an Alerts Center experience inside the existing web shell for list, detail, filter, acknowledge, and resolve workflows.
- Expose unresolved-alert access in the shared shell without forcing an Operations Overview redesign in the same change.
- Keep the first alerting rollout small enough to validate operational behavior before health-alert and analytics work expand the model.

**Non-Goals:**

- Maintenance alerts such as gateway-offline or battery-drop notifications.
- Analytics reports, SLA trend dashboards, or Overview KPI redesign.
- Generic no-code rule expressions or arbitrary Boolean rule composition.
- Escalation ownership, assignment workflows, paging integrations, or mobile alert UX.
- Premium-tier alert semantics or historical backfill of alerts from preexisting derived events.

## Decisions

### 1. Use a typed rule model for the first rollout instead of a generic expression engine

The first alerting change should optimize for clear product behavior, not a fully general rules DSL. The backend should support explicit rule types for:

- `table_sla`
- `unauthorized_geofence`

Each rule type can have a small, typed configuration surface such as area scope, threshold seconds, channel preferences, and enablement.

Alternatives considered:

- Generic expression builder over all event fields: rejected because it adds parser, validation, UX, and debugging complexity before the first two alert types are proven.
- Hard-code alerts with no rule records: rejected because the change explicitly includes rule configuration and the later platform needs a durable rule model.

### 2. Evaluate alerts from derived operational state, not directly from raw telemetry or web clients

Alert generation should run downstream of the accepted positioning and derived-event layer so every consumer uses the same zone-entry, dwell, and table-timer semantics. Table SLA alerts should evaluate from the current table timer snapshots. Unauthorized geofence alerts should evaluate from canonical zone-transition history plus current spatial metadata such as `alert_participation` and restricted-zone typing.

Alternatives considered:

- Evaluate from raw MQTT messages: rejected because it would duplicate positioning and zone semantics.
- Evaluate from browser state: rejected because web clients are not durable system-of-record inputs.

### 3. Persist alert rules, alert instances, action history, and delivery attempts as separate concerns

The system needs different durable records for different jobs:

- alert rules: configuration and channel preferences
- alert instances: active and historical alert occurrences
- action history: acknowledgement and resolution trail with actor context
- notification deliveries: in-app or email delivery attempt records

Separating those concerns keeps backend query paths straightforward and prevents rule edits or action history from being encoded into one overloaded alert table.

Alternatives considered:

- Single alerts table with embedded JSON for actions and deliveries: rejected because triage history and delivery-state querying become harder to reason about.
- Delivery state only in external providers: rejected because the Alerts Center needs a local, durable view of what happened even when email is optional or unavailable.

### 4. Deduplicate active alerts by rule and operational scope

The engine should avoid creating an unbounded stream of identical active alerts while the same condition remains unresolved. A table SLA rule should keep one active alert per rule and table scope until the condition clears or the alert is resolved according to the lifecycle policy. An unauthorized geofence rule should do the same for the chosen scope of asset, area, and triggering transition.

Alternatives considered:

- New alert row for every matching poll or repeated event: rejected because the queue would become noisy and operationally unusable.
- No historical record after resolution: rejected because later audit and alert-history workflows need durable prior instances.

### 5. Deliver in-app notifications first-class and keep email optional and adapter-based

In-app notification delivery should always be backed by durable backend records that the web shell can query for unread or unresolved state. Email delivery should be optional per rule and only attempted when outbound email settings are configured. The design should treat email as best-effort delivery with recorded attempts, not as the sole source of truth for alert presence.

Alternatives considered:

- Require email infrastructure for alerting to work: rejected because the product requirement is optional email delivery.
- Skip delivery records and rely only on alert instances: rejected because channel behavior and later troubleshooting need separate delivery outcomes.

### 6. Deliver Alerts Center inside the existing shell and keep Overview changes minimal

The current shell already has the right shape for another delivered monitoring route. This change should add Alerts Center navigation and unresolved-alert access in the shell, but it should not redesign the existing Operations Overview cards and triage logic in the same pass.

Alternatives considered:

- Rebuild Overview and shell together around alerts: rejected because it widens scope beyond the backlog slice.
- Deliver alert APIs without a dedicated web route: rejected because the change explicitly includes Alerts Center UI.

## Risks / Trade-offs

- [Inline alert evaluation adds write-path complexity to derived-event processing] -> Mitigation: keep the first rollout limited to two typed rule kinds and use deduplication per rule and scope.
- [Email delivery without a dedicated background delivery service may have transient failures] -> Mitigation: treat email as optional, persist delivery attempts, and keep in-app alert state authoritative.
- [Source materials disagree on maintenance alerts] -> Mitigation: state explicitly in proposal, specs, and docs that maintenance alerts remain deferred to the later health and observability change.
- [Alert lifecycle semantics can drift if acknowledgement and resolution rules are vague] -> Mitigation: define explicit persisted states and user actions in the specs instead of leaving triage behavior implicit.

## Migration Plan

1. Add alert rule, alert instance, alert action, and delivery persistence alongside the existing derived-event baseline.
2. Add backend rule-management and alert-query contracts before wiring the web shell to them.
3. Extend the derived-event processing flow so delivered rule types can create or update alert instances from new operational signals.
4. Add the Alerts Center route and shell-level unresolved-alert access in the web application.
5. Start the alert engine in forward-only mode for new derived events and current timer state after deployment, without backfilling old alert history.

## Open Questions

- None at proposal stage. The remaining work is mostly implementation sequencing and keeping the first alerting rollout narrowly scoped.
