## MODIFIED Requirements

### Requirement: Authorized users can open the Analytics workspace
The RTLS Analytics Platform SHALL provide an Analytics workspace inside the protected monitoring shell for authorized General Users and Administrators.

#### Scenario: Authorized user opens the Analytics route
- **WHEN** an authorized user navigates to the delivered Analytics route with a supported site or floor context
- **THEN** the application SHALL render the Analytics workspace with a report switcher, parameter controls, export actions, and the preserved shell context

### Requirement: Analytics workflows communicate empty and degraded report states explicitly
The RTLS Analytics Platform SHALL distinguish empty historical results, sparse coverage, unsupported report requests, and export-job state inside the Analytics workspace.

#### Scenario: User queues an export from Analytics
- **WHEN** an authorized user requests an export for the current supported analytics scope
- **THEN** the workspace SHALL show the created export job in a recent-export queue with pending, completed, or failed state plus download access when ready
