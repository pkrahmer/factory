# <project>

<One sentence: what this repository is.> Built by the factory (github.com/pkrahmer/factory); the pipeline's rules reach every agent as a skill, so this file holds only what is true of this project.

## Language
- Everything in this repository is English: code, comments, docs, tickets, commit messages.

## Architecture
- <Layers, dependency direction, what is pure, where wiring happens.>
- <Typing and validation rules.>

## Tests
- <Framework; where tests live; fixtures; what may be faked and what may not.>

## Docs
- `README.md` is for the newcomer: what it is, how to run it, where to look next. `docs/api.md` holds what the schema cannot say (concepts, errors, examples); `docs/architecture.md` the layers and their reasons; `docs/decisions.md` lasting decisions. The documenter stage writes these from each story's docs criterion; the coder does not.
- `docs/openapi.json` is generated: `make openapi` writes it, a test fails when it is stale, and the coder runs the target after changing a route. Nobody edits it.
- Docstrings: one per module (its purpose, a sentence) and one per public class and function in <the packages that form the interface>; none on private names or where the signature says it all. Comments say why, never what. `ruff`'s `D` rules enforce the presence; the reviewer judges the content.

## Checks
- `make check` must be green before any stage reports done. It runs <tools: lint, types, sast (semgrep + bandit), secrets (detect-secrets), licenses (pip-licenses allow list), tests with coverage and, for an HTTP API, the schemathesis contract test>. `make lint` and `make test` run <subset>; the pipeline knows only these three targets.

## Not without asking (end the stage with `question`)
- New dependency, new top-level package, change to `factory/`, change to a test you did not write, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
