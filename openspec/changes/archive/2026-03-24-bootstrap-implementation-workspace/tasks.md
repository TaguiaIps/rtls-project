## 1. Repository Foundation

- [x] 1.1 Define the canonical `apps/` and `packages/` workspace layout for backend, web, mobile, and shared code
- [x] 1.2 Create the mobile application baseline under the agreed workspace path
- [x] 1.3 Create the initial shared package locations for contracts and configuration
- [x] 1.4 Document workspace commands, dependency installation flow, and environment setup conventions

## 2. Application Baselines

- [x] 2.1 Scaffold the FastAPI backend baseline under the workspace layout
- [x] 2.2 Scaffold the React web baseline under the workspace layout
- [x] 2.3 Verify the mobile baseline can coexist with the backend and web applications in the shared workspace
- [x] 2.4 Add baseline lint, format, test, and build commands for each implemented application or package

## 3. Local Runtime Stack

- [x] 3.1 Create the Docker Compose stack for `web`, `api`, `worker`, `mqtt-broker`, `redis`, `timescaledb`, and `object-storage`
- [x] 3.2 Define environment variable templates and local secret-handling conventions for the runtime stack
- [x] 3.3 Document local startup, shutdown, reset, and verification steps for contributors
- [x] 3.4 Validate that the local stack shape remains compatible with the initial pilot-server deployment strategy

## 4. CI and Verification

- [x] 4.1 Add pull-request CI for lint, tests, and build validation across the workspace
- [x] 4.2 Verify that the workspace documentation, deployment strategy, and implementation plan remain consistent with the bootstrap decisions
- [x] 4.3 Record any follow-on decisions that must become later OpenSpec changes instead of being expanded inside the bootstrap change
