# The contract between a repository and the factory is three targets: `check`, `lint`, `test`.
# `check` is the gate every stage must pass; `lint` and `test` are what the tests stage runs on
# its own (the type check is skipped there, because the modules under test do not exist yet).
# What each target runs is the repository's business; this file is a Python example.
.PHONY: check lint sast secrets licenses test mutants
.SILENT:

check: lint sast secrets licenses test
	echo "check: green"

lint:
	uv run ruff check --output-format=concise .
	uv run ruff format --check --quiet .
	echo "lint: green"

# Static analysis: semgrep with rule sets vendored under security/semgrep (copy the sets you
# want from github.com/semgrep/semgrep-rules; offline and pinned), plus bandit.
sast:
	SEMGREP_SEND_METRICS=off uv run semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error src
	uv run bandit -q -c pyproject.toml -r src
	echo "sast: green"

# Secrets beyond the reviewed baseline (`uv run detect-secrets scan > .secrets.baseline` once).
secrets:
	uv run detect-secrets-hook --baseline .secrets.baseline $$(git ls-files | grep -vE '^(uv\.lock|\.secrets\.baseline)$$')
	echo "secrets: green"  # pragma: allowlist secret (the word, not a key)

# Licences of the production dependencies against an allow list.
ALLOWED_LICENSES = MIT;MIT License;MIT-0;BSD;BSD License;BSD-2-Clause;BSD-3-Clause;3-Clause BSD License;ISC;ISC License;Apache-2.0;Apache 2.0;Apache Software License;PSF-2.0;Python Software Foundation License;MPL-2.0;Mozilla Public License 2.0 (MPL 2.0)
licenses:
	uv export -q --frozen --no-dev --no-emit-project --format requirements-txt -o .licenses-requirements.txt
	uv run pip-licenses --from=mixed --allow-only="$(ALLOWED_LICENSES)" \
	  --packages $$(sed -n 's/^\([A-Za-z0-9_.-]*\)==.*/\1/p' .licenses-requirements.txt) > /dev/null
	rm -f .licenses-requirements.txt
	echo "licenses: green"

# Tests, with the API contract test among them when the project has an HTTP API: a schemathesis
# test that holds every endpoint to the published OpenAPI schema (see the reference repository).
test:
	uv run pytest -q --no-header --tb=short
	echo "test: green"

# Optional, outside the gate: how well the tests notice a broken line (mutmut as a dev
# dependency, configured under [tool.mutmut] in pyproject.toml). Run it for the number. Leave a
# property-based test (the API contract test) out of it (`pytest_add_cli_args = ["--ignore=…"]`):
# under a mutant it shrinks the failure it found until mutmut's CPU limit ends the run, and the
# kill is counted as a timeout.
mutants:
	rm -rf mutants
	# Its progress is a spinner on one line; keep only the final counts, and the exit status.
	uv run mutmut run > .mutmut.log 2>&1; status=$$?; tr '\r' '\n' < .mutmut.log | tail -2; rm -f .mutmut.log; exit $$status
	uv run mutmut results
