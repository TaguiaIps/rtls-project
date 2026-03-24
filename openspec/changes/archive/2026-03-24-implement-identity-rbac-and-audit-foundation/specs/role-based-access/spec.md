## ADDED Requirements

### Requirement: Two-role authorization model
The RTLS Analytics Platform SHALL enforce a two-role authorization model with `Administrator` and `General User` roles.

#### Scenario: User role is attached to authenticated requests
- **WHEN** the system accepts a valid authenticated request
- **THEN** the request context SHALL include the authenticated user's role for downstream authorization decisions

#### Scenario: User account has an unsupported role value
- **WHEN** an authentication or authorization flow encounters an unsupported role assignment
- **THEN** the system SHALL deny access and treat the request as unauthorized

### Requirement: Backend route authorization
The RTLS Analytics Platform SHALL enforce role-based access checks on protected backend routes.

#### Scenario: Administrator accesses an administrator-only route
- **WHEN** an authenticated Administrator requests a route reserved for administrative actions
- **THEN** the system SHALL authorize the request if all other request validation passes

#### Scenario: General User accesses an administrator-only route
- **WHEN** an authenticated General User requests a route reserved for administrative actions
- **THEN** the system SHALL deny the request with an authorization error

### Requirement: Role-aware web routing
The RTLS Analytics Platform SHALL route authenticated web users to role-appropriate entry points after sign-in.

#### Scenario: Administrator completes login
- **WHEN** an Administrator successfully signs in through the web application
- **THEN** the web application SHALL route the user to the administrator-appropriate starting area for setup and system management

#### Scenario: General User completes login
- **WHEN** a General User successfully signs in through the web application
- **THEN** the web application SHALL route the user to the operations-appropriate starting area for monitoring and analytics

### Requirement: Protected web application shell
The RTLS Analytics Platform SHALL restrict protected web application navigation and page rendering to authenticated users with sufficient role access.

#### Scenario: Authenticated user opens an allowed area
- **WHEN** an authenticated user navigates to a web route permitted for their role
- **THEN** the web application SHALL render the requested protected area with role-aware navigation context

#### Scenario: Authenticated user opens a disallowed area
- **WHEN** an authenticated user navigates to a web route not permitted for their role
- **THEN** the web application SHALL prevent access and route the user to an allowed destination or authorization error state
