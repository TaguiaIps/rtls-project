# user-authentication Specification

## Purpose
TBD - created by archiving change implement-identity-rbac-and-audit-foundation. Update Purpose after archive.
## Requirements
### Requirement: Local credential authentication
The RTLS Analytics Platform SHALL authenticate platform users with local email-and-password credentials and issue JWT-based sessions for successful sign-in attempts.

#### Scenario: User signs in with valid credentials
- **WHEN** an active user submits a valid email and password to the authentication endpoint
- **THEN** the system SHALL return a valid access token and refresh token pair for that user session

#### Scenario: User sign-in fails
- **WHEN** a user submits invalid credentials or a disabled account attempts to sign in
- **THEN** the system SHALL reject the request without exposing whether the email or password caused the failure

### Requirement: Refresh session rotation and revocation
The RTLS Analytics Platform SHALL support refresh-token rotation and session revocation for authenticated users.

#### Scenario: Access token is refreshed
- **WHEN** a valid refresh token is presented to the refresh endpoint
- **THEN** the system SHALL issue a new access token and rotate the refresh token for the same authenticated session

#### Scenario: Refresh token is revoked or replayed
- **WHEN** a revoked, expired, or already-rotated refresh token is presented
- **THEN** the system SHALL reject the request and invalidate the affected refresh session

### Requirement: First Administrator bootstrap
The RTLS Analytics Platform SHALL provide a non-UI bootstrap path to create the first Administrator account for local and pilot-style deployments.

#### Scenario: First Administrator is initialized
- **WHEN** an operator runs the documented bootstrap workflow with valid administrator account inputs
- **THEN** the system SHALL create an Administrator account that can sign in through the standard authentication flow

#### Scenario: Duplicate bootstrap is attempted
- **WHEN** a bootstrap workflow attempts to create an Administrator account that conflicts with an existing account or bootstrap rule
- **THEN** the system SHALL reject the operation with a clear operational error

### Requirement: Web login entry point
The RTLS Analytics Platform SHALL provide a web login experience for authenticated entry into the platform.

#### Scenario: User opens the web application unauthenticated
- **WHEN** the user navigates to a protected web route without a valid authenticated session
- **THEN** the web application SHALL direct the user to the login screen before protected content is shown

#### Scenario: User signs out
- **WHEN** an authenticated user signs out from the web application
- **THEN** the system SHALL invalidate the active refresh session and clear the web application's authenticated state

