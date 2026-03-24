# Workspace Bootstrap Guide

This guide documents the first implementation baseline for the RTLS Analytics Platform.

It complements:

- [README.md](/home/hugo/Documents/taguia/rtls_project/README.md)
- [deployment-strategy.md](/home/hugo/Documents/taguia/rtls_project/docs/deployment-strategy.md)
- [implementation-plan.md](/home/hugo/Documents/taguia/rtls_project/docs/implementation-plan.md)

## 1. Workspace Layout

The bootstrap workspace uses an `apps/` and `packages/` layout:

- `apps/api`
  FastAPI application baseline and worker entrypoint.
- `apps/web`
  React and Vite baseline for the future Operations Overview and Live Map interfaces.
- `apps/mobile`
  Expo React Native baseline for the future Asset Finder and commissioning workflows.
- `packages/contracts`
  Shared JavaScript-side contract definitions.
- `packages/config`
  Shared JavaScript-side product and local runtime configuration.

## 2. Prerequisites

- Python `3.10+`
- `uv`
- Node.js `20+`
- Docker and Docker Compose

## 3. Environment Setup

Copy the template:

```bash
cp .env.example .env
```

The template defines:

- API host and port
- web origin and JWT auth settings
- TimescaleDB connection settings
- Redis connection URL
- MQTT broker host and port
- object storage endpoint and credentials
- object storage bucket and region
- local web and mobile API URLs

Do not commit a populated `.env` file.

## 4. Install Commands

Create the root virtual environment and install the backend and JavaScript workspace dependencies:

```bash
uv venv
make install
```

Useful individual commands:

```bash
make api-install
make js-install
make bootstrap-admin EMAIL=admin@example.com PASSWORD=StrongPass123 DISPLAY_NAME="Platform Admin"
```

Backend dependency management uses `uv` with a repository-root virtual environment at `.venv`.
The backend sync command is equivalent to:

```bash
source .venv/bin/activate
uv sync --project apps/api --extra dev --active
```

## 5. Local Runtime Commands

Start the full local runtime:

```bash
make compose-up
```

Stop the local runtime:

```bash
make compose-down
```

Reset containers and volumes:

```bash
make compose-reset
```

The runtime stack includes:

- `web`
- `api`
- `worker`
- `mqtt-broker`
- `redis`
- `timescaledb`
- `object-storage`

## 6. Verification Commands

Run the baseline validation commands:

```bash
make lint
make test
make build
```

These map to:

- Python `ruff`, `pytest`, and `build` through `uv run --project apps/api --active`
- JavaScript workspace `lint`, `test`, and `build` scripts

## 7. Expected Local Endpoints

- Web: `http://localhost:5173`
- API root: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- API auth token: `POST http://localhost:8000/api/auth/token`
- MinIO console: `http://localhost:9001`
- MQTT broker: `localhost:1883`
- TimescaleDB: `localhost:5432`
- Redis: `localhost:6379`

## 8. Identity Bootstrap

Before signing into the web application, create the first Administrator account:

```bash
make bootstrap-admin EMAIL=admin@example.com PASSWORD=StrongPass123 DISPLAY_NAME="Platform Admin"
```

This workflow intentionally lives outside the UI so the first privileged account is created through an explicit operator action.

## 9. Pilot Alignment

The local runtime uses the same service inventory intended for the first pilot deployment:

- coarse-grained `api` and `worker` services
- one MQTT broker
- one Redis instance
- one TimescaleDB instance
- one object storage service

This keeps local validation aligned with the deployment strategy without introducing Kubernetes or fine-grained worker splitting yet.

## 10. Spatial Admin Baseline

The current Administrator web workspace now includes the first spatial setup flow:

- create sites and floors
- upload one raster floor plan per floor
- confirm scale using two reference points and a measured real-world distance
- define polygonal `zone`, `table`, `restricted_zone`, and `poi` areas

Current limits are intentional:

- supported floor-plan formats are `PNG` and `JPG`
- coordinates are stored as normalized image-space points
- CAD/PDF parsing is deferred to a later change
- advanced map editing such as snapping, hole editing, and collaborative editing is deferred

See [spatial-admin-workflow.md](/home/hugo/Documents/taguia/rtls_project/docs/spatial-admin-workflow.md) for the step-by-step operator flow.
