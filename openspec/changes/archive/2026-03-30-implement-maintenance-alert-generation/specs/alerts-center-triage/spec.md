## MODIFIED Requirements

### Requirement: Authorized users can review active and historical operational alerts
The RTLS Analytics Platform SHALL provide an Alerts Center where authorized users can review current and historical operational and maintenance alerts.

#### Scenario: User opens the active alert queue
- **WHEN** an authorized user opens the Alerts Center
- **THEN** the system SHALL return a filterable list of current alert instances with severity, type, age, scope, and status context, including maintenance alerts for gateway stale or low-battery conditions

#### Scenario: User filters or searches alert history
- **WHEN** an authorized user applies supported filters such as status, alert type, site, floor, severity, or time range
- **THEN** the Alerts Center SHALL reduce the visible alert list to the matching alert instances and history entries, including system-managed maintenance alert types

### Requirement: Alert detail exposes operational context and action history
The RTLS Analytics Platform SHALL present enough alert detail for later investigation and operational learning.

#### Scenario: User opens an alert detail view
- **WHEN** an authorized user inspects a single alert instance
- **THEN** the system SHALL show the affected asset or area context, triggering rule summary, delivery-channel context, timestamps, and prior persisted triage actions for that alert, including gateway context for maintenance alerts

#### Scenario: Alert has prior triage history
- **WHEN** an alert instance has been acknowledged, resolved, or otherwise acted on through supported workflows
- **THEN** the detail view SHALL expose those persisted actions in chronological order
