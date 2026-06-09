## MODIFIED Requirements

### Requirement: Delivered alert rules generate durable alert instances from canonical operational signals
The RTLS Analytics Platform SHALL evaluate delivered alert rules from canonical derived-event, gateway-health, and table-timer signals and persist alert instances when a rule condition is matched.

#### Scenario: Table SLA rule is violated
- **WHEN** a delivered table SLA rule evaluates current timer state for an SLA-eligible table and the configured threshold is exceeded
- **THEN** the system SHALL create or maintain a durable alert instance for that rule and table scope

#### Scenario: Unauthorized geofence rule is matched
- **WHEN** a delivered unauthorized geofence rule evaluates canonical zone-transition history and a tracked asset enters or exits the configured restricted zone scope according to the rule settings
- **THEN** the system SHALL create or maintain a durable alert instance for that rule and operational scope

#### Scenario: Gateway heartbeat becomes stale
- **WHEN** gateway-health evaluation determines that a registered gateway has crossed the configured stale-heartbeat threshold
- **THEN** the system SHALL create or maintain a durable maintenance alert instance for that gateway scope

#### Scenario: Gateway battery drops below the delivered warning threshold
- **WHEN** gateway-health evaluation determines that a registered gateway battery level has dropped below the delivered maintenance warning threshold
- **THEN** the system SHALL create or maintain a durable maintenance alert instance for that gateway scope

#### Scenario: Matching condition repeats while the alert remains active
- **WHEN** additional evaluations or matching health or derived-event signals occur for the same active rule and operational scope before the alert is resolved or cleared
- **THEN** the system SHALL NOT create duplicate simultaneous active alerts for that same rule and scope

### Requirement: Alert delivery supports in-app notifications and optional email attempts
The RTLS Analytics Platform SHALL support durable in-app notification delivery for alert instances and optional email delivery attempts for rules that enable email.

#### Scenario: Delivered alert instance is created
- **WHEN** the system creates a new alert instance for a delivered rule, including a system-managed maintenance rule
- **THEN** the system SHALL persist an in-app notification record or equivalent durable unread alert signal that supported web workflows can query

#### Scenario: Rule enables email delivery and email delivery is configured
- **WHEN** a delivered rule enables email delivery and the runtime has outbound email delivery configured
- **THEN** the system SHALL attempt email delivery for the alert instance and persist the delivery outcome

#### Scenario: Rule enables email delivery but runtime email delivery is unavailable
- **WHEN** a delivered rule enables email delivery but outbound email delivery is not configured or an attempt fails
- **THEN** the system SHALL preserve the alert instance and in-app notification state without requiring successful email delivery

## ADDED Requirements

### Requirement: System-managed maintenance rules remain platform-owned
The RTLS Analytics Platform SHALL reserve maintenance alert rules for platform-managed gateway-health evaluation instead of treating them as user-authored editable rules.

#### Scenario: User requests editable alert rules
- **WHEN** an authorized user opens the delivered alert-rule management flow
- **THEN** the system SHALL return only user-authored delivered rule types that the UI can edit instead of exposing system-managed maintenance rules as editable configuration
