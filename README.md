# RTLS Analytics Platform

Repository for the RTLS Analytics Platform, a documentation-first and now code-backed workspace for indoor real-time location intelligence focused on restaurants and large catering operations.

## Versioning

This repository follows Semantic Versioning for releases and tags, but it does not have an official release number yet because the project is still establishing its first implementation baseline.

- Versioning policy: [`VERSIONING.md`](./VERSIONING.md)
- Changelog: [`CHANGE.LOG`](./CHANGE.LOG)

## Workspace Structure

- `apps/api`: FastAPI baseline for the backend API and worker entrypoints
- `apps/web`: React and Vite baseline for the web dashboard
- `apps/mobile`: Expo React Native baseline for future mobile asset-finding and commissioning flows
- `packages/contracts`: shared runtime and contract definitions for the JavaScript workspaces
- `packages/config`: shared product and local-stack configuration for the JavaScript workspaces
- `docs/`: requirements, design, UX, planning, deployment, and prototype documentation
- `openspec/`: OpenSpec project context and change artifacts
- `ops/`: local infrastructure configuration such as the Mosquitto baseline

## Prerequisites

- Python `3.10+`
- `uv`
- Node.js `20.19+` or `22.12+`
- Docker with Compose support

## Getting Started

1. Copy the environment template.

   ```bash
   cp .env.example .env
   ```

2. Install backend and JavaScript workspace dependencies.

   ```bash
   uv venv
   make install
   ```

3. Bootstrap the first Administrator account.

   ```bash
   make bootstrap-admin EMAIL=admin@example.com PASSWORD=StrongPass123 DISPLAY_NAME="Platform Admin"
   ```

4. Start the local container stack.

   ```bash
   make compose-up
   ```

5. Run the quality baseline.

   ```bash
   make lint
   make test
   make build
   ```

6. Sign in and open the protected Admin setup workflow.
   - Web sign-in: `http://localhost:5173/login`
   - Admin workspace: `http://localhost:5173/admin`

## Local Services

The bootstrap Compose stack includes:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

Default URLs:

- Web: `http://localhost:5173`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- MinIO console: `http://localhost:9001`

## Key Documents

- Workspace setup: [`docs/workspace-bootstrap.md`](./docs/workspace-bootstrap.md)
- Auth foundation: [`docs/auth-foundation.md`](./docs/auth-foundation.md)
- Admin setup workflow: [`docs/spatial-admin-workflow.md`](./docs/spatial-admin-workflow.md)
- Deployment strategy: [`docs/deployment-strategy.md`](./docs/deployment-strategy.md)
- Implementation plan: [`docs/implementation-plan.md`](./docs/implementation-plan.md)
- UX specification: [`docs/ux-design.md`](./docs/ux-design.md)

## License

This project is copyrighted to Hugo de Paula and is not licensed for public use. Refer to the LICENSE file when it becomes available.
