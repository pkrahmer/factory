# Deterministic core

The plan for moving the pipeline's control flow out of skill text and into tested code. Nothing here is done yet. The human decides the open points under *Decisions for the human*; then it is built in the order under *Order*, and one demo run in hardening mode verifies it.

## The finding

Three end-to-end runs found seventeen factory defects (the archived `docs/rebuild-log.md`, fixes 1 to 17). Not one of them was a stage agent judging its actual work badly: no wrong test, no bad code that review missed, no misleading documentation. Every defect sat in the machine, in the engine code, or in the bookkeeping that skill text asks a model to carry out. The judgement held up: the reviewer caught a published `maxLength` that applied before stripping, intake caught a criterion that contradicted its Interface a stage before the tester would have, and the acceptor found an unpaired-surrogate crash that no story had named.

Meanwhile the bookkeeping is the most expensive single item. The dispatcher is a Sonnet session that starts for every line, reads the skill, runs some git and gh commands, and stops. It costs about the same every time, whatever it does.

### Where the faults sat

| Fix | What failed | Where the fault sat | After this plan |
| :- | :- | :- | :- |
| 1, 2, 12 | demo-check false alarms, a second run without a clean start | script | unchanged (code already) |
| 3, 6 | crash loop on an empty target, a restart idling the line | entrypoint, tick | unchanged; 6 gets simpler with D |
| 14, 15 | merged acceptance never booked, UTF-8 decoding | watcher code | unchanged (found live, now tested) |
| 4 | a dispatcher run only to count the tick's own comment | the tick/dispatcher boundary | gone: no model run for bookkeeping at all |
| 5 | a silent close sent the coder to guess; the round cap at `accept` looped | dispatcher protocol, as skill text | a handler with unit tests; the loop was found "from skill and code" by hand, a test finds it before a live run |
| 8 | a close during the stages went unnoticed | dispatcher protocol | the same check, in tested code |
| 10 | intake after an answer worked only because two models improvised | dispatcher protocol (which branch) and intake | branch choice in code; carrying the answer in stays intake's |
| 7 | the dispatcher recomputed a claim's age and did nothing | model improvised against the line | gone |
| 11, 13 | a log entry as a bullet, a wrong entry number, an unindented verdict | model formatting (dispatcher, reviewer) | gone: code numbers and appends entries, the verdict is an outcome |
| 16 | a carried-in criterion after `docs:` | model placement (intake, coder) | caught by the ticket check after every stage |
| 17 | intake accepted a Demo command without `Expect:` | model judging a format rule | gone: code checks the format, intake judges the rest |
| 9 | the pull request invited questions nobody answers | wording the demo copies "word for word" | one tested constant |

From `docs/decisions.md`, before the log: a ticket copied instead of moved, a transition line that could not know its own commit, timestamps guessed by Haiku, the coder and the reviewer reporting `make check` green after running its commands by hand, a coder dying on a permission prompt for `… | head`. All are file, git, clock or gate handling done by a model. None is judgement.

Of the ten fixes outside the machine and the engine, five are a model not executing protocol correctly (7, 11, 13, 16, 17), four are protocol that was incomplete or wasteful and could only be found in a live run (4, 5, 8, 10), one is wording (9). The rebuild log's *Open* list says it directly: the attempts cap, `reject`, `doing → tests` and two stories in `ongoing/` are covered for the watcher by unit tests, but "the dispatcher's handling is skill text only".

### What the bookkeeping costs

The tick records one line per dispatcher run. Its `usage` and `num_turns` are the dispatcher session's own; `total_cost_usd` includes the subagent it started (Claude Code's cost-tracking documentation says so, and the numbers agree: an intake run and an `ask` run have the same session tokens, 20k fresh and 130k cached, but cost $0.18 and $0.11). So a dispatcher session costs what a line without an agent costs, and the rest of a `run` line is the agent.

Lines without an agent, run 3 part two (`.git/factory-dispatches.jsonl` in the container, 75 runs):

| Line | Runs | Average | Seconds |
| :- | -: | -: | -: |
| `ask` | 8 | $0.11 | 15 |
| `pr` | 7 | $0.11 | 15 |
| `merged` | 4 | $0.12 | 17 |
| `closed` | 3 | $0.13 | 19 |

Run lines, average of the eight clean stories of run 2 (cost tables on pull requests 11 to 18), split into the dispatcher's $0.11 and the agent:

| Stage | Run | Dispatcher | Agent |
| :- | -: | -: | -: |
| intake (Sonnet) | $0.19 | $0.11 | $0.08 |
| tests (Opus) | $0.38 | $0.11 | $0.27 |
| doing (Opus) | $0.32 | $0.11 | $0.21 |
| review (Opus) | $0.37 | $0.11 | $0.26 |
| docs (Sonnet) | $0.19 | $0.11 | $0.08 |
| demo (Opus) | $0.32 | $0.11 | $0.21 |
| archive (`merged`) | $0.12 | $0.12 | — |
| **story** | **$1.87** | **$0.78 (42 %)** | **$1.09** |

Run 3 part two, with questions, reworks and closes: 22 bookkeeping runs ($2.54) plus 53 run lines at about $0.11 dispatcher share each, about $8.4 of $21.18, 40 %. In time, the dispatcher's share is about 15 to 20 seconds per line, roughly two of a clean story's six and a half dispatcher minutes.

Two more costs are inside the agents and cannot be measured from the records, because the agents' own turns are not recorded (the "turns" column on every pull request is the dispatcher's, always about 5; that column is misleading today). Each stage agent spends three to six tool calls on claiming, editing the stage, committing and pushing, intake and demo more for the pull request, and the demo agent copies the whole pull request body on Opus. My estimate is $0.15 to $0.30 per story. The verification run measures it.

## What a model carries today

Per skill and agent: what it decides (judgement or writing) and what it only executes (state, git, GitHub, format).

| Who | Decides | Only executes |
| :- | :- | :- |
| dispatcher (`factory`) | nothing. The skill opens with "You do not judge". The closest are "find the question" (by convention the last log entry) and "the answer says retry" (the only other answer is a close, which is a different line) | re-reading the line's ticket; the pull request state before a stage; checkout, pull, merge `main` in, abort; the task message; the turn-limit resume; stall detection and its log entry, counter, comment; posting a question, `blocked`, `comments_seen`; copying comments into the log and skipping its own; archive, discard, refused-report copy, `outcome`; reopen and draft; round + 1, the three-option question; `reject`; `expired`; deleting branches; log numbering; the closing sentence |
| rules (`factory-rules`) | R8, R9, R13: when to ask, what not to touch | R2 commit at the end, R5 frontmatter, R6 claim with `date -u`, R7 stage edit, R10 branch, push, R11 the gate, R12 rounds, R14 subjects |
| intake | is the story buildable: a concrete Interface, testable criteria, every Interface behaviour and every rule's failing side covered, architecture, scope; the questions; carrying an answer into the story | the branch, the frontmatter, the push, the draft pull request and its body, `pr`, the claim, the stage change; and format checks: the path and id, `FEATURE.md` present, every section present, an `Expect:` per Demo command, the closing criteria last |
| tester | the tests, the boundaries a criterion states, whether a criterion needs interpretation (a question) | claim; "does the ticket come from `doing`" (state the code knows); one `make test`, its last line recorded; `make lint`; stage change, commit, push |
| coder | the code, the refactor, whether a test is wrong (a question), whether an answer calls for a test change (`→ tests`); its commits and their messages | claim; stage change, push; reading `round` to know it is a rework |
| reviewer | the verdict and the findings | claim; a `make check` run of its own; round + 1, the cap, the stage; verdict indentation |
| documenter | what to write, what is stale, a code-versus-docs finding | claim; round, cap, stage, commit, push |
| demo | whether output meets each `Expect:` line and contradicts no criterion | claim; running the Demo blocks and pasting trimmed output; assembling the pull request body from the ticket, copying a fixed paragraph word for word; `gh pr ready`; round, cap, stage, push |
| acceptor | the eight checks, the feature demo, reading the mutants, the verdict, the drafts | the branch; the frontmatter with the sorted `stories`; the draft pull request, its body, the fixed paragraph; `gh pr ready`; summing the cost lines (check 8); the next free story numbers |

## Candidates, ranked

Each judged on: failure classes removed, cost saved per story, testability, flexibility lost, effort, and the dependency on Claude Code as the runtime.

### A — The dispatcher becomes code (rank 1)

`factory-tick` handles every watcher line itself, in Python, and starts the stage agent directly (`claude -p --agent <agent>`, or the agent file's settings passed as flags; see *Runtime*). Everything in the dispatcher row above moves, unchanged in meaning. The agents stay exactly as they are in this step: they still claim, change the stage, commit and push.

- **Removes:** improvisation against the line (7), formatting of the log and the archive (11, 13), and the class "protocol that is wrong but only a live run can show it" (5, 8, 10), which becomes unit-tested. The paths no run has walked (`reject`, the attempts cap, `doing → tests`, two in `ongoing/`) become tests.
- **Saves:** about $0.78 per clean story (42 %), $0.11 to $0.13 per question, answer, close or archive, and 15 to 20 seconds per line.
- **Testability:** every handler runs against a throwaway repository with a bare `origin` and a fake GitHub, like the existing watcher and tick tests.
- **Loses:** the dispatcher's ability to get past a gap the skill did not foresee. Fix 10 shows what that ability did: it hid a defect until someone read the transcripts. In code the same gap is an exception, which the tick already counts, retries and, at the third failure, reports on the pull request. Loud is better than lucky.
- **Effort:** the largest step: Markdown story handling (frontmatter, sections, numbered log), a `gh` wrapper with a fake, the handlers, the agent runner, the tick wiring. Roughly 900 lines of code and tests.
- **Runtime:** the factory no longer needs Claude Code's skill invocation (`/factory`), its subagent tool, or a model to run git. Claude Code remains the agents' runtime, reached through one module.

### B — The stage protocol becomes code (rank 2)

The runner does what R2, R5, R6, R7, R10, R11, R12 and R14 ask of every agent. Before an agent: claim, branch, frontmatter, draft pull request (intake, acceptor), and the facts the agent now infers (rework round and which entry holds the findings, test-change mode for the tester, intake after an answer, the acceptor's archived stories, next free story numbers and cost sum). After: the agent's outcome is read from its structured output (`--json-schema`, a field `outcome`, one of the allowed next stages or `question`, and a field `entry`, the log entry's text), validated against `next`, and applied: round + 1 and the cap, `blocked`, the numbered log entry, the commit subject, the push, and for demo and acceptor the pull request body from a template and `gh pr ready`.

Three checks come with it, all after the agent and before the commit:
- **Lanes on the diff.** The guard hook sees only Edit and Write; a `sed -i` or `>` in Bash passes it. The runner compares every changed path with the lane and restores what lies outside.
- **Frontmatter untouched.** Agents no longer edit it; a changed frontmatter is restored and noted.
- **The gate.** After `tests` (`make lint` green, `make test` red), `doing` and `docs` (`make check` green), the runner runs the target itself and refuses a forward outcome on red: the run counts as a stall, with the output's tail in the log. The reviewer then reads the runner's result instead of running the gate again, so the time roughly evens out.

- **Removes:** illegal stage changes by agents (`reject` remains for hand edits), guessed or missing claims, forgotten pushes, wrong counters, a gate reported green but not run, shell writes outside the lane, and the class of copying fixed text (9). Agents no longer need `git push`, `git checkout`, `git merge` or `gh`; the container's allow list drops them and denies `gh` and `git push` outright. No agent can post on a pull request, which is what made the review-comments plan's `factory:` prefix fragile.
- **Saves:** the agents' protocol turns, estimated at $0.15 to $0.30 per story, plus shorter skills in every agent's context.
- **Testability:** transitions, caps, the lane and frontmatter checks, the pull request bodies: all unit-tested. The agents' remaining instructions are about their work.
- **Loses:** the coder keeps committing its own work (the feature and refactor commits are the reviewer's view); everything else commits through the runner. The pull request body becomes a template: the criteria with the tester's mapping entry beside them instead of a checklist the demo agent assembles.
- **Effort:** medium, about 600 lines, and every skill rewritten shorter.
- **Runtime:** the agent definition shrinks to prompt, model, tools and lane: what any agent runtime takes.

### C — A ticket check in code (rank 3)

`factory-check-story`, called by the runner: the path and id, `FEATURE.md` beside it, every section of `TICKET.md`, an `Expect:` line after every Demo block, the criteria numbered with `make check stays green` and `docs:` last, the log a numbered list. Before intake, a failed check is a question no model can talk away; intake still runs for its judgement, and the runner puts both into one question. After every stage, a failed check is a stall naming the line.

- **Removes:** 16 and 17, and catches any later drift of an agent in the story's shape.
- **Saves:** little money; intake's step 4 gets shorter.
- **Effort:** small, about 200 lines. Needs the runner (A) to call it.

### D — The claim leaves Git (rank 4)

With A and B the runner runs the agent synchronously, under the tick's lock, and knows when the run ends. The claim no longer needs to be a commit: the runner writes `.git/factory-run.json` (story, stage, start) before the agent and removes it after. A file left behind means the run died; the tick handles it as `expired` today (attempts + 1, log entry, comment), and the entrypoint's start time still marks every older claim dead at once. `claimed_at` leaves the frontmatter, which keeps six fields.

- **Removes:** every claim commit (six per story), the push of a claim, and the reason `docs/fewer-commits.md` exists. A pull request like #18 goes from thirteen commits to eight, with no amend and no intake exception.
- **Changes:** the watcher contract: `busy` and `expired` read the run file instead of `claimed_at`. Version 5 of `stages.yml`. The board's "claimed" column reads the file.
- **Loses:** the claim is no longer visible on GitHub, which nobody reads it from.
- **Effort:** small, after B.

### E — Running the Demo blocks in code (not recommended now)

It looks mechanical, and the demo stories show it could be: each block is a self-contained script that starts its server, waits, calls and kills. But there is no evidence of a demo agent altering a command, the saving is small, and a block that misbehaves (a server that does not die, a port in use) is exactly where a model recovers and code would need a process-group timeout and a rule for each case. Leave it with the model; C already checks that every block has its output pasted. Revisit if a run shows a demo agent "fixing" a command.

## What stays with the models, and why

- **Every verdict:** buildable (intake), the verdict and findings (reviewer), output against `Expect:` and the criteria (demo), the feature verdict and the drafts (acceptor). This is where the runs show the models earning their cost.
- **All writing:** tests, code, refactors, documentation, questions, log entries, the acceptance report, proposed stories. Code numbers and places an entry; the model writes it.
- **Interpreting the human's free text where it changes the work:** intake carrying an answer into criteria and Interface, the coder deciding that an answer calls for a test change, the coder reading a close comment as rework. It looks like copying; it is mapping prose onto a structure, and two of the runs' successful paths (13, path 1) were exactly that. Code checks the result's shape afterwards (C).
- **The coder's commits.** The split into feature and refactor commits is a statement about the work, which the reviewer reads.
- **Running the Demo**, for the reasons under E.
- **The turn-limit hand-back.** The runner resumes the session once with "write your outcome now"; whether the partial work makes sense is the model's to say.

The premise fails for two things that look like judgement but are not: "find the question" (by R8 it is the agent's last entry; with B it is the outcome's `entry`) and "does the answer say retry" (the attempts-cap question offers retry or close, and a close is its own line, so any comment is a retry; see the decisions).

## Runtime

The container runs Claude Code 2.1.289. Its CLI has `--agent <agent>`, `--json-schema`, `--append-system-prompt`, `--settings`, `--max-turns`, `--model`, `--permission-mode` and `--resume`; `total_cost_usd` includes subagents, `usage` does not. Not documented: whether `-p --agent` applies the agent file's `skills`, `hooks`, `maxTurns`, `permissionMode` and `effort` when the agent is the main session, and whether a session ended by `--max-turns` can be resumed. The first step of the work is a spike in the container on a throwaway repository (no GitHub, cents): start the coder with `--agent`, confirm the preloaded skills and the guard hook, hit a turn limit and resume, read the result's structured output. If `--agent` does not apply the file, the runner reads the agent file and passes model, tools, skill texts (`--append-system-prompt-file`) and the hook (`--settings`) itself. Either way one module (`agent.py`) knows how an agent is started, and a later move to the Agent SDK or another runtime touches only that module.

## Changes, file by file

All in this repository; the product repositories only pick up a new `stages.yml` from `template/` when D lands.

**A**
1. `src/factory/story.py` (new): read and write a story: frontmatter in a fixed key order, sections by heading, append a numbered log entry (continuation lines indented), insert a line under a heading.
2. `src/factory/github.py` (new): the `gh` calls the dispatcher makes today (view state and comments, create, edit body, ready, ready --undo, reopen, comment), behind a small protocol with a fake for tests. Every comment the factory posts carries a hidden marker `<!-- factory -->`; `comments_seen` keeps its meaning.
3. `src/factory/agent.py` (new): build the command from the agent's name (per the spike), run it, read the JSON result (outcome, cost, turns, denials, max-turns), resume once on a turn limit.
4. `src/factory/dispatch.py` (new): one handler per line kind, as the `factory` skill describes them today, including the pull request check before a stage, the branch preparation and the stall entry with a denied command quoted from the result.
5. `src/factory/tick.py`: `dispatch()` calls the handlers instead of `claude -p "/factory <line>"`; the record per run becomes per agent (turns and tokens are then the agent's); `MUST_COMMIT` and the branch-tip comparison go, because code knows whether it committed; `only_own_comments` uses the marker.
6. `claude/skills/factory/SKILL.md`: deleted. `claude/settings.json`: unchanged in A.
7. `tests/test_story.py`, `tests/test_github.py`, `tests/test_dispatch.py`, `tests/test_agent.py` (new): every handler, including the paths never walked live.
8. `README.md`, `docs/WATCH_CONTRACT.md` (who reads the line), `docs/branching.md` (the dispatcher's commits are the tick's), `docs/diagrams/draw.py` and 03, 07, 08 (the grey "dispatcher, a model" becomes green code), `docs/decisions.md`.

**C**
9. `src/factory/story.py`: the format check, also as `factory-check-story <path>`; tests.
10. `claude/skills/stage-intake/SKILL.md`: step 4 keeps the judgement checks only.

**B**
11. `src/factory/dispatch.py`: the stage protocol before and after an agent, the outcome schema, the lane and frontmatter checks, the gate after `tests`, `doing`, `docs`, the pull request bodies as templates.
12. `claude/skills/factory-rules/SKILL.md`: as under *The rules afterwards*.
13. Every `stage-*` skill: the protocol steps go (claim, stage edit, commit, push, `gh`); each ends with "your outcome". `stage-demo` and `stage-feature` lose the pull request body; `stage-tests` loses step 0's detection and gets the mode from the task; `role-reviewer` reads the runner's gate result instead of running `make check` itself and loses the indentation rule.
14. `claude/agents/*.md`: unchanged frontmatter; the one-line bodies say "end with your outcome".
15. `claude/settings.json`: drop `git push*`, `git checkout *`, `git switch *`, `git merge *`, `git pull*`, `gh pr *` from the allow list; deny `Bash(gh *)` and `Bash(git push*)`.
16. `src/factory/guard.py`: unchanged; the diff check backs it up.

**D**
17. `src/factory/watch.py`, `src/factory/tick.py`: the run file; `busy`/`expired` from it; `outlived_claim` reads it; the board's column.
18. `template/stages.yml`: `version: 5`. `template/TICKET.md`: six fields. `docs/WATCH_CONTRACT.md`: version 5. The entrypoint keeps the run file at start (it is the evidence of a killed run) and removes only the locks.

## The watcher contract afterwards

- Lines, their order and their conditions are unchanged. The consumer of a line is the tick's handler, not a model.
- With D (version 5): the frontmatter holds six fields, `stage`, `pr`, `blocked`, `comments_seen`, `round`, `attempts`. `busy` and `expired` are decided from `.git/factory-run.json` (story and start), with the same lease. Inputs gain that file.
- `reject` stays and now guards against hand edits only; agents cannot make a stage change.
- *What it must not do* is unchanged: the watcher still only reads.

## The rules afterwards

- R1, R3, R4, R9, R13, R15: unchanged in substance.
- R2: every stage ends with an outcome; the runner commits it, a failed run included.
- R5: the frontmatter and the log numbering are the runner's; you write your entry's text; `Assignment` and carried-in criteria stay yours, a new criterion before the two closing ones.
- R6: gone (the runner claims).
- R7: your outcome is one of the stages your task lists, or `question`; the runner checks and applies it. You never move a file.
- R8: to ask, end with `question` and the question as your entry.
- R10: the runner creates branches and pull requests, merges `main` in, commits and pushes. You do not push, check out, merge or call `gh`; the coder commits its work with `ticket <id>:` subjects.
- R11: `make check` must be green before you hand forward; the runner runs it again after `tests`, `doing` and `docs` and refuses red.
- R12: rounds and their cap are the runner's; a rework task names the entry with the findings.
- R14: subjects are the runner's, the coder's work commits excepted.

## Verification

- `make check` green at every commit; for A, the paths of the rebuild log's *Open* list and every handler as tests before anything runs live.
- The spike before A, in the container, on a throwaway repository.
- After all four, one demo run in hardening mode (`demo/README.md`), with deliberate defects for the paths runs 1 to 3 did not walk (`reject` by a hand edit, the attempts cap, a test change approved) plus a close at `accept` and an intake question. What must hold: no `claude -p "/factory …"` in the tick log; every pull request's commits are stage changes and work commits only; the records show the agents' own turns; the clean stories cost about $1.10 each instead of $1.87, which is the claim this plan stands on.

## Effect on the other plans, and the order

- **`docs/clean-before-publish.md`** is not in this repository any more: it was carried out (this repository is its result) and deleted in the first commit, as its last line says. Nothing here touches it.
- **`docs/fewer-commits.md`** becomes obsolete with D: there are no claim commits left to fold away, the intake exception goes because the runner opens the pull request, and no agent amends anything. Without D, the same result is a few lines in the runner (amend its own unpushed claim commit), still no agent rule. Either way the plan as written, an R6 rule and an amend in five skills, should be withdrawn.
- **`docs/review-comments.md`** gets different and smaller. Reading review comments and reviews, copying them into the log and posting replies are the runner's; an agent's reply arrives in its outcome and the runner posts it with the marker, so the loop of the reviewer answering its own replies cannot happen and `gh api` never enters the agents' allow list. The "answer mode" is a task the runner gives the reviewer. Still open, and not fixable by code: GitHub lets nobody request changes on their own pull request, and the factory opens them with the owner's token, so the rework trigger needs either a second account for the factory or another signal (a close after inline comments). Replan it after B.

**Order:** the spike, A, C, B, D, then one verification run; then review comments, replanned on top. Fewer commits is withdrawn. A goes first because it carries most of the cost and most of the untested protocol, and because everything after it needs a runner that starts the agents.

## Decisions for the human

1. **The claim (D).** Out of Git into the runner's file, with the contract at version 5 and `fewer-commits` withdrawn; or kept in the frontmatter, written and committed by the runner, contract unchanged. Recommended: out of Git.
2. **What the human sees and does changes in three places.** The attempts-cap question says "comment anything to retry, close to discard", and any comment retries. The pull request body becomes a template (criteria with the tester's mapping entry instead of an assembled checklist). The factory's own comments carry a hidden marker instead of relying on a `factory:` prefix. Recommended: all three.
3. **How much is verified live, and when.** One demo run after A to D (about $12 at the new price, an hour and a half), or one after A and another after B and D. Recommended: one run at the end. The spike covers the one real unknown, starting agents directly, and everything else is unit-tested before it runs.
