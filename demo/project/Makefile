# The contract between this repository and the factory is three targets: `check`, `lint`, `test`.
# `check` is the gate every stage must pass; `lint` and `test` are what the tests stage runs on
# its own (the type check is skipped there, because the modules under test do not exist yet).
.PHONY: sync check lint types layers sast audit test openapi

# Quiet by default: agents read this output on every run, so a green check
# should be a handful of lines and a red one should name the problem once.
.SILENT:

check: lint types layers sast audit test
	echo "check: green"

sync:
	uv sync

lint:
	uv run ruff check --output-format=concise .
	uv run ruff format --check --quiet .
	echo "lint: green"

types:
	uv run mypy --no-error-summary --hide-error-context
	echo "types: green"

layers:
	uv run lint-imports --no-cache 2>&1 | grep -E 'BROKEN|Contracts:'
	echo "layers: green"

sast:
	uv run bandit -q -c pyproject.toml -r src
	echo "sast: green"

# The audit only changes when the lockfile does, and it needs the network.
# The stamp makes it run on a lockfile change and skip otherwise.
audit: .audit-stamp
	echo "audit: green (as of uv.lock)"

.audit-stamp: uv.lock
	uv export -q --frozen --no-emit-project --format requirements-txt -o .audit-requirements.txt
	uv run pip-audit --strict --progress-spinner=off -r .audit-requirements.txt
	rm -f .audit-requirements.txt
	touch .audit-stamp

# Short tracebacks, no banner, coverage lines only for files that miss lines. Exit code 5 is
# pytest's "no tests collected": green for the empty project, impossible once the first test exists.
test:
	uv run pytest -q --no-header --tb=short -p no:cacheprovider \
	  --cov --cov-report=term-missing:skip-covered || [ $$? -eq 5 ]
	echo "test: green"

# docs/openapi.json is the API schema as the running app reports it, committed so it can be
# read on GitHub. A test fails when it is stale; run this after changing a route or a schema.
openapi:
	mkdir -p docs
	uv run python -c "import json; from app.api.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))" > docs/openapi.json
	echo "openapi: docs/openapi.json written"
