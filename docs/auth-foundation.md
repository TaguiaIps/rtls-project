# Identity, RBAC, and Audit Foundation

This document describes the implemented authentication, role-based access control, and audit-event persistence for the RTLS Analytics Platform.

OpenSpec references: `user-authentication`, `role-based-access`, `audit-event-recording`.

## Scope

This implementation includes:

- local `email + password` authentication with JWT-based sessions
- refresh-token rotation and session revocation
- two platform roles: `Administrator` and `General User`
- backend route authorization and role-aware web routing
- protected web application shell with role-appropriate entry points
- web login experience with "Command" interaction standards (password visibility toggles, real-time validation, focus-responsive Cyan border)
- persisted audit events for authentication lifecycle actions and configuration mutations

This implementation intentionally does not include:

- SSO or enterprise identity providers
- password reset
- MFA
- mobile authentication UX
- the full Audit Log review UI (query filtering by actor, action type, target, and time range is supported at the data layer)

## Administrator Bootstrap

The first `Administrator` is created outside the main UI:

```bash
make bootstrap-admin EMAIL=admin@example.com PASSWORD=StrongPass123 DISPLAY_NAME="Platform Admin"
```

The command runs:

```bash
python3 -m rtls_api.bootstrap_admin --email ... --password ... --display-name ...
```

Bootstrap rules:

- the target email must not already exist
- the command fails if an `Administrator` account already exists
- the created account is immediately usable through the normal authentication flow

## API Surface

Implemented endpoints:

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/token` | Authenticates user with credentials, returns access and refresh tokens. |
| `POST` | `/api/auth/refresh` | Rotates refresh token and issues new access token pair. |
| `POST` | `/api/auth/logout` | Revokes active refresh session and clears authenticated state. |
| `GET` | `/api/me` | Returns current authenticated user context. |
| `GET` | `/api/admin/summary` | Returns administrator summary (Administrator only). |
| `PATCH` | `/api/admin/users/{user_id}` | Updates a user record (Administrator only). |

Access model:

- `GET /api/me` requires any authenticated active user
- `/api/admin/*` routes require the `Administrator` role
- role enforcement happens in the API, not just in the web app
- unsupported role values are treated as unauthorized

## Authorization Model

The two-role model (`Administrator`, `General User`) is enforced at two levels:

1. **Backend route authorization**: Protected backend routes check the authenticated user's role before processing the request. Administrator-only routes deny General User requests with an authorization error.

2. **Role-aware web routing**: After sign-in, the web application routes users to role-appropriate entry points:
   - Administrators are routed to the administrator setup/management area.
   - General Users are routed to the operations/analytics area.

3. **Protected web shell**: Navigation and page rendering is restricted to authenticated users with sufficient role access. Accessing a disallowed route prevents navigation and routes the user to an allowed destination or error state.

## Session Model

- access tokens are short-lived JWTs
- refresh tokens are rotated on use
- refresh-session records are stored in the operational database
- active refresh-token state is stored in Redis under the configured session prefix
- login audit records target the persisted refresh-session identifier created for that sign-in
- the web client serializes concurrent refresh retries so one expiring access token does not replay the same rotated refresh token
- logout revokes the active refresh session and clears the web session state
- logout rejects rotated or replayed refresh tokens instead of revoking the currently active session
- sign-in failures reject the request without exposing whether the email or password caused the failure

## Audit Events

The API persists normalized audit records for:

**Authentication lifecycle:**

- login success
- login failure
- refresh success
- refresh rejection
- logout
- logout rejection
- Administrator bootstrap creation

**Configuration mutations:**

- administrator-driven user updates
- site, floor, floor-plan, zone, gateway, and asset CRUD operations
- scale calibration updates
- CSV bulk import events
- alert rule creation and updates
- lifecycle run triggers

Stored audit fields include:

- actor identity when known
- actor role when known
- action category
- action type
- target type and target identifier when applicable
- minimal structured details
- event timestamp

Secrets such as raw passwords and raw refresh tokens are never written into audit-event records.

Audit events are persisted in a form that supports future filtering by actor, action category, target reference, and time window without redesigning the underlying record shape.

## Environment Variables

Relevant auth settings in `.env`:

- `RTLS_WEB_ORIGIN`
- `RTLS_JWT_SECRET_KEY`
- `RTLS_JWT_ALGORITHM`
- `RTLS_ACCESS_TOKEN_TTL_MINUTES`
- `RTLS_REFRESH_TOKEN_TTL_DAYS`
- `RTLS_REFRESH_SESSION_KEY_PREFIX`

Use a non-default `RTLS_JWT_SECRET_KEY` outside local development.
