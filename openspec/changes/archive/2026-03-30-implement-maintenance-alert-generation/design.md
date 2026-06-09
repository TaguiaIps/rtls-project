## Context

The current platform already persists gateway heartbeats, computes stale and low-battery gateway risks, and renders alert instances through the Alerts Center. The missing behavior is the bridge between those health signals and the durable alert model: stale or low-battery conditions remain summary-only diagnostics rather than actionable maintenance alerts.

This change must close `NFR-REL-001` without introducing a second alerting system, without requiring a schema migration that would break existing local databases, and without turning system-generated maintenance rules into editable user-authored rules.

## Goals / Non-Goals

**Goals:**
- Generate durable maintenance alerts for stale and low-battery gateway conditions.
- Clear or refresh those alerts automatically as gateways recover or remain unhealthy.
- Reuse the existing alert timeline, unread delivery, acknowledgement, and resolution behavior.
- Keep maintenance alerts visible in the Alerts Center and alert summary endpoints.
- Preserve the current user-authored rule editor for SLA and unauthorized-geofence rules only.

**Non-Goals:**
- Add a new background scheduler or clustered reliability subsystem.
- Add configurable maintenance thresholds beyond the delivered battery and heartbeat settings.
- Implement the deferred Operations Overview KPI expansion or true self-location mobile calibration work.

## Decisions

### Reuse alert rules and alert instances with system-managed maintenance rule types

The backend will introduce dedicated maintenance `AlertRuleType` values for stale and low-battery gateway conditions. Each scoped site or floor will use automatically ensured system-managed rules stored in the existing `alert_rules` table so the platform can continue to use the same alert-instance lifecycle, notification-delivery records, and triage actions.

Why this over a separate maintenance-incidents table:
- the Alerts Center, unread counts, and action timeline already depend on `AlertInstance`
- delivery and triage semantics stay uniform across operational and maintenance alerts
- no new UI surface is required to make the alerts actionable

### Use a hybrid synchronization strategy for gateway maintenance alerts

Low-battery alerts can be created or cleared directly during heartbeat ingestion because the triggering signal arrives with the heartbeat payload. Stale alerts are silence-driven, so they cannot rely on an incoming event at the moment the threshold is crossed.

The system will therefore:
- sync the reporting gateway's maintenance-alert state during heartbeat ingestion
- run a scoped maintenance-alert sweep before alert summary, alert list, alert detail, and observability summary responses

Why this over a new scheduler:
- it closes the requirement with the runtime primitives already present in the repository
- it avoids adding new infrastructure or worker loops
- the delivered Health and Alerts surfaces already refresh often enough to keep visible state aligned during active operations

### Keep system-managed maintenance rules out of the editable rules endpoint

The delivered rule-management UI is for user-authored SLA and geofence rules. Rather than add a new database column to mark system ownership, the backend will keep maintenance rules discoverable by alert instances but exclude their rule types from the rules listing and update flows used by the editor.

Why this over a schema change such as `system_managed`:
- existing local databases are created without migrations; adding a new column would not retrofit existing installations
- filtering by rule type is sufficient for the delivered UX and keeps the change low-risk

## Risks / Trade-offs

- [Stale alerts appear on the next scoped sweep rather than at the exact threshold-crossing millisecond] → Trigger sweeps from alert and health reads, which are the user-visible operational surfaces for this data.
- [System-managed rules are identified by reserved rule types rather than an explicit ownership column] → Reserve the new rule types from user-authored CRUD paths and document them as platform-managed.
- [More reads now perform scoped alert synchronization] → Keep the sweep bounded by optional site or floor scope and reuse indexed heartbeat and gateway tables.

## Migration Plan

1. Add the new maintenance alert rule types and synchronization helpers.
2. Invoke synchronization from heartbeat ingestion and alert or observability reads.
3. Update web alert filters and contracts to recognize maintenance alerts.
4. Add regression coverage for low-battery creation, stale-gateway sweeping, and recovery clearing.
5. Sync the modified baseline specs and archive the change.

Rollback: remove the maintenance sync calls and new rule types. Existing maintenance alert rows can remain as historical records because the alert model already supports cleared or resolved history safely.

## Open Questions

None for this delivered baseline. Future work can decide whether maintenance thresholds become user-configurable or scheduled independently of read traffic.
