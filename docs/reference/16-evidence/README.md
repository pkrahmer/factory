# 16. Evidence and verification

This chapter holds v1's numbers: how v1 is verified before it runs, what its four runs showed, the seventeen defects they found, and what has not been verified at all.

## The concept

A factory is verified on three levels, and each finds what the others cannot.

- **Unit tests** check the code against fakes of the hosting service and the agent runtime, with a throwaway repository as the remote. They are cheap, fast and repeatable, and they reach paths no live run walks on its own. They cannot show what a model does with its instructions, or whether the fakes match the real services.
- **End-to-end runs** let the factory build a real project, with a person or an agent playing the human. They are the factory's real test suite (P17 in [chapter 3](../03-principles/README.md)): they show what the models do, what the services do, and what a story costs. They are expensive, and a clean run walks only the happy path.
- **Hardening runs** are end-to-end runs with stories that carry deliberate defects, one per path the factory must handle: a question, a rework, a cap, a close.

The evidence a run leaves is the factory's own records, never an agent's account of itself (P11): the cost records (P16), the work items' logs, the pull requests and the history. One instrument built from them decided v1's shape: a table of every defect by **where the fault sat**, in code, in a model executing a step with one right result, in a protocol only prose described, or in wording. [Chapter 1](../01-why-a-factory/README.md) draws the conclusion.

A **clean** story is one in which every stage passed the first time, with no question and no rework. The baselines below are for clean stories.

## Verification in v1

### The test suite

`make check` in the factory's repository runs ruff's lint and format check, `mypy` in strict mode, `hadolint` on the Dockerfile and `pytest`. At `930c61a` the suite has 183 tests in ten files, unchanged since 5 October, and takes about 70 seconds on a laptop:

| File | Tests | What it covers | How |
| :- | -: | :- | :- |
| [`test_watch.py`](../../../tests/test_watch.py) | 48 | every event and its precedence; reading branches, `origin/main` and acceptances; `last_change`; the board | `evaluate` on constructed snapshots, without Git; the readers on a throwaway repository |
| [`test_dispatch.py`](../../../tests/test_dispatch.py) | 41 | every handler and the stage protocol: caps, send-backs, the undo, the checks, the hand-over, the acceptor's facts | a throwaway repository with a bare `origin`, `FakeGitHub`, and a fake agent that edits, may commit, and returns an outcome |
| [`test_tick.py`](../../../tests/test_tick.py) | 23 | `needs_handling`, the memo, failures and `give_up`, the lock, leftovers, the preflight stamp, the cost table at the gate | pure functions; a throwaway repository with stubbed handlers |
| [`test_guard.py`](../../../tests/test_guard.py) | 18 | lanes, protected paths, paths outside the repository | the hook's JSON input |
| [`test_preflight.py`](../../../tests/test_preflight.py) | 12 | every item, the fixes per platform | tool lookup and commands passed in as functions |
| [`test_agent.py`](../../../tests/test_agent.py) | 9 | the command line, the budget resume, the denials, the installed agent files | canned JSON results in place of Claude Code |
| `test_story.py`, `test_check_story.py`, `test_github.py`, `test_costs.py` | 32 | the story format, form validation, the `gh` calls and the marker, the cost table | strings, a recorder in place of `gh`, temporary files |

Generation 5 wrote `test_dispatch.py` from the dispatcher skill it replaced; its docstring says every path the skill described is a test, "including the ones no live run has walked". Some tests are named for a defect a run found, such as the non-ASCII report (fix 15 below) or the cost-table comment (fix 4).

The suite stops at every process boundary: `entrypoint.sh`, `scripts/demo-check.sh`, the skills' effect on a model, Claude Code's behavior and `gh`'s real output are not tested. The fakes are written from what the code expects, not recorded from the services.

> [!WARNING]
> **v1 limit:** nothing tests the containment of [chapter 15](../15-safety/README.md) or a project's own checks. The guard is tested on its input, and the undo on a fake agent's writes, but no test starts an agent and tries a denied command, a write from the shell outside the lane, or a push. The demonstration project's `layers` target could never fail ([chapter 12](../12-project-contract/README.md)), and no run noticed. A check that has never failed is not known to work.

### The demonstration

[`demo/README.md`](../../../demo/README.md) is v1's end-to-end test: a Claude Code session, given one prompt, plays the human against an empty GitHub repository and the demonstration project ([chapter 12](../12-project-contract/README.md)). Before it starts, [`scripts/demo-check.sh`](../../../scripts/demo-check.sh) prints one `ok`, `missing` or `note` line per prerequisite, among them an empty target, a fresh work volume and an image newer than the factory's checkout.

The session copies one feature at a time, promotes the lowest story, waits for its archive, answers questions "as a sensible single-user to-do service would", and merges or closes. It never edits product code, the target's `.claude/` or pushed history, and never runs a stage's commands by hand. It stops at $40 of spending, after four hours, at a stall that looks like the factory's fault, or before merging something it believes wrong. A further run on the same target starts from a commit that removes everything and from a fresh work volume, so that cost records keyed by a story's path do not mix two runs. The README's cost figure, "about 1.50 to 2.20 USD" a story, is generation 4's.

### Hardening mode

*Hardening mode*, in the same README, changes one rule: every defect is the factory's until proven otherwise. The session fixes it in the skills, the rules, the engine or the template, runs `make check`, commits, rebuilds the image and lets the story continue; it stops and asks the maintainer only when a fix would change the model rather than a detail: a new stage, a new rule, a change to what the human does, or to the watcher's contract. The README lists twelve paths, each carried by a story with one deliberate defect, marked `<!-- carries path N -->`. Run 3's plan split a test change the human approves off path 3 as a thirteenth; the README does not list it.

## Evidence from the runs

### Four runs

All four ran against the demonstration project in `pkrahmer/factory-demo-todo`; [chapter 1](../01-why-a-factory/README.md) says what each was for. The *Starts* column counts different things: in generation 4 the tick started the dispatcher, one Sonnet session per event with the stage agent as its subagent; in generation 5 it starts agent runs.

| Run | Generation | When (UTC, 2026) | Work items | Pull requests | Starts | Cost | Fixes |
| -: | -: | :- | :- | :- | -: | -: | :- |
| 1 | 4 | 4 Oct, 21:28–23:28 | 8 stories | #1–#10 | 69 | $17.97 | 1–12 |
| 2 | 4 | 4–5 Oct, 23:31–00:59 | 8 stories | #11–#18 | 48 | $14.09 | 13, after the run |
| 3 | 4 | 5 Oct, 08:59–11:42 | 3 acceptances, 1 refused; then 4 stories archived, a fifth left at the gate, 1 acceptance refused | #19–#29 | 6 + 75 | about $26 | 14–17 |
| 4 | 5 | 5 Oct, 16:47–19:38 | 8 stories, 3 acceptances | #30–#40 | 59 | $15.89 | none |

The times run from a run's start to its last archive (run 3: to the stop at 11:42); run 4's cost records span 16:49 to 19:36. The records of runs 1 to 3 were lost with their work volumes; their numbers survive in the maintainer's run log and in the cost tables on their pull requests. Run 4's records are kept in this book's `data/` folder, as `demo-dispatches.jsonl`.

### Seventeen fixes

Runs 1 to 3 found seventeen factory defects. [Chapter 1](../01-why-a-factory/README.md) counts them by kind; this is the list.

| Fix | What failed | Where the fault sat | The fix |
| :- | :- | :- | :- |
| 1 | `demo-check.sh` said `claude` was missing inside a Claude Code session | code: the script | also accept `CLAUDECODE=1` |
| 2 | `demo-check.sh` called a fresh image older than its commit | code: time stamps compared as strings across time zones | both in UTC |
| 3 | the container crash-looped on the empty target; a pushed setup would never have reached it | code: the entrypoint | prepare each repository every round, and wait until it is ready |
| 4 | a dispatcher start only to count the tick's own cost-table comment | protocol: the tick and the dispatcher | the tick skips comments that are all its own |
| 5 | a close at `accept` without a reason sent the coder to guess; past the round cap it would have looped on every tick | protocol: the dispatcher skill | reopen first; without a reason, or past the cap, the three-option question |
| 6 | a restart during a stage would have idled the line for over an hour | code: the entrypoint and the tick | locks removed at start; an agent run older than the start is expired at once; `TERM` trapped |
| 7 | the dispatcher recomputed the age of an `expired` claim (generation 4's run record), found it fresh and did nothing | a model executing a step | the event is authoritative; a dispatcher start that moved no branch counts as failed |
| 8 | a close while the stages worked went unnoticed until the gate | protocol | the pull request's state is read before an agent starts |
| 9 | the pull request invited questions that nobody answers | wording | the closing paragraph says what each action does |
| 10 | intake after an answer worked only because two models improvised | protocol: which branch, and who carries the answer in | the existing branch is checked out; intake carries the answer into the story |
| 11 | an archive entry written as a bullet | a model executing a step | the skill defines appending as the next number |
| 12 | a second run on the same target would add the first run's costs | code: the script | "empty" includes a main branch with an empty tree; a fresh work volume is required |
| 13 | unindented verdicts ended the log's list; two archives misnumbered their entry | a model executing a step | the reviewer indents; the next number follows the last entry |
| 14 | a merged acceptance that brought drafts was never booked | code: the watcher | a report on the main branch not at `done` is listed whatever `drafts/` holds |
| 15 | a report quoting `Straße` read as empty on Windows, so a refused acceptance looked due | code: subprocess output decoded in the locale's encoding | decode as UTF-8 |
| 16 | a criterion carried in from an answer landed after `docs:` | a model executing a step | R5 says where it goes |
| 17 | intake accepted a demonstration without `Expect:` | a model executing a step | intake's entry lists one line per point it checked |

The seven defects in code stayed fixed; three of them (6, 14, 15) are pinned by a test, and the rest sit in scripts no test reaches. Generation 5 took the other ten out of the models' hands: handlers in code (4, 5, 8, and the branch choice of 10, while carrying the answer in stays intake's), code that numbers and places entries (11, 13), form validation that detects a misplaced criterion (16) or prevents a missing `Expect:` (17), no model left to second-guess an event (7), and a tested constant (9). v1's decision log records five more defects from generations 1 to 3, all file, Git, clock or check handling done by a model.

### Paths walked

| Path | What it walks | Generation 4 (runs 1–3) | Generation 5 (run 4 and after) |
| :- | :- | :- | :- |
| 1 | intake asks: a behavior without a criterion; a demonstration without `Expect:` | runs 1, 3 | — |
| 2 | intake asks for a failing side | run 3 | run 4 |
| 3 | the tester finds a criterion against the interface | — (intake caught it a stage earlier) | — |
| 4 | a review rework | runs 1, 3 | run 4 |
| 5 | a documenter finding | — (intake caught the planted defects) | — |
| 6 | a demo finding | — (the same) | — |
| 7 | the round cap | run 1 (at `accept`), run 3 (at `review`) | — |
| 8 | the attempts cap and its retry | run 3 (an agent file removed) | — |
| 9 | `reject` after a stage change by hand | — | — |
| 10 | two stories in `ongoing/` at once | run 3 | — |
| 11 | a close at `accept` | runs 1, 3 | — |
| 12 | an acceptance refused; one merged, with its drafts promoted | refused and merged, run 3 | merged, run 4; drafts promoted after it |
| 13 | a test change the human approves (`doing → tests`) | run 3 | run 4 |

Run 1 also walked a restart during a stage, a close while the stages worked, a discarded story promoted again, and a merge while the send-back question was open, all on generation 4.

> [!WARNING]
> **v1 limit:** most paths have run live only on code that no longer exists. Generation 5 replaced the dispatcher skill and every agent's protocol; on generation 5 the caps, the restart, the closes, the discard and two stories in production have run only as unit tests, and `reject` has never run live on any generation.

### Run 4, item by item

| Work item | Pull request | Agent runs | Agent minutes | Cost | Promotion to archive | What happened |
| :- | :- | -: | -: | -: | -: | :- |
| F0001-S0001 | #30 | 11 | 6.1 | $2.85 | 62 min | the reviewer found a gap in a test; the coder asked; the human chose the test change, `doing → tests → doing`; about 52 of the 62 minutes were the simulated human's two waits |
| F0001-S0002 | #31 | 6 | 2.5 | $1.31 | 7.0 min | clean |
| F0001-S0003 | #32 | 6 | 4.0 | $1.54 | 8.9 min | clean |
| F0001-S0004 | #33 | 8 | 5.0 | $1.94 | 10.2 min | one review rework |
| F0001 acceptance | #34 | 1 | 5.0 | $1.59 | | accepted with drafts |
| F0002-S0001 | #35 | 7 | 2.8 | $1.36 | 10.2 min | the intake question of [chapter 1](../01-why-a-factory/README.md) |
| F0002-S0002 | #36 | 6 | 2.1 | $0.85 | 7.1 min | clean |
| F0002-S0003 | #37 | 6 | 2.2 | $1.12 | 7.0 min | clean |
| F0002 acceptance | #38 | 1 | 5.0 | $1.47 | | accepted with drafts (S0004, S0005) |
| F0003-S0001 | #39 | 6 | 2.3 | $1.00 | 7.3 min | clean |
| F0003 acceptance | #40 | 1 | 3.2 | $0.87 | | accepted |

Clean stories averaged $1.16, all eight $1.50, an acceptance $0.87 to $1.59. *Promotion to archive* is wall-clock time and includes the simulated human, who usually acted within seconds, and the tick's pause (below): a clean story spent two to four minutes in agents and seven to nine on the clock.

After run 4, on later commits, the human promoted three of F0001's proposed drafts as S0005 to S0007 (#41, #42, #44): 6 agent runs each, $0.97, $0.54 and $0.47, about four to five minutes from promotion to archive. Two more F0001 acceptances followed (#43, #45), $1.62 and $1.60. S0007 and both acceptances ran on the image built at 20:59 UTC; which image ran S0005 and S0006 is not recorded.

### What the bookkeeping cost

Run 2's cost tables give whole dispatcher starts, the stage agent included. A start without an agent cost $0.11 to $0.13 in run 3, so v1's plan for generation 5 took $0.11 as the dispatcher's share of every start. Run 4's records give the agents alone, averaged over its five clean stories:

| Stage | Run 2: dispatcher | Run 2: agent | Run 4: agent | Run 4: turns |
| :- | -: | -: | -: | -: |
| intake | $0.11 | $0.08 | $0.09 | 5.4 |
| tests | $0.11 | $0.27 | $0.28 | 5.6 |
| doing | $0.11 | $0.21 | $0.27 | 7.8 |
| review | $0.11 | $0.26 | $0.23 | 5.2 |
| docs | $0.11 | $0.08 | $0.13 | 8.0 |
| demo | $0.11 | $0.21 | $0.17 | 4.2 |
| archive | $0.12 | — | — | — |
| **a clean story** | **$0.78** | **$1.09** | **$1.16** | |

The stage averages are rounded; the totals are the stories' own. The dispatcher's 42% is gone; the agents cost about what they did. In run 3's second part, with questions, reworks and closes, the dispatcher's share was about 40%, $8.40 of $21.18. Run 4's 59 agent runs read 8.2 million tokens from the cache, wrote 1.5 million to it and produced 0.2 million.

### The measurements behind three changes

After run 4, its records and its 59 transcripts, which five analysts read for where the tokens went, led to three changes ([chapter 14](../14-runtime/README.md) describes them):

- *The pause.* In run 4 every story waited out the full two-minute pause three times, for steps the simulated human took right after the factory's. The pause now starts at 15 seconds and doubles.
- *Connectors.* About 7,500 tokens an agent run, an estimated fifth of all cache cost, were the cached prefix written again after the connectors' announcement. A two-call test confirmed it: the second call wrote 5,500 tokens to the cache without `--strict-mcp-config` and 200 with it.
- *Fewer turns.* Every call re-read a prefix of 20,000 to 40,000 tokens. The reviewer ran `make check` in all ten of its agent runs, four times as a turn of its own, and six of nine testers read `docs/architecture.md`.

### What is not verified

Beyond the narrow evidence of [chapter 1](../01-why-a-factory/README.md) (one project, a simulated human, one machine, no full run of the code this book describes):

- **The effect of the last two changes.** S0006 and S0007 wrote 7,600 to 9,800 tokens to the cache per agent run, against 22,000 for run 4's stories, which fits the connector change; but they were smaller stories, and no full run has measured either change.
- **The human.** Every run had a simulated human, who was never notified by GitHub ([chapter 10](../10-human-at-the-gate/README.md)).

> [!WARNING]
> **v1 limit:** the evidence is not in the repository. The defect list and runs 1 to 3 are recorded in a run log in the factory's earlier, unpublished history, and v1 has no procedure that keeps a run's cost records, its tag in the demonstration repository and its summary together in version control.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - for each hardening path, the plan names its unit test and requires a live run on the shipped code that walks it, `reject` included;
>   - every defect found in a run gets a row saying where the fault sat; a row outside code is moved into code, or its exception recorded (P1);
>   - a baseline is quoted with its conditions: the tick's pause, the human's answer times, the story's size. Run 4's: a clean story about six agent runs, $1.16, seven to nine minutes under a two-minute pause; an acceptance $0.87 to $1.59 ([chapter 1](../01-why-a-factory/README.md) says how narrow this evidence is).
> - **Incidental to v1:** pytest, the demonstration project, a Claude Code session as the human, the $40 and four-hour stops.
> - **Watch for:**
>   - fakes checked against the real services, by a contract test or a recorded session;
>   - the containment and the project's checks tested as cases that must fail (the Planner boxes of [chapters 15](../15-safety/README.md) and [12](../12-project-contract/README.md));
>   - a real human in at least one run, to measure notifications and answer times;
>   - a run's records, summary and fault table committed at its end (P2).
