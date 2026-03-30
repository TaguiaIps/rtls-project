## Why

Gateway stale and low-battery conditions already appear in Health summaries, but they do not create durable maintenance alerts that operators can triage through the delivered Alerts Center. This leaves `NFR-REL-001` partially implemented even though the platform already has the heartbeat, health-risk, and alert-instance primitives needed to close the gap.

## What Changes

- Add system-managed maintenance alert generation for stale and low-battery gateway conditions.
- Reuse the delivered alert-instance, notification-delivery, and triage timeline model instead of introducing a parallel maintenance incident store.
- Sync gateway maintenance alert state from heartbeat ingestion and from scoped alert or health reads so stale gateways can open alerts even when silence is the triggering condition.
- Expose maintenance alerts in the delivered alert summary, queue, detail, and filter flows while keeping system-generated maintenance rules out of the editable user-authored rule management list.
- Update documentation and backlog mapping so deferred dashboard and mobile UX follow-on work stays separate from the completed maintenance-alert reliability requirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `alert-rules-and-notification-delivery`: add system-managed maintenance alert types derived from gateway heartbeat and battery health state.
- `alerts-center-triage`: include maintenance alerts in delivered alert queue, filtering, and triage detail.
- `health-audit-ui-and-observability`: synchronize gateway-risk state into durable maintenance alerts so Health and Alerts stay aligned on current infrastructure risk.

## Impact

- Backend: `apps/api/src/rtls_api/alerts.py`, `apps/api/src/rtls_api/alerts_api.py`, `apps/api/src/rtls_api/ingestion.py`, `apps/api/src/rtls_api/observability.py`, `apps/api/src/rtls_api/models.py`, and `apps/api/src/rtls_api/schemas.py`
- Shared contracts and web alert filters: `packages/contracts`, `apps/web/src/operations/AlertsCenter.tsx`
- Tests: backend alert, ingestion, and observability regression coverage
- Docs: requirements, UX, system-design, implementation-plan, and synced OpenSpec baseline specs
