## Context

The RTLS Analytics Platform now has a bootstrapped workspace, local runtime, and CI baseline, but it does not yet have any application identity model, protected routes, or persisted audit trail foundation. The requirements and system design already establish JWT authentication, role-based access control, and auditability as baseline platform behavior:

- `FR-SEC-001`: secure login using JWT
- `FR-SEC-002`: role-based access control
- `FR-SEC-003`: audit log for configuration changes

The UX design also assumes a login screen, role-based landing behavior, and later audit-log review flows. This change must establish the backend and web foundations now so the next admin and operations changes do not need to invent their own user identity patterns.

User decisions already fixed for this proposal:

- Authentication starts with local `email + password`
- The first Administrator is created through seed, environment, or CLI bootstrap
- This change implements backend auth plus the web login flow only
- Audit data is persisted now, but the full Audit Log UI remains deferred

The design therefore needs to stay small enough for an early implementation pass while still defining durable identity, session, and audit models.

## Goals / Non-Goals

**Goals:**

- Introduce a local user identity model with secure password storage and explicit Administrator versus General User roles.
- Introduce short-lived access tokens and refresh-token rotation aligned with the system design direction.
- Protect backend routes with role-aware authorization checks.
- Add the first web login and logout flow with role-based post-login routing.
- Persist audit events for authentication lifecycle events and for configuration mutations performed by authenticated users.
- Provide a repeatable, documented way to bootstrap the first Administrator account in local and pilot-style deployments.

**Non-Goals:**

- Implement SSO, OAuth provider integration, or enterprise identity federation in this change.
- Implement a complete user-management console, invite flow, password reset flow, or MFA.
- Implement the full Audit Log screen, filtering UI, or operational observability dashboard.
- Implement mobile authentication UX in this change.
- Finalize every future protected route; this change only establishes the shared enforcement model and protects the routes that exist now.

## Decisions

### 1. Use local credentials with an extensible internal user model

The platform will start with a first-party user table containing email, password hash, role, status, and audit metadata. Passwords should be stored with a modern adaptive hash, and the domain model should leave room for future identity-provider linkage without requiring a second user model later.

Rationale:

- It is the smallest secure path that works in local development, Docker Compose, and pilot deployments.
- It avoids blocking the roadmap on external identity-provider decisions.
- It still allows later SSO support by extending identity sources rather than replacing the core user entity.

Alternatives considered:

- External SSO from day one: stronger enterprise fit long-term, but too much scope and vendor coupling for the current stage.
- Temporary hard-coded users: faster superficially, but it would create immediate rework and undermine auditability.

### 2. Use JWT access tokens plus Redis-backed refresh session state

The API will issue short-lived access tokens and longer-lived refresh tokens. Refresh tokens should rotate on use, and the server should track active refresh sessions in Redis so logout, revocation, and replay detection remain possible without turning the API into a fully stateful session service.

Rationale:

- It matches the architecture direction already documented in `docs/system-design.md`.
- It keeps request authorization stateless for API access while preserving practical revocation control.
- It creates a reusable session model for later mobile and multi-device support.

Alternatives considered:

- Pure opaque server sessions: simpler revocation, but weaker fit for the planned API and WebSocket architecture.
- Non-rotating refresh tokens: smaller implementation effort, but weaker security posture and poorer auditability.

### 3. Keep authorization role-based and explicit in both backend and web shell

This change will support two roles only: `Administrator` and `General User`. Backend route guards remain authoritative, while the web application uses role-aware routing and shell behavior for navigation and post-login landing. UI hiding alone is not treated as authorization.

Rationale:

- It maps directly to the requirements and personas already defined in the repository.
- It keeps the permission model small enough for early implementation.
- It prevents later changes from scattering authorization assumptions across pages and handlers.

Alternatives considered:

- Fine-grained permission matrices now: potentially useful later, but premature for the current phase.
- Web-only route gating: insufficient because backend APIs still need authoritative enforcement.

### 4. Persist audit events now, but defer audit review UX

The platform will persist normalized audit events for authentication lifecycle events and for configuration mutations executed by authenticated users. Each event should capture actor identity, role, action type, target type, target identifier, timestamp, and minimal structured metadata. The UI for browsing the Audit Log remains a later change.

Rationale:

- It prevents later admin and observability work from retrofitting audit capture after sensitive actions already exist.
- It satisfies the governance direction without forcing the full log-review interface into this change.
- It creates a stable data contract that later Audit Log screens can query directly.

Alternatives considered:

- Actor context only, no persistence: smaller initial scope, but causes rework and lost historical fidelity.
- Full audit UI now: useful eventually, but it would pull too much observability scope into an identity foundation change.

### 5. Bootstrap the first Administrator outside the main UI

The first Administrator account should be created through a documented seed command, environment-driven bootstrap path, or equivalent CLI workflow. The login UI assumes an existing authorized user; it does not implement first-run account creation.

Rationale:

- It keeps the initial security boundary predictable.
- It avoids complex first-run onboarding state and edge cases.
- It fits local development and early pilot-server operations.

Alternatives considered:

- Self-serve first-user setup UI: more polished, but riskier and more complex at this stage.
- Hard-coded default admin credentials: unacceptable security posture even for early environments.

## Risks / Trade-offs

- [Local credentials add password-security responsibility to the platform] → Mitigation: use a modern password hash, document password handling rules, and keep the model extensible for future SSO.
- [Redis-backed refresh state adds operational coupling to authentication] → Mitigation: reuse the already-approved runtime stack and keep session state narrowly scoped to refresh-session management.
- [Persisted audit metadata could drift into over-collection] → Mitigation: record structured operational facts only, exclude secrets and raw credentials, and keep payloads minimal for LGPD-conscious handling.
- [Role model may need finer granularity later] → Mitigation: centralize authorization checks so a later permission model can extend the same enforcement points.
- [Audit UI is deferred] → Mitigation: ensure the event schema and storage model are queryable so the later Audit Log change is additive rather than a redesign.

## Migration Plan

1. Add user, refresh-session, and audit-event persistence models plus the corresponding backend services.
2. Add credential authentication, token issuance, token refresh, logout or revocation, and route-guard enforcement in the API.
3. Add Administrator bootstrap tooling for local and pilot-like deployments.
4. Add web login, logout, authenticated session bootstrap, and role-aware route entry.
5. Add audit-event writes for authentication lifecycle events and the configuration mutations available at implementation time.
6. Validate that docs, UX assumptions, and later implementation plan dependencies remain aligned.

Rollback strategy:

- If the implementation proves unstable, disable the new auth flows behind a single revert of this change rather than leaving partially protected routes or partial audit capture in place.
- If refresh-token rotation introduces issues, keep the user model and access-token verification but revert the refresh-session layer as one unit until corrected.

## Open Questions

- Which exact password-hashing library should be standardized in the backend implementation.
- Whether refresh tokens should be delivered via HTTP-only cookies for the web app or via explicit token payloads in the first implementation pass.
- Whether login failure rate limiting belongs in this change or the next security-hardening pass.
- Which configuration mutations will exist early enough to emit real audit events during this change beyond authentication lifecycle records.
