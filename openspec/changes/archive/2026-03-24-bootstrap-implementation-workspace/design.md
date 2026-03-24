## Context

The repository is currently documentation-first. It contains requirements, architecture direction, UX design, and generated prototypes, but no agreed implementation layout or local runtime baseline. Later changes in the implementation plan depend on a stable foundation for:

- backend and web application placement
- mobile baseline ownership
- shared contracts
- developer tooling
- containerized local infrastructure
- CI enforcement

User decisions for this change:

- Stack: FastAPI, React, Expo React Native
- Mobile baseline: there is no surviving `ips_app`, so the bootstrap change must create a new mobile baseline
- Local runtime: `web`, `api`, `worker`, `mqtt-broker`, `redis`, `timescaledb`, and `object-storage`
- Repo shape: `apps/` and `packages/`
- CI baseline: lint, tests, and build on every pull request
- Deployment posture: optimize for local development plus a first pilot server

The design must establish a foundation that is small enough for early implementation, but strong enough that later changes do not have to rework repo structure or local operations.

## Goals / Non-Goals

**Goals:**

- Create a canonical monorepo layout for backend, web, mobile, and shared packages.
- Create a new cross-platform mobile baseline that fits the shared workspace and tooling direction.
- Define a local Docker Compose stack that mirrors the first pilot deployment shape closely enough for realistic integration work.
- Standardize environment variable naming, local startup flow, and CI expectations.
- Keep the first runtime topology intentionally coarse so feature changes can proceed without premature microservice fragmentation.

**Non-Goals:**

- Implement production business features such as authentication, live positioning, alerts, or analytics.
- Finalize cloud-provider-specific infrastructure or production Kubernetes manifests.
- Commit to Kafka, service mesh, or other higher-complexity infrastructure before throughput justifies it.
- Define the complete mobile application feature set beyond keeping the current Flutter baseline in scope.

## Decisions

### 1. Use an `apps/` and `packages/` monorepo layout

The workspace should be organized as:

- `apps/api`
- `apps/web`
- `apps/mobile`
- `packages/contracts`
- `packages/config`
- optional later packages for shared tooling or SDKs

Rationale:

- It makes ownership boundaries obvious without scattering code across unrelated top-level folders.
- It supports the planned multi-application platform without forcing many repositories.
- It gives later OpenSpec changes a predictable target for backend, web, and mobile work.

Alternatives considered:

- Flat `backend/`, `web/`, `mobile/` layout: simpler at first, but weaker for shared packages and long-term workspace growth.
- Backend-only bootstrap: lower initial scope, but it would force a second restructuring once web and mobile implementation begins.

### 2. Keep the runtime topology coarse at first

The first implementation baseline should use:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Rationale:

- This is the minimum realistic topology that matches the architecture documents and the deployment strategy.
- A single `worker` is sufficient at bootstrap time and avoids premature runtime fragmentation.
- It still leaves clean expansion paths toward `worker-ingest`, `worker-positioning`, `worker-events`, and `worker-analytics`.

Alternatives considered:

- Split every service immediately: too much operational overhead for a repo with no implementation baseline.
- Minimal `api` plus database only: too detached from the actual RTLS pipeline to validate integration assumptions early.

### 3. Use Expo React Native for the new mobile baseline

The workspace should create a new Expo React Native application at `apps/mobile`.

Rationale:

- It removes the mismatch between the approved change and the actual repository, which no longer contains the old Flutter app.
- It aligns the mobile stack with the React web application and shared JavaScript tooling.
- It keeps cross-platform mobile delivery viable without introducing a second front-end language and toolchain.

Alternatives considered:

- Recreate Flutter immediately: viable, but it would add a separate UI language and tooling stack to a repo that currently has no mobile code.
- Exclude mobile from bootstrap: simpler short-term, but it would postpone a repo-level decision that later changes already depend on.

### 4. Standardize CI around lint, tests, and build

Every pull request should run the baseline quality gates relevant to the active applications and packages.

Rationale:

- The first implementation baseline should not allow unchecked drift in formatting, broken builds, or obvious contract breakage.
- Later feature changes should inherit quality gates instead of inventing them.

Alternatives considered:

- Lint-only CI: too weak for a multi-application workspace.
- No CI in bootstrap: guarantees later rework and inconsistent standards.

### 5. Align local development with the first pilot-server shape

The local runtime should optimize for development, but its service inventory and configuration model should remain compatible with a first pilot deployment on a small container host.

Rationale:

- It reduces drift between developer workflows and early deployed environments.
- It matches the agreed deployment posture: local development plus a first pilot server.
- It keeps configuration naming and container boundaries reusable.

Alternatives considered:

- Local-only shortcuts with a completely different topology: faster initially, but creates integration surprises later.
- Full Kubernetes from day one: too much complexity before a real implementation baseline exists.

## Risks / Trade-offs

- [Monorepo complexity for a repo with little code] → Mitigation: keep the initial package count low and create only the shared packages that are immediately justified.
- [The chosen mobile stack may be reconsidered later] → Mitigation: keep the bootstrap mobile baseline minimal and treat deeper mobile architecture decisions as later changes.
- [A single `worker` may become a bottleneck once real telemetry arrives] → Mitigation: define clean split points now and defer the actual split to later changes.
- [Local Compose may hide production orchestration concerns] → Mitigation: keep the deployment strategy explicit and treat Compose as the local and pilot baseline, not the final HA target.
- [CI setup may slow early iteration] → Mitigation: keep the baseline checks focused on lint, tests, and build only.

## Migration Plan

1. Create the monorepo structure and place backend, web, mobile, and shared packages under the agreed layout.
2. Introduce baseline tooling, environment files, and workspace commands.
3. Introduce the Docker Compose stack and service startup documentation.
4. Add CI workflows for lint, test, and build.
5. Validate that the workspace can be started locally and that later changes have clear entry points.

Rollback strategy:

- If the workspace structure proves too disruptive before implementation starts, revert the bootstrap change as a single foundation change rather than letting downstream feature changes depend on a partial baseline.

## Open Questions

- Which package manager and task runner should be used for the JavaScript workspace portion.
- Whether the backend worker should be a separate image from the start or the same image with different entrypoints.
- Whether Redis Streams is needed in the bootstrap change or only a plain Redis baseline is required initially.
- Whether the first CI setup should include container image builds or defer that to a later infrastructure-focused change.
