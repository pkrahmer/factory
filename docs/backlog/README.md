# Backlog

Ideas discussed and parked, with the design as far as it got. Not decisions (those are in `../decisions.md`); the human picks from here. A small idea is an entry below; a bigger one, with a plan of its own, is a file in this folder, listed first. A plan that is built or withdrawn moves to `../archive/`.

## Plans with their own file

| Plan | State |
| :- | :- |
| [`review-comments.md`](review-comments.md) | Built and reverted on 2026-10-05; to be replanned. Make the human's review comments and reviews on the diff count: "Request changes" as the rework path, a plain review comment answered by the reviewer. |
| [`mutants-in-story-loop.md`](mutants-in-story-loop.md) | Parked on 2026-10-05. Mutation testing after the coder in every story, instead of test-only stories from each feature acceptance. |

## Ideas

- **Dev instance in the container.** A second checkout per repository on `main`, `make serve` as an optional fourth target on `$PORT`, restarted by the tick when `main` moves; later the demo stage runs against it and the pull request carries its URL. No image, no socket. Deferred until the build is solid.
- **Releases.** A release ships only accepted features: the release step (whichever form it takes) reads each feature's `ACCEPTANCE.md` `outcome` and refuses while a complete feature is `due`, `running` or `refused`. Within that, merge = release when the story's changelog line says so: `Fixed` → patch, `Added`/`Changed`/`Removed` → minor, `Breaking` → major, none → no release. The dispatcher cuts `## Unreleased` into the version and tags in the done commit. Version from the tag (`hatch-vcs`/`uv-dynamic-versioning`). GitHub Actions for `make check` on ready pull requests only (free minutes), image build and deploy pull-based on the NAS by a separate builder container with the Docker socket, never the agents' container.
- **Changelog.** `CHANGELOG.md` in Keep-a-Changelog form, one user-facing line per story written by the documenter under `## Unreleased`, only when the user notices the change; part of the docs criterion. Comes with the first release story.
- **Mutation survivors of the first product repository (2026-10-05).** 31 survivors: `errors._summary` formatting untested (8), `sqlite._format_created_at` with a non-UTC offset, `routes._apply` loading a todo it does not use (dead line). Material for a story, or for the feature acceptance above.
- **Mutation testing in the story loop (2026-10-05).** `make mutants` took 5 s on the demo project, so it could run after the coder: the reviewer sorts the survivors against the criteria (missing test, unrequested code, equivalent) and the tester adds the missing tests, instead of each gap becoming a test-only story at the next acceptance. Shape and open questions in [`mutants-in-story-loop.md`](mutants-in-story-loop.md).
- **Language server for the agents (2026-10-05).** Claude Code has LSP built in through plugins: put `LSP` in `--tools`, and the agent gets diagnostics after each edit plus read-only navigation (definition, references, hover, symbols). It works headless and is unaffected by `--strict-mcp-config`, so no MCP server is needed. For Python the only official plugin is `pyright-lsp`, and a plugin is just an `lspServers` entry (command, args, extension map).
  - **Not now:**
    - Agents navigate cheaply already. In 40 sessions they made 120 grep/find/ls calls against 162 file reads, usually `grep -n "def x" -A8 <file>` chained with other reads, at no extra turn.
    - The demo has 623 lines of source.
    - The gate already reports type errors.
  - **The main con is two checkers.** Pyright diagnostics while the agent edits, and `mypy --strict` as the gate, disagree in places, and the code is already shaped by mypy (the demo's decorator-form exception handlers).
  - **If it comes back:** one checker for both. Candidate: Astral's `ty`, which is its own checker and language server (`ty server`), a uv dev dependency with no Node.
    - It was still 0.0.84 at the time, with no equivalent of the Pydantic mypy plugin.
    - On the demo code, green under mypy, it found one diagnostic: it does not honour a mypy-coded `type: ignore[misc]`.
    - Start-up cost is no reason for a long-running server: a cold `ty check` of the demo took about 0.15 s (mypy cold 3.2 s). A server that outlives the agent processes would also have to follow the dispatcher's checkouts and merges, or serve stale diagnostics.
  - **Trigger:** session logs where agents need several grep rounds to find code, or read whole files for one function. Then test one agent with and without `LSP` on the same story.
- **Running the Demo blocks in code (2026-10-05).** Part E of the deterministic-core plan ([`../archive/deterministic-core.md`](../archive/deterministic-core.md)): each Demo block is a self-contained script, so code could run it and paste the output, leaving the demo agent only the judgment. Not built: no run showed a demo agent altering a command, the saving is small, and a misbehaving block (a server that does not die, a port in use) is where a model recovers and code would need a process-group timeout and a rule per case. **Trigger:** a run where a demo agent "fixes" a command.
- **Paths never run live.** `doing → tests` after an approved test change, the attempts cap and its retry question, `reject`, two stories in `ongoing/` at once (from the demo runs). The demo's hardening mode (`demo/README.md`) lists them as paths to provoke with deliberately imperfect stories.
- **Not yet covered elsewhere.** Pull request review comments on diff lines are not read (only issue comments; the plan is [`review-comments.md`](review-comments.md)); a watchdog for a dead container (GitHub Action or NAS cron); `CLAUDE_VERSION` pinned in the image; SPA support (Node in the image, browser demo).
