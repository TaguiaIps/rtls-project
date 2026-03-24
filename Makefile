PYTHON ?= python3
NPM ?= npm

.PHONY: install api-install js-install lint test build format compose-up compose-down compose-reset bootstrap-admin

install: api-install js-install

api-install:
	$(PYTHON) -m pip install -e ./apps/api[dev]

js-install:
	$(NPM) install

lint:
	$(PYTHON) -m ruff check apps/api
	$(NPM) run lint

test:
	$(PYTHON) -m pytest apps/api/tests
	$(NPM) run test

build:
	$(PYTHON) -m build ./apps/api
	$(NPM) run build

format:
	$(PYTHON) -m ruff format apps/api
	$(NPM) run format

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

compose-reset:
	docker compose down -v --remove-orphans

bootstrap-admin:
	$(PYTHON) -m rtls_api.bootstrap_admin --email "$(EMAIL)" --password "$(PASSWORD)" --display-name "$(DISPLAY_NAME)"
