# <project>

<One paragraph: what this is, for whom, and what it does. The reader has thirty seconds.>

## Getting started

```bash
uv sync                       # install
uv run python -m <package>    # run
make check                    # everything the pipeline checks: lint, types, tests
```

<What the reader sees when it works: a URL, a prompt, an output line.>

## Using it

<The two or three things a user does with it, each with a runnable example.> The HTTP API documents itself at `/docs` (Swagger UI) and `/redoc`; the same schema is committed as `docs/openapi.json` for reading on GitHub.

## Where to look next

- `docs/api.md` — concepts, errors and examples the schema cannot express
- `docs/architecture.md` — the layers and why they are cut that way
- `docs/decisions.md` — lasting decisions and what was rejected
- `CLAUDE.md` — the rules every change follows (architecture, tests, checks)

## How it is built

Built by the factory (github.com/pkrahmer/factory): features and their user stories live under `factory/features/`, one folder per feature, and one stage agent at a time takes a story through tests, code, review, docs and demo. A story's pull request carries the whole story; merging it accepts the story.
