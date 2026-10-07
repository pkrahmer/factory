# C. Decision index

v1's decision log, [`docs/decisions.md`](../../decisions.md), records each design decision as one entry: its date, what was decided, the reason and usually what was rejected. The decision log is append-only, newest last, so an entry stays as written when a later one replaces it; the column *Superseded by* names the later entry, with the part it replaces in parentheses when it replaces only a part. The ids D01 to D58 are this index's, in the decision log's order; the decision log has none. The chapters cite a design decision by date and topic, as in "Design decision: 2026-10-05 (the dispatcher is code)", and since many entries share a date, the topic identifies the entry. The index follows the decision log at `930c61a`, the commit the book describes; D57 and D58 were written on 2026-10-07, D57 under the date of the events it records. The column *Chapters* lists the chapters that cite an entry by its date; a dash means no chapter cites it, not that no chapter treats its subject.

## Built inside the first product repository (until the extraction on 2026-10-04)

| Id | Date | Design decision | Superseded by | Chapters |
| :- | :- | :- | :- | :- |
| D01 | 2026-10-03 | A separate tester stage writes the tests before implementation, and the coder may not edit them. | — | [3](../03-principles/README.md) |
| D02 | 2026-10-03 | `make check` must pass at every stage; an advisory result gets ignored. | D53 (which check runs after which stage) | [3](../03-principles/README.md) |
| D03 | 2026-10-03 | Everything on the main branch: one work item in flight, its code and its file in one commit. | D07 | — |
| D04 | 2026-10-03 | Refactoring is a step inside the coder stage (red, green, refactor), not a stage of its own. | — | [3](../03-principles/README.md) |
| D05 | 2026-10-03 | The reviewer reads and runs checks but writes no code, not even experiments. | D56 (running `make check`) | [3](../03-principles/README.md) |
| D06 | 2026-10-04 | Work items (v1's *tickets*) live in one folder, `tasks/`, and the stage is a frontmatter field, not a folder. | D27 (the one folder) | — |
| D07 | 2026-10-04 | A branch per work item again, `ticket/<id>-<slug>`, with a draft pull request from intake on; the human accepts by merging; one checkout, WIP 1. | — | [3](../03-principles/README.md) |
| D08 | 2026-10-04 | Lanes are enforced by a `PreToolUse` hook per agent (`guard.py`), not by global deny rules. | — | [3](../03-principles/README.md) |
| D09 | 2026-10-04 | The dispatcher session runs on Sonnet, not Haiku, so that it can run unattended. | D48 | — |
| D10 | 2026-10-04 | A preflight verifies the machine's tools before the loop, asks the human before installing any, then runs `make check` on the main branch; stage agents never work around a missing tool. | D13 (the `make check` probe), D17 (asking the human) | [3](../03-principles/README.md) |
| D11 | 2026-10-04 | Questions reach the human only on the pull request, never in the chat, so that every answer becomes a log entry. | — | [3](../03-principles/README.md) |
| D12 | 2026-10-04 | A wrong test goes back to the tester (`doing → tests`) once the human approves; the coder never edits tests. | — | [3](../03-principles/README.md) |
| D13 | 2026-10-04 | The preflight probes with `make lint` and the shell tools the recipes call, not `make check`: a work item's branch may be red on purpose. | — | [14](../14-runtime/README.md) |
| D14 | 2026-10-04 | The dispatcher speaks only when the human has something to do or know; the watcher remembers the last event it printed. | D17 (the dispatcher's silence) | — |
| D15 | 2026-10-04 | Intake runs on Sonnet, not Haiku: it is the judgment step that decides whether a story can be built. | — | [9](../09-agents-and-skills/README.md) |
| D16 | 2026-10-04 | Stage agents run in permission mode `auto`, with an allow list of the shell commands they were seen to use. | — | [9](../09-agents-and-skills/README.md) |
| D17 | 2026-10-04 | Generation 3: no dispatcher session; a scheduler ticks every two minutes and starts the dispatcher, headless, only for an event that needs it. | D48 (the model dispatcher), D54 (the interval) | [3](../03-principles/README.md) |
| D18 | 2026-10-04 | Every stall is a comment on the pull request, not only the one at the attempts cap. | — | [3](../03-principles/README.md) |
| D19 | 2026-10-04 | Rules, skills and fields call the person the factory works for *the human*, not by name: the factory is a pattern, not one person's tool. | — | — |
| D20 | 2026-10-04 | The loop runs in a container that owns its checkout; the image holds tools, never the repository; one service per repository, on a NAS, was planned. | D25 (one service per repository) | [14](../14-runtime/README.md), [15](../15-safety/README.md) |
| D21 | 2026-10-04 | Work items without a branch are read from `origin/main`, so that one committed from the phone is seen while the checkout sits on another branch; the tick fetches, the watcher never. | — | — |
| D22 | 2026-10-04 | The tick records each dispatcher start's cost as a JSON line; the sum goes on the pull request at the gate and into the log at the archive. | D48 (one record per dispatcher start) | [3](../03-principles/README.md) |
| D23 | 2026-10-04 | The factory stops knowing how a project is built: lanes move into `stages.yml`, and `make check`, `make lint` and `make test` become the whole project contract. | — | [3](../03-principles/README.md) |
| D24 | 2026-10-04 | The factory moves into its own repository; the product repository keeps its stage table, its work-item template (`factory/TICKET.md`), its work items, `CLAUDE.md` and the Makefile. | — | [3](../03-principles/README.md) |

## In this repository

| Id | Date | Design decision | Superseded by | Chapters |
| :- | :- | :- | :- | :- |
| D25 | 2026-10-04 | The factory is a repository and image of its own: the engine a package, skills and agents installed at user level, each project carrying only its own files; rejected: a Claude Code plugin, Git submodules. | — | — |
| D26 | 2026-10-04 | The rules are a skill, `factory-rules`, preloaded into every stage agent, not an import in each project's `CLAUDE.md`: the rules travel with the factory. | D49 (the preloading) | — |
| D27 | 2026-10-04 | Generation 4: features and stories replace the flat `tasks/` folder, where finished work items hid the live ones; a story's folder, `drafts/`, `ongoing/` or `done/`, is its lifecycle. | — | — |
| D28 | 2026-10-04 | The frontmatter shrinks to seven fields that only machines need, and `awaiting: human` becomes the stage `accept`: every field an agent maintains is one it can get wrong. | D52 (`claimed_at`) | — |
| D29 | 2026-10-04 | Lanes are glob patterns, not folder names. | — | [3](../03-principles/README.md) |
| D30 | 2026-10-04 | Closing a pull request sends the story back to the coder at `accept`, and at any other stage discards it to `drafts/`, where the human's text survives. | D35 (a close without a reason at `accept`) | — |
| D31 | 2026-10-04 | A `docs` stage between `review` and `demo`, with its own agent, the documenter, which also reads the other documents for drift. | — | [3](../03-principles/README.md) |
| D32 | 2026-10-04 | Every story ends with two fixed criteria: `make check stays green`, and `docs:` with what the reader must know, or `none` and why. | — | [3](../03-principles/README.md) |
| D33 | 2026-10-04 | The template's README describes the application, not the factory: its readers are the application's users. | — | — |
| D34 | 2026-10-04 | The preflight verifies that every agent the stage table names is installed; its stamp holds the factory's version and a hash of `stages.yml`. | — | [14](../14-runtime/README.md) |
| D35 | 2026-10-05 | A pull request closed at `accept` without a reason is reopened as a draft, and the dispatcher asks: comment what to change, close again to discard, or merge; a silent close had left the coder nothing to address. | — | — |
| D36 | 2026-10-05 | A restart recovers by itself: the entrypoint removes stale locks, and an agent run begun before the restart is `expired` at once. | — | [3](../03-principles/README.md) |
| D37 | 2026-10-05 | The dispatcher never second-guesses an event: an `expired` event is a dead agent run, however recent its run record; a start that moved no branch on an event that always commits is a failure. | D48 (the no-branch rule) | [3](../03-principles/README.md) |
| D38 | 2026-10-05 | Before starting an agent, the dispatcher asks GitHub for the pull request's state, so that a pull request closed during the stages is noticed. | — | [3](../03-principles/README.md) |
| D39 | 2026-10-05 | The pull request description's closing line says only what each of the human's actions does at `accept`. | — | [3](../03-principles/README.md) |
| D40 | 2026-10-05 | After an answer, intake runs on the existing branch and writes an answer that changes the story into it verbatim, citing the log entry; rejected: the watcher naming the branch, a change to the watcher's contract. | — | — |
| D41 | 2026-10-05 | Failure paths are criteria: intake asks for a missing failing side; the tester tests a stated limit on both sides and invents nothing. | — | [3](../03-principles/README.md) |
| D42 | 2026-10-05 | The template's `check` gains SAST, a secrets scan, a license allow list and an API contract test; a silencing marker needs a stated reason. | — | [12](../12-project-contract/README.md) |
| D43 | 2026-10-05 | Feature acceptance: an acceptor judges each completed feature once, writes `ACCEPTANCE.md` and proposes drafts, which only the human promotes. | — | [3](../03-principles/README.md), [11](../11-feature-acceptance/README.md) |
| D44 | 2026-10-05 | Trunk-based stays: stories merge into the main branch one at a time, and a feature's acceptance decides its status and later what ships, not what reaches the main branch. | — | [3](../03-principles/README.md), [11](../11-feature-acceptance/README.md) |
| D45 | 2026-10-05 | Commits carry noreply addresses only, because a repository the factory builds may be public. | D58 (the default address) | [13](../13-git-and-github/README.md) |
| D46 | 2026-10-05 | The hands-off exercise becomes the demonstration (`demo/README.md`, `scripts/demo-check.sh`), with a hardening mode for maintainers. | — | — |
| D47 | 2026-10-05 | The factory is republished as a new repository from one commit: its history held a personal address and private repository names, and a rewrite leaves old commits reachable through pull request refs. | — | — |
| D48 | 2026-10-05 | Generation 5: the dispatcher is code (`factory.dispatch`), one tested handler per event; only a `run` event starts a model, and an agent run that ends without a stage change or a question is a stall. | — | [3](../03-principles/README.md), [7](../07-dispatcher/README.md) |
| D49 | 2026-10-05 | The tick starts each agent from its file with explicit flags: skills as prompt text, the lane guard as a hook, a dollar budget, the lease as a time limit. | — | [9](../09-agents-and-skills/README.md), [14](../14-runtime/README.md) |
| D50 | 2026-10-05 | Every comment the factory posts carries a hidden marker, `<!-- factory -->`; at the attempts cap, any comment means retry. | — | [3](../03-principles/README.md) |
| D51 | 2026-10-05 | Code validates a story's form (`story.check`) before intake; intake keeps what code cannot judge. | — | [3](../03-principles/README.md) |
| D52 | 2026-10-05 | The run record leaves Git for `.git/factory-run.json` (the watcher's contract version 5); `claimed_at` leaves the frontmatter, which keeps six fields. | — | [3](../03-principles/README.md) |
| D53 | 2026-10-05 | The stage protocol is code (`factory.stage`): an agent returns a decision and its log entry; the factory undoes writes outside the lane, runs the stage's checks, commits and pushes. | — | [3](../03-principles/README.md) |
| D54 | 2026-10-05 | The pause between ticks is 2 seconds after a handled event, then 15, doubling to 120. | — | [3](../03-principles/README.md), [14](../14-runtime/README.md) |
| D55 | 2026-10-05 | Agent runs leave out the login's connectors, auto memory, the Git snapshot and bytecode files; the connectors made every agent run rewrite its cached prefix. | — | [8](../08-stage-run/README.md), [14](../14-runtime/README.md) |
| D56 | 2026-10-05 | Stage skills ask for fewer turns and fewer reads of what `CLAUDE.md` or the factory already covers; the reviewer no longer runs `make check`, which the factory runs before and after it. | — | [9](../09-agents-and-skills/README.md), [14](../14-runtime/README.md) |
| D57 | 2026-10-05 | The plans *fewer commits* and *review comments* were built and reverted the same day: each added rules only a model could follow, for a small gain, and GitHub lets nobody request changes on their own pull request; *fewer commits* was withdrawn, *review comments* is to be replanned in code. | — | [3](../03-principles/README.md) |
| D58 | 2026-10-07 | The default commit address becomes `factory@noreply.invalid`, which matches no GitHub account; the old one matched an unrelated organization. | — | [13](../13-git-and-github/README.md) |
