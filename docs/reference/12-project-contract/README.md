# 12. The project contract

This chapter specifies the parts of the project contract that Part II left open: the control surface, the protected paths and the reader documentation, how a project is set up, and every place where v1's engine still knows what kind of project it builds.

## The concept

Three parts of the contract need more than [chapter 2](../02-concepts/README.md) said.

*The control surface* is a handful of named commands, and the factory reads nothing from them but the exit status and the tail of the output ([chapter 8](../08-stage-run/README.md)). Three properties make a surface usable:
- *A full check that contains the others.* The lint and the test run are the parts a stage may need alone; the full check runs them too, with everything else the project wants to hold.
- *Quiet output.* Agents read it in every turn that runs a command; green output should be a few lines, a red one should name the problem once.
- *Honest exit status.* Every tool's failure must reach the command's exit status. A pipe, a `|| true` or a filter that swallows it turns the check into a report that always says green.

**Protected paths** are the files that decide how the project is built and judged: the stage table, the forms, the guide, the build and check configuration, the dependency manifest. If an agent could change what the check judges, the check would judge nothing. No lane reaches them, whatever the project's lanes say. That covers the configuration wherever a tool looks for it, nested files and inline suppressions included, or the project names them on its list of things not to do without asking.

*The project guide's rules are enforced by the project's own checks* wherever a tool can do it: P10 applied inside the project. The guide says which check holds which rule, and leaves to the stories and the reviewer only what no tool can judge.

A project of another kind keeps the engine and the agents and changes only its side of the contract. As an illustration (v1 has built only the first kind):

| Kind | Stage table | Control surface | Guide and lanes |
| :- | :- | :- | :- |
| *Another language* | unchanged | the same names, the language's tools behind them | the language's layout and conventions |
| *A library* | a demonstration that runs examples instead of a service | adds an API compatibility check | the public interface named as such |
| *Infrastructure code* | a plan step whose output the human reads, and an apply after the gate | a validation that needs no credentials | modules, environments, what may never be applied |

The machine must also provide the project's toolchain; that is [chapter 14](../14-runtime/README.md)'s concern, and the limits below show what it costs in v1.

## In v1

### Setting up a project

The factory's [`README.md`](../../../README.md), *What a repository needs*, is the checklist. A project is ready when its main branch carries:

| Path | Started from | Owner | Read by |
| :- | :- | :- | :- |
| `factory/stages.yml` | [`template/stages.yml`](../../../template/stages.yml) | the human | the engine, the guard, the preflight ([chapter 5](../05-stage-machine/README.md)) |
| `factory/TICKET.md` | `template/` | the human | form validation ([chapter 4](../04-work-items/README.md)) |
| `factory/FEATURE.md` | `template/` | the human | nobody; the human copies it |
| `factory/features/…` | — | the human (drafts), the factory (state, archive) | the watcher ([chapter 6](../06-watcher/README.md)) |
| `CLAUDE.md` | [`template/CLAUDE.md`](../../../template/CLAUDE.md) | the human | every agent run, loaded by Claude Code from the checkout |
| `Makefile` with `check`, `lint`, `test` | [`template/Makefile`](../../../template/Makefile) | the human | the factory, the preflight, the agents |
| `pyproject.toml`, `uv.lock` | the project | the human | the entrypoint's `uv sync --frozen`, the agents' `uv run` |
| `.gitignore` | the project | the human | Git; see below |
| `README.md`, `docs/` | [`template/README.md`](../../../template/README.md) | the documenter's lane | the project's readers |

Plus a GitHub repository with the settings of [chapter 13](../13-git-and-github/README.md), and a container whose `REPOS` names it. The files are copied by hand; no command installs them. The entrypoint does not tick the repository until its main branch carries `factory/stages.yml`, and `uv sync --frozen` succeeds, which a lock file out of step with its manifest prevents ([chapter 14](../14-runtime/README.md)).

The `.gitignore` belongs to the contract, although no file names it. Everything the checks and the tools leave behind (`.venv/`, caches, `.audit-stamp`, `mutants/`) must be ignored: an untracked file on the main branch stops every tick with "working tree is dirty on main", and on a work item's branch it is committed with the stage's result.

The paths `factory/stages.yml` and `factory/TICKET.md` are fixed in the code (`watch.load_config`, `story.check_file`, `guard.CONFIG`, the preflight, the tick's stamp, the entrypoint). Only the features' folder is configurable, as `root:` in the stage table.

### The control surface

The factory calls `make <target>` in the checkout (`tick.make`) and logs the result as [chapter 8](../08-stage-run/README.md) describes.

| Target | Called by the factory | Called by agents | In the template | In the demonstration project |
| :- | :- | :- | :- | :- |
| `check` | `checks` after `doing` and `docs` | coder, documenter, acceptor | `lint sast secrets licenses test` | `lint types layers sast audit test` |
| `lint` | `checks` after `tests`; the preflight's probe | tester | ruff check and format check | the same |
| `test` | a report after `tests` (`records`) | tester, coder | pytest | pytest with branch coverage |
| `mutants` | never | the acceptor, if the project has the target ([chapter 11](../11-feature-acceptance/README.md)) | mutmut, outside `check` | the same |

Every other target reaches the factory only through `check`, which the factory never looks inside. Both Makefiles set `.SILENT:`, and every target `check` runs ends with `echo "<target>: green"`, so a green check logs as `` `make check`: check: green ``. The demonstration project's `test` accepts pytest's exit status 5, "no tests collected", so the empty project's first `make check` is green; once a test exists, 5 cannot occur. Its `audit` runs `pip-audit` only when `uv.lock` is newer than a stamp file, because it needs the network; a new advisory against an unchanged lock file is never reported.

### The template and its first instance

[`demo/project/`](../../../demo/project/) is the first project set up from the template: a single-user to-do service on FastAPI, Pydantic and SQLAlchemy, which the demonstration runs built. Its guide names the check behind each rule:

| The guide says | Held by |
| :- | :- |
| layers `app.api` → `app.service` → `app.domain`; `app.repository` → `app.domain`; service and repository never import each other | `make layers`: import-linter's layers contract in `pyproject.toml`, every layer optional so it holds from the first story on; but see the limits |
| `app.domain` imports no framework and does no I/O | each story's criteria and tests |
| type everything | `make types`: `mypy --strict` over `src` and `tests` |
| docstrings on the interface packages | ruff's `D` rules, Google convention, waived for `app.api`, `app.repository` and `__main__` |
| tests cover the code | 90% branch coverage of `src/app`, or `make test` fails |
| `docs/openapi.json` is generated, nobody edits it | a test that story F0001-S0003 requires fails when it is stale; `make openapi` writes the file, and the coder runs it after changing a route |
| bandit and pip-audit are part of the checks | `make sast`, `make audit` |

The template's `check` differs from the project's, because the template changed on 2026-10-05, after the project was set up:

| | Template | Demonstration project |
| :- | :- | :- |
| *Lint, tests* | ruff; pytest | ruff; pytest with 90% branch coverage |
| *Types, layers* | none | mypy `--strict`; import-linter |
| *SAST* | semgrep with rule sets vendored under `security/semgrep`, and bandit | bandit |
| *Dependencies* | a license allow list over the production dependencies (pip-licenses) | pip-audit for known vulnerabilities |
| *Secrets* | detect-secrets against a reviewed `.secrets.baseline` | none |
| *API conformance* | a schemathesis test, described in a comment | none |

The design decision of 2026-10-05 names the classes an enterprise stack covers, in shapes that run in seconds and offline, among them dependency analysis; the template's `check` has a license check but no vulnerability audit.

### Reader documentation

The template's README is written for the application's reader, who "has thirty seconds": what it is, *Getting started* (install, run, `make check`), *Using it* with runnable examples, *Where to look next* (`docs/api.md` for what the schema cannot say, `docs/architecture.md` for the layers and their reasons, `docs/decisions.md` for lasting decisions, `CLAUDE.md`), and the closing paragraph *How it is built*.

### Protected paths

`guard.py` holds three lists that no lane can reach, checked before the lane. [Chapter 8](../08-stage-run/README.md) applies them during and after the agent run (`stage._undo_out_of_lane` calls `guard.refusal`):

| List | Entries | Protects |
| :- | :- | :- |
| `NEVER_DIRS` (first path component) | `.claude` | the project's Claude Code settings, which could grant an agent permissions |
| `NEVER_FILES` (exact path from the root) | `pyproject.toml`, `uv.lock`, `Makefile`, `CLAUDE.md`, `factory/stages.yml`, `factory/TICKET.md` | the manifest, the lock file, the control surface, the guide, the stage table, the story form |
| `NEVER_NAMES` (file name anywhere) | `FEATURE.md` | every feature description, and the feature form with them |

A refusal reads "*path* is owned by the human; a change there is a question (R15)".

### Where the engine knows the project

| Assumption | Where |
| :- | :- |
| *The control surface is `make`* | `tick.make`; the preflight's tool list and its `make lint` probe; the shell tools `sh`, `grep`, `rm`, `touch` its recipes call (`preflight.SHELL_TOOLS`, which matches the demonstration project's Makefile; the template's also calls `sed`, `git`, `tr` and `tail`) |
| *The environment is `uv`* | the preflight requires `uv` and a `.venv` folder in the checkout; the entrypoint runs `uv sync --frozen` when `pyproject.toml` exists, once per container start; the allow list and the skills ([chapter 9](../09-agents-and-skills/README.md)) |
| *The language is Python* | `agent.AGENT_ENV` ([chapter 8](../08-stage-run/README.md)); the image is `python:3.12-slim-bookworm` |
| *The file names of Python, uv, make and Claude Code* | `guard.NEVER_FILES` |
| *The stage and role names* | [chapter 5](../05-stage-machine/README.md), *Names in the code* |

The factory's own README calls `uv` "the only tool assumption left"; the table shows it is not.

> [!WARNING]
> **v1 limit:** the project's toolchain is the factory's. Every check and every agent command runs inside the factory's container, so a project can use only what its image holds: Python 3.12, `uv` (which can fetch other Python versions), `make`, `git`, `gh` and `curl`. A project in Go or TypeScript needs a new image, and nothing in the contract declares which toolchain a project needs. A project without `pyproject.toml` gets no `uv sync`, so it has no `.venv`, and the preflight fails on every tick unless someone creates the folder by hand.

> [!WARNING]
> **v1 limit:** the protected paths belong to the engine, not to the project, and they stop at exact root paths. A project cannot add a path: a Go project's `go.mod` is protected only as long as no lane pattern reaches it. A nested `src/CLAUDE.md` is in the coder's lane, and Claude Code loads it as instructions for later agent runs that read files there; a subproject's `Makefile` or `pyproject.toml` in a monorepo is unprotected.

> [!WARNING]
> **v1 limit:** a check can be weakened from inside a lane. The tester's lane `tests/*` includes `tests/conftest.py`, whose pytest hooks can skip or deselect tests. The coder's lane `src/*` can hold a nested `ruff.toml`, which ruff prefers for the files beneath it. Inline `# noqa`, `# type: ignore` and `# pragma: no cover` work anywhere in a lane, and the template's guide asks about only `nosemgrep`, `nosec` and `pragma: allowlist secret`. Ignored files are outside the undo ([chapter 15](../15-safety/README.md)), so `touch .audit-stamp`, which every agent may run, skips the demonstration project's audit until the lock file changes. Only the reviewer's reading of the diff stands against any of these.

> [!WARNING]
> **v1 limit:** the demonstration project's layer rule is printed, not enforced. Its `layers` target pipes `lint-imports` into `grep -E 'BROKEN|Contracts:'`; `make` runs the recipe without `pipefail`, so the exit status is `grep`'s, and `grep` matches the summary line of a broken contract too. A domain module that imports the service layer prints "Layers BROKEN", then "layers: green", and `make check` stays green (verified on a copy of the project while this chapter was written).

> [!WARNING]
> **v1 limit:** the template does not run as shipped. Its `check` calls semgrep on `security/semgrep` and detect-secrets against `.secrets.baseline`, and the template ships neither; it ships no `pyproject.toml` that would declare its tools, and no `.gitignore`. Its README promises "lint, types, tests" and its Makefile's comment a type check, but its `check` has no type check; the schemathesis test it describes is not in it ("see the reference repository"). Its `secrets` target scans `git ls-files` only, while the factory runs a stage's checks before it commits, so a file the documenter has just created is not scanned. And `template/tasks/.gitkeep` is a leftover of the flat `tasks/` folder of generations 2 and 3.

> [!WARNING]
> **v1 limit:** nothing verifies a project's setup before the first story. A missing `check` target, or a main branch that fails it, first meets the coder, whose skill tells it to ask. A main branch that fails `make lint` fails the preflight's probe once the stamp is due, and the factory then stops for that repository, with a line in the tick log only ([chapter 14](../14-runtime/README.md)).

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - the control surface: named commands judged by exit status, a full check that contains the lint and the test run, quiet output whose tail is reported;
>   - protected paths no lane can reach: the stage table, the forms, the guide, the build and check configuration, the dependency manifest, wherever their tools look for them;
>   - the guide names the check that holds each of its rules, and the rest is left to criteria and review.
> - **Incidental to v1:** `make`, `uv`, the file names, the `echo "<target>: green"` convention, the tools behind each target, `factory/` as the folder.
> - **Watch for:**
>   - a check whose exit status is its tools'; test it by breaking each rule once and expecting red (v1's `layers` would fail that test);
>   - let the project declare its toolchain (an image, a devcontainer, a tool list) and its protected paths, with the engine's own files as a floor; treat nested configuration files, test hooks and inline suppressions as protected or as questions;
>   - the undo should cover ignored files the checks rely on (stamps, caches);
>   - a setup command that installs the contract's files and verifies them: every target exists, the full check is green on the main branch, `.gitignore` covers what the checks leave behind, the hosting service's settings are right ([chapter 13](../13-git-and-github/README.md));
>   - keep the template runnable: a fresh project from it must pass its own `check`;
>   - a check that needs the network belongs outside the stories' path, in the acceptance or a scheduled job.
