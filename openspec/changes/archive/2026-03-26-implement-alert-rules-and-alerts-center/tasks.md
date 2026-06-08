## 1. Alert Contracts And Scope

- [x] 1.1 Define the alert rule, alert instance, alert action, and notification-delivery contracts for the delivered alert types and triage workflows.
- [x] 1.2 Document the scope boundary between this change and the later health-alert and analytics changes, including the explicit deferral of maintenance alerts.

## 2. Backend Alert Foundation

- [x] 2.1 Add durable backend storage for alert rules, active and historical alert instances, user action history, and notification-delivery attempts.
- [x] 2.2 Implement protected backend rule-management and alert-query APIs for delivered alert types, queue filters, detail views, acknowledgement, and resolution actions.
- [x] 2.3 Extend derived-event processing so table SLA and unauthorized geofence conditions can create, deduplicate, and lifecycle-manage alert instances without reparsing raw telemetry.
- [x] 2.4 Record audit events for alert rule mutations and persisted triage actions.

## 3. Notification Delivery

- [x] 3.1 Implement in-app notification persistence and unread or unresolved alert summary queries for the web shell.
- [x] 3.2 Implement optional email-delivery integration and durable attempt tracking for rules that enable email delivery.
- [x] 3.3 Add backend regression coverage for rule validation, alert generation, deduplication, delivery behavior, and triage actions.

## 4. Web Alerts Center

- [x] 4.1 Extend the shared web operations shell with a delivered Alerts destination and unresolved-alert access point.
- [x] 4.2 Implement the Alerts Center route with list, filter, detail, acknowledgement, resolution, and rule-editing workflows that align with the delivered backend contracts.
- [x] 4.3 Add or update shared contracts and web tests for Alerts Center navigation, queue rendering, detail context, and user actions.

## 5. Documentation And Validation

- [x] 5.1 Update system and UX documentation to reflect the delivered alert-rule and Alerts Center scope, including the maintenance-alert deferral.
- [x] 5.2 Validate the change with `openspec validate implement-alert-rules-and-alerts-center --strict`.
