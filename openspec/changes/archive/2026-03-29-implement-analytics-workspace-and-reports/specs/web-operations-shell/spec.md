## ADDED Requirements

### Requirement: The shell exposes delivered Analytics access
The RTLS Analytics Platform SHALL expose a delivered Analytics destination in the shared monitoring shell once the Analytics workspace route is available.

#### Scenario: Authorized user views shell navigation after Analytics delivery
- **WHEN** an authenticated General User or Administrator opens the shared monitoring shell after the Analytics workspace route is delivered
- **THEN** the shell SHALL expose an Analytics destination alongside the other delivered monitoring routes

#### Scenario: User navigates into Analytics from another monitoring route
- **WHEN** the user opens Analytics from Overview, Live Map, Alerts Center, or a deep link within the shared shell
- **THEN** the shell SHALL preserve the compatible site or floor context when handing off to the Analytics workspace
