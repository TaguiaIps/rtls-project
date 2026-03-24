# Repository Guidelines

## Project Structure & Module Organization

This repository is an `apps/` + `packages/` monorepo.

- `apps/api`: FastAPI backend, SQLAlchemy models, auth, spatial APIs, and Python tests in `apps/api/tests`.
- `apps/web`: React + Vite dashboard. Admin and operations UI live in `apps/web/src`.
- `apps/mobile`: Expo React Native baseline for future mobile workflows.
- `packages/contracts`: shared TypeScript contracts used by web/mobile.
- `packages/config`: shared product/runtime constants.
- `docs`: requirements, UX, deployment, and workflow docs.
- `openspec`: change proposals, designs, tasks, and baseline specs.
- `ops`: local infrastructure config such as Mosquitto.

## Build, Test, and Development Commands

- Backend dependency manager: `uv`. The backend virtual environment lives at repo root in `.venv`.
- `uv venv`: create the backend virtual environment in `.venv`.
- `make install`: install Python and JS workspace dependencies.
- `make api-install` / `make js-install`: install only backend or JS workspace dependencies.
- `source .venv/bin/activate && uv sync --project apps/api --extra dev --active`: sync backend dependencies into the active `.venv`.
- `make compose-up` / `make compose-down`: start or stop the local Docker stack.
- `make bootstrap-admin EMAIL=admin@example.com PASSWORD=StrongPass123 DISPLAY_NAME="Platform Admin"`: create the first Administrator account.
- `make lint`, `make test`, `make build`: run the full repo quality baseline.
- `source .venv/bin/activate && uv run --project apps/api --active python -m pytest apps/api/tests`: run backend tests only.
- `source .venv/bin/activate && uv run --project apps/api --active python -m ruff check apps/api`: lint backend only.
- `source .venv/bin/activate && uv run --project apps/api --active python -m build ./apps/api`: verify the backend package builds cleanly.
- `npm run test --workspace @rtls/web`: run web tests only.
- Prefer targeted workspace commands before full-repo commands when the change is isolated.

## Coding Style & Naming Conventions

- Python: 4-space indentation, type hints, small focused modules, `snake_case` for functions/files.
- TypeScript/React: 2-space indentation, functional components, `PascalCase` for components, `camelCase` for variables/hooks.
- Use existing tools before hand-formatting: `ruff` for Python, `eslint` for JS/TS.
- Keep route handlers thin; business rules belong in reusable backend modules, not in request parsing code.
- Keep shared request/response shapes in `packages/contracts` when they are consumed by web or mobile.
- Keep API and UI copy aligned with repository terminology from `docs/` and `openspec/GLOSSARY.md`.

## Commenting Standards

- Write comments and docstrings in English.
- Comment intent, invariants, edge cases, or non-obvious behavior; do not narrate obvious code.
- Remove stale implementation-history comments when touching a file.

## Architecture Principles

- Keep presentation, business logic, persistence, and contracts in separate modules.
- Prefer API-first changes: update OpenSpec and shared contracts before spreading shape changes through apps.
- Reuse the spatial, auth, and audit foundations already in `apps/api` instead of re-encoding the same logic elsewhere.

## Testing Guidelines

- Backend uses `pytest`; web/mobile/packages use `vitest`.
- Add or update tests with each behavior change.
- Name tests `test_<feature>.py` for Python and `*.test.ts(x)` for TypeScript.
- Prefer integration-style API tests for backend routes and user-visible flow tests for React screens.
- When request/response models change, verify whether `packages/contracts` and related UI consumers must change too.

## Commit & Pull Request Guidelines

- Follow Conventional Commits seen in history: `feat(scope): ...`, `docs(scope): ...`, `chore(scope): ...`.
- Keep commits atomic and scoped to one concern.
- Avoid mixing backend, contracts, and frontend changes in one commit unless the feature genuinely spans those layers.
- PRs should include: purpose, impacted paths, validation run (`make test`, `npm run build`, etc.), linked OpenSpec change, and screenshots for UI changes.

## Git Workflow

- Prefer working from a branch, not directly on `main`, when the change is more than a trivial docs fix.
- Keep the worktree clean before starting a new OpenSpec change or archive step.
- Commit in small, reviewable units that match the implemented scope.
- Do not rewrite or discard user changes unless explicitly requested.
- Before pushing, rerun the relevant validation commands for the files you changed.

## OpenSpec & Configuration Notes

- Propose and implement changes through `openspec/changes/<change-name>/`.
- Copy `.env.example` to `.env`; never commit populated secrets.
- Do not use bare `pip install` for backend workflow changes; use `uv venv`, `uv sync`, and `uv run`.
- Raster floor plans currently support `PNG` and `JPG` only. CAD/PDF import is deferred by design.
- Archive completed changes only after tasks are fully checked and the related specs are synced when required.

## Review Guidelines

- Focus reviews on correctness, regressions, security, and maintainability.
- For backend changes, check auth, audit, and persistence boundaries.
- For frontend changes, check terminology consistency, protected-route behavior, and usability of admin/operations flows.
- For docs and OpenSpec changes, verify they match implemented behavior and do not drift from the approved scope.
