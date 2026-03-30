## MODIFIED Requirements

### Requirement: Administrators can review infrastructure health in the web app
The RTLS Analytics Platform SHALL provide a protected administrator Health workspace that summarizes the current infrastructure health baseline using delivered gateway, alert, and ingestion state.

#### Scenario: Administrator opens the Health workspace
- **WHEN** an authenticated Administrator opens the delivered Health view in the admin area
- **THEN** the web app SHALL show a current health summary including stale-gateway, low-battery, alert-pressure, ingestion or metrics baseline context, the latest lifecycle-run status, and maintenance alerts synchronized from the current gateway-risk state

#### Scenario: General User attempts to open the Health workspace
- **WHEN** an authenticated General User requests the delivered admin Health workspace
- **THEN** the system SHALL deny access instead of rendering administrator health data

### Requirement: Administrators can review current gateway risks
The RTLS Analytics Platform SHALL let an authenticated Administrator inspect gateway risks derived from the latest-known heartbeat state.

#### Scenario: Stale or low-battery gateways exist
- **WHEN** the delivered health summary detects gateways with stale heartbeat state or low battery state
- **THEN** the administrator Health workspace SHALL present those gateway risks with enough floor and device context for follow-up and SHALL synchronize corresponding maintenance alerts into the delivered alert model
