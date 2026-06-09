## MODIFIED Requirements

### Requirement: Authorized users can open a shared protected monitoring shell
The RTLS Analytics Platform SHALL provide a shared protected web shell for the currently delivered monitoring routes that implements the "Command Rail" high-density layout and the "Deep Void" surface hierarchy.

#### Scenario: Authenticated General User opens the operations area
- **WHEN** an authenticated General User navigates to a delivered monitoring route
- **THEN** the web application SHALL render the shared operations shell with the "Command Rail" sidebar, role-appropriate navigation, and the "Deep Void" background surface hierarchy

#### Scenario: Authenticated Administrator opens a monitoring route
- **WHEN** an authenticated Administrator navigates to a delivered monitoring route
- **THEN** the web application SHALL render the same shared shell featuring the "Command Rail" layout while preserving access to administrator-only destinations
