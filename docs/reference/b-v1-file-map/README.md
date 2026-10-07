# B. v1 file map

This appendix maps every file tracked on v1's main branch at commit `930c61a` to its purpose and to the chapters that explain it; a dash means no chapter does. Files that serve one purpose share a row. File names are not links, on purpose: in print every link becomes a footnote. Chapter 17's table *Documents that disagree with the code* names the files whose text is stale.

## The engine

| File | Purpose | Chapter |
| :- | :- | :- |
| `pyproject.toml` | The package, its six commands, ruff, mypy and pytest settings | [14](../14-runtime/README.md) |
| `uv.lock` | Pins the engine's dependencies for `uv run` (`make check`); the image's install does not use it | [14](../14-runtime/README.md) |
| `src/factory/__init__.py` | Empty; marks the package | — |
| `src/factory/agent.py` | Starts Claude Code headless for one agent run, the agent file passed as flags | [8](../08-stage-run/README.md), [15](../15-safety/README.md) |
| `src/factory/costs.py` | `factory-costs`: a work item's cost records, summed per agent | [10](../10-human-at-the-gate/README.md), [14](../14-runtime/README.md) |
| `src/factory/dispatch.py` | One handler per event, each ending in at most one commit and push | [5](../05-stage-machine/README.md), [7](../07-dispatcher/README.md) |
| `src/factory/github.py` | The pull request through the `gh` CLI; the marker on every post | [7](../07-dispatcher/README.md), [10](../10-human-at-the-gate/README.md) |
| `src/factory/guard.py` | `factory-guard`: refuses an agent's Edit and Write outside its lane or on a protected path | [8](../08-stage-run/README.md), [12](../12-project-contract/README.md), [15](../15-safety/README.md) |
| `src/factory/ops.py` | What the handlers share: context, work item edits, commit and push | [4](../04-work-items/README.md), [7](../07-dispatcher/README.md) |
| `src/factory/preflight.py` | `factory-preflight`: one `ok` or `missing` line per thing the loop needs | [14](../14-runtime/README.md) |
| `src/factory/repo.py` | The handlers' Git steps: branches, pulls, commits, pushes | [7](../07-dispatcher/README.md), [13](../13-git-and-github/README.md) |
| `src/factory/stage.py` | The stage protocol around one agent run, from the branch to the hand-over | [5](../05-stage-machine/README.md), [8](../08-stage-run/README.md), [11](../11-feature-acceptance/README.md) |
| `src/factory/story.py` | A work item as text: frontmatter, sections, numbered log; `factory-check-story` validates a story's form | [4](../04-work-items/README.md) |
| `src/factory/tick.py` | `factory-tick`: one tick, lock to handled event; runs the checks, writes cost records; state under `.git/` | [7](../07-dispatcher/README.md), [13](../13-git-and-github/README.md), [14](../14-runtime/README.md) |
| `src/factory/watch.py` | `factory-watch`: loads the stage table, prints the one next event, or the board | [6](../06-watcher/README.md) |
| `tests/test_*.py` (ten) | Tests with fakes for `gh` and the agent, and throwaway repositories | [16](../16-evidence/README.md) |

## Agents and instructions

| File | Purpose | Chapter |
| :- | :- | :- |
| `claude/agents/*.md` (seven) | Each stage agent: model, tools, effort, budget, skills and text; other keys have no effect | [8](../08-stage-run/README.md), [9](../09-agents-and-skills/README.md) |
| `claude/skills/factory-rules/SKILL.md` | The rules R1 to R15, preloaded into every agent | [9](../09-agents-and-skills/README.md) |
| `claude/skills/role-*/SKILL.md` (five) | How the acceptor, coder, documenter, reviewer and tester work and judge | [9](../09-agents-and-skills/README.md), [11](../11-feature-acceptance/README.md) |
| `claude/skills/stage-*/SKILL.md` (seven) | Each stage's steps, its log entry and its decisions | [9](../09-agents-and-skills/README.md), [11](../11-feature-acceptance/README.md) |
| `claude/settings.json` | The allow and deny lists for every agent | [9](../09-agents-and-skills/README.md), [15](../15-safety/README.md) |

## The machine

| File | Purpose | Chapter |
| :- | :- | :- |
| `Dockerfile` | The image: tools, `gh`, `uv`, Claude Code, the engine, agents and skills | [14](../14-runtime/README.md), [15](../15-safety/README.md) |
| `.dockerignore` | Keeps `.git/`, `.venv/` and `.env` out of the image | — |
| `compose.yml` | One service, `factory`, with its settings and two volumes | [14](../14-runtime/README.md) |
| `.env.example` | The container's settings: projects, token, commit identity | [14](../14-runtime/README.md) |
| `entrypoint.sh` | The scheduler: readies each project's checkout, clears stale locks at start, ticks the projects in turn | [14](../14-runtime/README.md), [15](../15-safety/README.md) |

## Templates

| File | Purpose | Chapter |
| :- | :- | :- |
| `template/stages.yml` | The stage table: stages, lanes, lease, attempts cap | [5](../05-stage-machine/README.md), [12](../12-project-contract/README.md) |
| `template/TICKET.md`, `template/FEATURE.md` | The story form and the feature form | [4](../04-work-items/README.md), [12](../12-project-contract/README.md) |
| `template/CLAUDE.md` | The project guide, as a skeleton | [9](../09-agents-and-skills/README.md), [12](../12-project-contract/README.md) |
| `template/Makefile` | The control surface, as a Python example | [12](../12-project-contract/README.md) |
| `template/README.md` | The project's README for readers, as a skeleton | [12](../12-project-contract/README.md) |
| `template/tasks/.gitkeep` | Unused: left from the flat `tasks/` folder of generations 2 and 3 | [12](../12-project-contract/README.md) |

## The demonstration

| File | Purpose | Chapter |
| :- | :- | :- |
| `demo/README.md` | The end-to-end demonstration, and its hardening mode | [16](../16-evidence/README.md) |
| `demo/features/**` (eleven) | Three features and their eight draft stories, ready to promote | [4](../04-work-items/README.md), [16](../16-evidence/README.md) |
| `demo/project/CLAUDE.md` | The demonstration project's guide | [12](../12-project-contract/README.md) |
| `demo/project/Makefile` | Its control surface: `check` (lint, types, layers, sast, audit, test), `openapi`, `mutants` | [12](../12-project-contract/README.md) |
| `demo/project/pyproject.toml`, `…/uv.lock` | Its dependencies, tool settings, layers contract; their lock | [12](../12-project-contract/README.md) |
| `demo/project/README.md` | Its README for readers, grown by the documenter | [12](../12-project-contract/README.md) |
| `demo/project/.gitignore`, `…/src/app/__init__.py`, `…/tests/__init__.py` | The empty start: ignored files, the package `app`, the test package | [12](../12-project-contract/README.md), [15](../15-safety/README.md) |
| `scripts/demo-check.sh` | The demonstration's prerequisites, one `ok`, `missing` or `note` line each | [13](../13-git-and-github/README.md), [16](../16-evidence/README.md) |

## Documents

| File | Purpose | Chapter |
| :- | :- | :- |
| `README.md` | Front page: trying it, running it, what a project needs | [12](../12-project-contract/README.md) |
| `docs/decisions.md` | The design decisions, append-only, newest last | [3](../03-principles/README.md), [C](../c-decision-index/README.md) |
| `docs/WATCH_CONTRACT.md` | The watcher's contract, version 5 | [5](../05-stage-machine/README.md), [6](../06-watcher/README.md) |
| `docs/branching.md` | The branches, who commits where, how a story's branch runs | [13](../13-git-and-github/README.md) |
| `docs/github-settings.md` | GitHub settings: projects, the factory's repository, tokens, the account | [13](../13-git-and-github/README.md), [15](../15-safety/README.md) |
| `docs/diagrams/*` (twelve) | v1's ten diagrams, their README, and `draw.py`, their generator | [17](../17-limits-and-backlog/README.md) |
| `docs/archive/README.md` | The archive's index: history only, never instructions | [17](../17-limits-and-backlog/README.md) |
| `docs/archive/deterministic-core.md` | The plan behind generation 5, built except part E | [3](../03-principles/README.md), [8](../08-stage-run/README.md), [16](../16-evidence/README.md), [17](../17-limits-and-backlog/README.md) |
| `docs/archive/fewer-commits.md` | A plan built, reverted and withdrawn on 2026-10-05 | [3](../03-principles/README.md), [17](../17-limits-and-backlog/README.md) |
| `docs/backlog/README.md` | The backlog's index: two plans and the open ideas | [17](../17-limits-and-backlog/README.md) |
| `docs/backlog/review-comments.md` | Reading the human's review comments; built, reverted, to be replanned | [3](../03-principles/README.md), [10](../10-human-at-the-gate/README.md), [17](../17-limits-and-backlog/README.md) |
| `docs/backlog/mutants-in-story-loop.md` | Mutation testing in every story; parked | [11](../11-feature-acceptance/README.md), [17](../17-limits-and-backlog/README.md) |
| `docs/reference/**` | This book, its print export, data and working files (writing plan, retarget list, figure kit) | — |

## Repository files

| File | Purpose | Chapter |
| :- | :- | :- |
| `Makefile` | `make check` (ruff, mypy, hadolint, pytest) and `make book`, which prints this book | [16](../16-evidence/README.md) |
| `.hadolint.yaml` | The Dockerfile linter's one exception: unpinned Debian packages | — |
| `.gitattributes` | Line endings: normalized, and LF for the files Linux runs | — |
| `.gitignore` | Ignored: caches, the virtual environment, `.env`, the book's build | — |
| `LICENSE` | The MIT license | — |
