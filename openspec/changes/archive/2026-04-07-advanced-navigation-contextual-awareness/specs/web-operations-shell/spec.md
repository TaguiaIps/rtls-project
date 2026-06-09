## MODIFIED Requirements

### Requirement: The shell exposes shared operational context
The RTLS Analytics Platform SHALL surface shared operational context in the web shell so Overview and Live Map can stay aligned on the same site, floor, and live-feed status through an integrated "Live Feed Heartbeat" treatment.

#### Scenario: User loads the shell with an available operational context
- **WHEN** the web shell loads for an authorized user with accessible site and floor data
- **THEN** the shell SHALL expose the current site or floor context together with a visible live-feed status heartbeat animation in the Top Bar

#### Scenario: User changes site or floor context from the shell
- **WHEN** the user changes the current site or floor context from a shell control or deep link
- **THEN** the shell SHALL preserve that context and update the breadcrumb trail and heartbeat status accordingly
