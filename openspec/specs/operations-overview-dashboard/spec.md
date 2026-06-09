# operations-overview-dashboard Specification

## Purpose
The Operations Overview dashboard provides a high-level summary of the live operational state, including active assets, infrastructure health, alerts, and SLA performance, serving as the primary landing page for monitoring.

## Requirements
### Requirement: Authorized users can open an Operations Overview landing screen
The RTLS Analytics Platform SHALL provide an Operations Overview landing screen for authorized operations and administrator users.

#### Scenario: User signs in to the monitoring experience
- **WHEN** an authorized user opens the Operations Overview
- **THEN** the screen SHALL summarize the current live operational state for the active site or floor instead of redirecting the user to a blank placeholder page

### Requirement: The overview triage surface summarizes available operational signals
The RTLS Analytics Platform SHALL summarize operational state using live-location, infrastructure-health, active-alert, and SLA performance signals.

#### Scenario: Overview data is available
- **WHEN** the overview loads with all supported operational signals
- **THEN** the screen SHALL show KPI-style summary values for active assets, infrastructure health, active alerts, and SLA performance together with a prioritized triage list

#### Scenario: Overview data is partially degraded or empty
- **WHEN** the overview lacks specific signal feeds (e.g., alerts or SLA events)
- **THEN** the affected KPI cards SHALL show an explicit "No Data" or degraded state instead of implying zero or healthy status

### Requirement: The overview summarizes active operational alerts
The RTLS Analytics Platform SHALL include an Alert KPI section on the Operations Overview that summarizes the current state of active alerts for the selected site or floor.

#### Scenario: Active alerts are present
- **WHEN** the Operations Overview loads and there are active alerts in the system
- **THEN** the dashboard SHALL display KPI cards for "Total Active Alerts", "Critical Alerts", and "Warning Alerts" with current counts

#### Scenario: No active alerts
- **WHEN** the Operations Overview loads and there are no active alerts
- **THEN** the Alert KPI cards SHALL show zero counts with a "Healthy" visual state

### Requirement: The overview summarizes SLA performance and trends
The RTLS Analytics Platform SHALL include an SLA KPI section on the Operations Overview that summarizes table/zone SLA performance and trends for the current monitoring window.

#### Scenario: SLA data is available
- **WHEN** the Operations Overview loads with available SLA performance data
- **THEN** the dashboard SHALL display KPI cards for "SLA Breach Count" and "SLA Success Rate %" for the current period

#### Scenario: SLA trend visualization
- **WHEN** the current Monitoring Window has a preceding comparison period
- **THEN** the SLA KPI cards SHALL include a trend indicator (e.g., +2%, -5%) comparing current performance to the previous window

### Requirement: KPI cards support direct functional drilldowns
The RTLS Analytics Platform SHALL allow users to drill down from Operations Overview KPI cards into the corresponding detailed views in the Alerts Center or Analytics workspace.

#### Scenario: User drills into Critical Alerts
- **WHEN** the user clicks on the "Critical Alerts" KPI card
- **THEN** the application SHALL navigate to the Alerts Center with the "Critical" priority and current site/floor filters automatically applied

#### Scenario: User drills into SLA Breaches
- **WHEN** the user clicks on the "SLA Breach Count" KPI card
- **THEN** the application SHALL navigate to the Analytics SLA report with the current timeframe and site/floor context preserved

### Requirement: The overview includes a floor-linked live map preview
The RTLS Analytics Platform SHALL provide a floor-linked live map preview on the Operations Overview so users can drill into the Live Map with preserved context.

#### Scenario: User opens the map preview call to action
- **WHEN** the user activates the Overview map preview drill-in
- **THEN** the application SHALL open the Live Map with the corresponding site or floor context preserved
