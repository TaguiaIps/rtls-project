SHELL := /bin/bash
PYTHON ?= python3
NPM ?= npm
UV ?= uv
VENV_DIR ?= .venv
VENV_ACTIVATE = source $(VENV_DIR)/bin/activate
UV_API_SYNC = $(VENV_ACTIVATE) && $(UV) sync --project apps/api --extra dev --active
UV_API_RUN = $(VENV_ACTIVATE) && $(UV) run --project apps/api --active

.PHONY: install api-install js-install lint test build format compose-up compose-down compose-reset bootstrap-admin certs

install: api-install js-install

api-install:
	$(UV) venv $(VENV_DIR)
	$(UV_API_SYNC)

js-install:
	$(NPM) install

lint:
	$(UV_API_RUN) python -m ruff check apps/api
	$(NPM) run lint

test:
	$(UV_API_RUN) python -m pytest apps/api/tests
	$(NPM) run test

build:
	$(UV_API_RUN) python -m build ./apps/api
	$(NPM) run build

format:
	$(UV_API_RUN) python -m ruff format apps/api
	$(NPM) run format

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

compose-reset:
	docker compose down -v --remove-orphans

certs:
	@mkdir -p ops/certs
	bash ops/certs/generate-certs.sh --all

bootstrap-admin:
	$(UV_API_RUN) python -m rtls_api.bootstrap_admin --email "$(EMAIL)" --password "$(PASSWORD)" --display-name "$(DISPLAY_NAME)"
