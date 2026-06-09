## ADDED Requirements

### Requirement: Administrators can review infrastructure health in the web app
The RTLS Analytics Platform SHALL provide a protected administrator Health workspace that summarizes the current infrastructure health baseline using delivered gateway, alert, and ingestion state.

#### Scenario: Administrator opens the Health workspace
- **WHEN** an authenticated Administrator opens the delivered Health view in the admin area
- **THEN** the web app SHALL show a current health summary including stale-gateway, low-battery, alert-pressure, and ingestion or metrics baseline context

#### Scenario: General User attempts to open the Health workspace
- **WHEN** an authenticated General User requests the delivered admin Health workspace
- **THEN** the system SHALL deny access instead of rendering administrator health data

### Requirement: Administrators can review current gateway risks
The RTLS Analytics Platform SHALL let an authenticated Administrator inspect gateway risks derived from the latest-known heartbeat state.

#### Scenario: Stale or low-battery gateways exist
- **WHEN** the delivered health summary detects gateways with stale heartbeat state or low battery state
- **THEN** the administrator Health workspace SHALL present those gateway risks with enough floor and device context for follow-up

### Requirement: Administrators can review audit history through a filterable Audit Log
The RTLS Analytics Platform SHALL provide a protected administrator Audit Log that supports server-side filtering of persisted audit events.

#### Scenario: Administrator filters audit history
- **WHEN** an authenticated Administrator requests audit history with supported actor, category, action-type, target, or time filters
- **THEN** the system SHALL return the matching audit events ordered by newest first

#### Scenario: Administrator opens the Audit Log without filters
- **WHEN** an authenticated Administrator opens the delivered Audit Log without specifying filters
- **THEN** the system SHALL return a bounded recent audit-event list instead of an unbounded history dump

### Requirement: The platform exposes a minimal observability baseline
The RTLS Analytics Platform SHALL expose a minimal metrics and request-tracing baseline suitable for local operational verification.

#### Scenario: Operator queries the metrics endpoint
- **WHEN** an operator requests the delivered metrics endpoint
- **THEN** the system SHALL return a text-based metrics payload describing the current baseline operational counters and gauges

#### Scenario: Client makes an API request
- **WHEN** the platform handles an API request through the delivered backend
- **THEN** the response SHALL include a request identifier that operators can use for tracing and support follow-up
