# operations-overview-dashboard Specification

## ADDED Requirements

### Requirement: Authorized users can open an Operations Overview landing screen
The RTLS Analytics Platform SHALL provide an Operations Overview landing screen for authorized operations and administrator users.

#### Scenario: User signs in to the monitoring experience
- **WHEN** an authorized user opens the Operations Overview
- **THEN** the screen SHALL summarize the current live operational state for the active site or floor instead of redirecting the user to a blank placeholder page

### Requirement: The overview summarizes currently available operational signals
The RTLS Analytics Platform SHALL summarize operational state using live-location and infrastructure-health signals that are available in the current product phase.

#### Scenario: Overview data is available
- **WHEN** the overview loads with current live-location and operational-health data
- **THEN** the screen SHALL show KPI-style summary values and a short triage list derived from those current signals

#### Scenario: Overview data is partially degraded or empty
- **WHEN** the overview lacks live positions, receives stale feed status, or has no current priority items
- **THEN** the screen SHALL show an explicit empty or degraded state instead of implying healthy live coverage

### Requirement: The overview includes a floor-linked live map preview
The RTLS Analytics Platform SHALL provide a floor-linked live map preview on the Operations Overview so users can drill into the Live Map with preserved context.

#### Scenario: User opens the map preview call to action
- **WHEN** the user activates the Overview map preview drill-in
- **THEN** the application SHALL open the Live Map with the corresponding site or floor context preserved

### Requirement: The overview triage surface stays within current backlog scope
The RTLS Analytics Platform SHALL limit the Operations Overview to the operational signals delivered in the current product phase instead of depending on later alert-center or analytics capabilities.

#### Scenario: Later alerting or analytics capabilities are not yet delivered
- **WHEN** the current product phase does not yet include full alert-center or analytics behavior
- **THEN** the Overview SHALL remain usable by relying on delivered live-location and health data rather than blocking on those later capabilities
