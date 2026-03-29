# web-operations-shell Specification

## Purpose
TBD - created by archiving change deliver-web-shell-operations-overview-and-live-map. Update Purpose after archive.
## Requirements
### Requirement: Authorized users can open a shared protected monitoring shell
The RTLS Analytics Platform SHALL provide a shared protected web shell for the currently delivered monitoring routes instead of rendering each monitoring page as an isolated screen.

#### Scenario: Authenticated General User opens the operations area
- **WHEN** an authenticated General User navigates to a delivered monitoring route
- **THEN** the web application SHALL render the shared operations shell with role-appropriate navigation and current-user context

#### Scenario: Authenticated Administrator opens a monitoring route
- **WHEN** an authenticated Administrator navigates to a delivered monitoring route
- **THEN** the web application SHALL render the same shared shell while preserving access to administrator-only destinations outside the operations area

### Requirement: The shell exposes shared operational context
The RTLS Analytics Platform SHALL surface shared operational context in the web shell so Overview and Live Map can stay aligned on the same site, floor, and live-feed status.

#### Scenario: User loads the shell with an available operational context
- **WHEN** the web shell loads for an authorized user with accessible site and floor data
- **THEN** the shell SHALL expose the current site or floor context together with a visible live-feed status treatment

#### Scenario: User changes site or floor context from the shell
- **WHEN** the user changes the current site or floor context from a shell control or deep link
- **THEN** the shell SHALL preserve that context across supported monitoring routes

### Requirement: The shell navigation is role-aware and delivery-aware
The RTLS Analytics Platform SHALL show only the destinations that are both permitted for the current user and delivered in the current product phase.

#### Scenario: General User views shell navigation
- **WHEN** a General User is signed in
- **THEN** the shell SHALL expose the delivered operations destinations without exposing administrator-only destinations

#### Scenario: A route is planned for a later backlog item
- **WHEN** a destination has not yet been delivered in the current product phase
- **THEN** the shell SHALL NOT present it as a working route in the primary navigation

### Requirement: The shell exposes delivered alert access
The RTLS Analytics Platform SHALL expose delivered alert access points in the shared operations shell once the Alerts Center is available.

#### Scenario: Authorized user views shell navigation after Alerts Center delivery
- **WHEN** an authenticated Administrator or General User opens the shared operations shell after the Alerts Center route is delivered
- **THEN** the shell SHALL expose an Alerts destination alongside the other delivered monitoring routes

#### Scenario: User has unresolved alerts in the current monitoring experience
- **WHEN** the shell can query unresolved or unread in-app alert state for the current user
- **THEN** the shell SHALL expose a visible unresolved-alert indicator or access point without requiring the user to discover alerts only through a deep link

### Requirement: The shell exposes delivered Analytics access
The RTLS Analytics Platform SHALL expose a delivered Analytics destination in the shared monitoring shell once the Analytics workspace route is available.

#### Scenario: Authorized user views shell navigation after Analytics delivery
- **WHEN** an authenticated General User or Administrator opens the shared monitoring shell after the Analytics workspace route is delivered
- **THEN** the shell SHALL expose an Analytics destination alongside the other delivered monitoring routes

#### Scenario: User navigates into Analytics from another monitoring route
- **WHEN** the user opens Analytics from Overview, Live Map, Alerts Center, or a deep link within the shared shell
- **THEN** the shell SHALL preserve the compatible site or floor context when handing off to the Analytics workspace
