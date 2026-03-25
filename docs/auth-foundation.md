# Identity, RBAC, and Audit Foundation

This document describes the first implementation of authentication, role-based access control, and audit-event persistence for the RTLS Analytics Platform.

## Scope

This change implements:

- local `email + password` authentication
- JWT access tokens
- refresh-token rotation
- two platform roles: `Administrator` and `General User`
- web login, logout, and role-aware routing
- persisted audit events for authentication lifecycle actions
- persisted audit events for configuration mutations available in the API baseline

This change intentionally does not implement:

- SSO or enterprise identity providers
- password reset
- MFA
- mobile authentication UX
- the full Audit Log review UI

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
- the created account is immediately usable through the normal login flow

## API Surface

Implemented endpoints:

- `POST /api/auth/token`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/me`
- `GET /api/admin/summary`
- `PATCH /api/admin/users/{user_id}`

Access model:

- `GET /api/me` requires any authenticated active user
- `/api/admin/*` routes require the `Administrator` role
- role enforcement happens in the API, not just in the web app

## Session Model

- access tokens are short-lived JWTs
- refresh tokens are rotated on use
- refresh-session records are stored in the operational database
- active refresh-token state is stored in Redis under the configured session prefix
- login audit records target the persisted refresh-session identifier created for that sign-in
- the web client serializes concurrent refresh retries so one expiring access token does not replay the same rotated refresh token
- logout revokes the active refresh session and clears the web session state
- logout rejects rotated or replayed refresh tokens instead of revoking the currently active session

## Audit Events

The API persists normalized audit records for:

- login success
- login failure
- refresh success
- refresh rejection
- logout
- logout rejection
- administrator-driven user updates
- Administrator bootstrap creation

Stored audit fields include:

- actor identity when known
- actor role when known
- action category
- action type
- target type and target identifier when applicable
- minimal structured details
- event timestamp

Secrets such as raw passwords and raw refresh tokens are never written into audit-event records.

## Environment Variables

Relevant auth settings in `.env`:

- `RTLS_WEB_ORIGIN`
- `RTLS_JWT_SECRET_KEY`
- `RTLS_JWT_ALGORITHM`
- `RTLS_ACCESS_TOKEN_TTL_MINUTES`
- `RTLS_REFRESH_TOKEN_TTL_DAYS`
- `RTLS_REFRESH_SESSION_KEY_PREFIX`

Use a non-default `RTLS_JWT_SECRET_KEY` outside local development.
