## MODIFIED Requirements

### Requirement: Web login entry point
The RTLS Analytics Platform SHALL provide a web login experience for authenticated entry into the platform that implements the "Command" interaction standards, including password visibility toggles and real-time validation feedback.

#### Scenario: User opens the web application unauthenticated
- **WHEN** the user navigates to a protected web route without a valid authenticated session
- **THEN** the web application SHALL render a "Command" style login form with a focus-responsive Cyan border and password visibility toggle

#### Scenario: User signs out
- **WHEN** an authenticated user signs out from the web application
- **THEN** the system SHALL invalidate the active refresh session and clear the web application's authenticated state
