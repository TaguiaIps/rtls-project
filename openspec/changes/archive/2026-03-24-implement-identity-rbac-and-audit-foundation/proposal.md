## Why

The RTLS Analytics Platform now has an implementation workspace, but it still lacks the identity and authorization foundation required to protect admin setup flows, route users by role, and capture accountable configuration activity. This change is needed now because the next planned changes depend on authenticated users, enforceable Administrator versus General User boundaries, and persisted audit context rather than ad hoc placeholders.

## What Changes

- Add local email-and-password authentication for the RTLS Analytics Platform with JWT-based access and refresh token flows.
- Add the first web login experience and post-login role routing for Administrator and General User personas.
- Add role-based authorization rules that protect backend routes and role-aware web application areas.
- Add seeded or CLI-driven bootstrap creation for the first Administrator account in local and pilot-style environments.
- Add persisted audit event recording for authentication lifecycle events and future configuration mutations, while explicitly deferring the full Audit Log UI to a later change.
- Establish the shared identity, session, and audit foundations that later admin, operations, and observability changes will build on.

## Capabilities

### New Capabilities
- `user-authentication`: Covers local credential-based sign-in, JWT session issuance, refresh, revocation, and Administrator bootstrap setup.
- `role-based-access`: Covers Administrator and General User authorization rules, protected route behavior, and role-aware web routing.
- `audit-event-recording`: Covers persisted audit events for authentication and configuration actions with actor context for later Audit Log features.

### Modified Capabilities
- None.

## Impact

- Affects backend API design, session handling, password management, Redis-backed refresh token behavior, and protected route enforcement.
- Affects the React web application by introducing login, logout, authenticated shell entry, and role-aware route handling.
- Adds new persistence concerns for users, sessions, and audit events in the application database and cache.
- Provides the security and governance baseline needed by future changes for floor setup, gateway management, alerts, and observability.
- May require follow-on updates to implementation documentation once exact endpoint names, token claims, and seed workflows are finalized in code.
