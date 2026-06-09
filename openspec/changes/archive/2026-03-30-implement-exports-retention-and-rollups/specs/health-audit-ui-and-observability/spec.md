## MODIFIED Requirements

### Requirement: Administrators can review infrastructure health in the web app
The RTLS Analytics Platform SHALL provide a protected administrator Health workspace that summarizes the current infrastructure health baseline using delivered gateway, alert, and ingestion state.

#### Scenario: Administrator opens the Health workspace
- **WHEN** an authenticated Administrator opens the delivered Health view in the admin area
- **THEN** the web app SHALL show a current health summary including stale-gateway, low-battery, alert-pressure, ingestion or metrics baseline context, and the latest lifecycle-run status

#### Scenario: Administrator triggers retention and rollup refresh
- **WHEN** an authenticated Administrator requests the delivered lifecycle action from Health
- **THEN** the system SHALL start a lifecycle run and surface its pending or completed state in the administrator Health workspace
