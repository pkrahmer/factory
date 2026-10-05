# To-do service

Single-user to-do service (FastAPI) built by the factory (github.com/pkrahmer/factory); the pipeline's rules reach every agent as a skill, so this file holds only what is true of this project. `factory/` holds this repository's stage table, the two forms and the features with their stories.

## Language
- Everything in this repository is English: code, comments, docs, tickets, commit messages.

## Architecture
- One package, `app`, under `src/`. Layers: `app.api` → `app.service` → `app.domain`; `app.repository` → `app.domain`. Wiring (choosing the concrete repository) happens in `app.api.main` only.
- `app.domain` imports nothing from the project and no framework (`fastapi`, `pydantic`, `sqlalchemy`), and does no I/O: frozen dataclasses, the domain errors, the repository protocol.
- `app.service` depends on the repository protocol only; it never imports `app.repository` or `app.api`.
- `app.repository` implements the domain protocol structurally (no inheritance) and imports nothing from `app.service` or `app.api`.
- `app.api` translates HTTP to service calls and maps domain errors to status codes in one place.
- Boundaries use Pydantic models; the core uses frozen dataclasses. No bare dicts across function boundaries.
- Type everything; `mypy --strict` is part of the checks. `Any` only at a boundary that Pydantic validates immediately.
- import-linter (`make check`) enforces the layer order for every layer that exists, including that `app.service` and `app.repository` never import each other; the framework-free domain is each story's criteria and tests.
- Before changing the architecture, read `docs/architecture.md` when it exists; lasting reasons are in `docs/decisions.md`.

## Tests
- pytest. Tests live under `tests/`, mirroring the layer (`tests/domain/`, `tests/service/`, `tests/api/`, `tests/repository/`), each folder a package with an `__init__.py`; a module outside the layers is tested at the `tests/` root.
- Plain test functions, shared fixtures in `tests/conftest.py`, parametrize for tables of cases. Fake the repository through its protocol, or use the in-memory repository once it exists; never mock the code under test.
- No network, no sleeps, no files outside `tmp_path`. HTTP is tested through FastAPI's `TestClient` (httpx) against `create_app`; no server process in tests.
- Security review for API stories: every endpoint validates body, query and path parameters through a schema; `bandit` and `pip-audit` are part of the checks.

## Docs
- `README.md` is for the newcomer: what it is, how to run it, where to look next. `docs/api.md` holds what the schema cannot say (title rules, error shape, filters, storage); `docs/architecture.md` the layers and their reasons; `docs/decisions.md` lasting decisions. The documenter stage writes these from each story's docs criterion; the coder does not.
- `docs/openapi.json` is generated: `make openapi` writes it from `app.api.main:app`, a test fails when it is stale, and the coder runs the target after changing a route or a schema. Nobody edits it.
- Docstrings: one per module (its purpose, a sentence) and one per public class and function in `app.domain` and `app.service`, which are the interface; `app.api`, `app.repository` and `__main__` need only the module docstring. None on private names. Comments say why, never what. `ruff`'s `D` rules (Google convention) enforce the presence; the reviewer judges the content.

## Checks
- `make check` must be green before any stage reports done. It runs ruff (including the docstring rules), mypy --strict, import-linter, bandit, pip-audit and pytest with coverage (90 % branch coverage of `src/app`). `make lint` and `make test` run the first and the last of these alone; the pipeline knows only these three targets. `make openapi` regenerates `docs/openapi.json`.
- Run Python through `uv run`. The dependencies for the whole to-do service are already in `pyproject.toml`: FastAPI, Pydantic, SQLAlchemy 2.0 (Core), uvicorn; httpx for the test client.

## Not without asking (end the stage with `question`)
- New dependency, new top-level package, change to `factory/`, change to a test you did not write.
