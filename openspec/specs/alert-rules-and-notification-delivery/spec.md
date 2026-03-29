# alert-rules-and-notification-delivery Specification

## Purpose
TBD - created by archiving change implement-alert-rules-and-alerts-center. Update Purpose after archive.
## Requirements
### Requirement: Authorized users can manage delivered operational alert rules
The RTLS Analytics Platform SHALL allow authorized users to create, update, enable, disable, and review alert rules for the delivered operational alert types.

#### Scenario: Authorized user creates a table SLA rule
- **WHEN** an authorized user configures a rule for an SLA-eligible table scope with a threshold and supported delivery channels
- **THEN** the system SHALL persist the rule as an enabled or disabled alert rule that later alert evaluation can consume

#### Scenario: Authorized user updates or disables a delivered rule
- **WHEN** an authorized user changes the configuration or enabled state of an existing delivered alert rule
- **THEN** the system SHALL persist the updated rule without requiring changes to the underlying derived-event model

### Requirement: Delivered alert rules generate durable alert instances from canonical operational signals
The RTLS Analytics Platform SHALL evaluate delivered alert rules from canonical derived-event and table-timer signals and persist alert instances when a rule condition is matched.

#### Scenario: Table SLA rule is violated
- **WHEN** a delivered table SLA rule evaluates current timer state for an SLA-eligible table and the configured threshold is exceeded
- **THEN** the system SHALL create or maintain a durable alert instance for that rule and table scope

#### Scenario: Unauthorized geofence rule is matched
- **WHEN** a delivered unauthorized geofence rule evaluates canonical zone-transition history and a tracked asset enters or exits the configured restricted zone scope according to the rule settings
- **THEN** the system SHALL create or maintain a durable alert instance for that rule and operational scope

#### Scenario: Matching condition repeats while the alert remains active
- **WHEN** additional evaluations or matching derived events occur for the same active rule and operational scope before the alert is resolved or cleared
- **THEN** the system SHALL NOT create duplicate simultaneous active alerts for that same rule and scope

### Requirement: Alert delivery supports in-app notifications and optional email attempts
The RTLS Analytics Platform SHALL support durable in-app notification delivery for alert instances and optional email delivery attempts for rules that enable email.

#### Scenario: Delivered alert instance is created
- **WHEN** the system creates a new alert instance for a delivered rule
- **THEN** the system SHALL persist an in-app notification record or equivalent durable unread alert signal that supported web workflows can query

#### Scenario: Rule enables email delivery and email delivery is configured
- **WHEN** a delivered rule enables email delivery and the runtime has outbound email delivery configured
- **THEN** the system SHALL attempt email delivery for the alert instance and persist the delivery outcome

#### Scenario: Rule enables email delivery but runtime email delivery is unavailable
- **WHEN** a delivered rule enables email delivery but outbound email delivery is not configured or an attempt fails
- **THEN** the system SHALL preserve the alert instance and in-app notification state without requiring successful email delivery

