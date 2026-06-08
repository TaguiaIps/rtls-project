# web-operations-shell Specification

## ADDED Requirements

### Requirement: The shell exposes delivered alert access
The RTLS Analytics Platform SHALL expose delivered alert access points in the shared operations shell once the Alerts Center is available.

#### Scenario: Authorized user views shell navigation after Alerts Center delivery
- **WHEN** an authenticated Administrator or General User opens the shared operations shell after the Alerts Center route is delivered
- **THEN** the shell SHALL expose an Alerts destination alongside the other delivered monitoring routes

#### Scenario: User has unresolved alerts in the current monitoring experience
- **WHEN** the shell can query unresolved or unread in-app alert state for the current user
- **THEN** the shell SHALL expose a visible unresolved-alert indicator or access point without requiring the user to discover alerts only through a deep link
