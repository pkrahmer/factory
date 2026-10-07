# Writing plan for the reference

This file tells a fresh session how to write the rest of the reference in `docs/reference/`. It is self-contained: a session that has read this plan, the preface and Part I knows everything it needs, and nothing depends on an earlier session's memory. It is not part of the book (`_print/book.py` does not pick it up).

## Status

| Part | Chapters | State |
| :- | :- | :- |
| Preface | `README.md` | Front part written (conventions, "Words with one meaning"); the introduction around it is written last |
| I · The idea | 1–3 | Written, two lecturer rounds, trimmed to budget, 5 figures, in print |
| II · The machine | 4–11 | **Next** |
| III · Around the machine | 12–15 | Open |
| IV · Looking back | 16–17 | Open |
| Appendices | A–C | Open |
| Introduction | `README.md` | Last |

Branch `docs/reference` of github.com/pkrahmer/factory; the book describes v1 at commit `537fc20`. Every session updates this table before it ends.

## Starting a session

Give the new session this prompt, with the part filled in:

> Read `docs/reference/WRITING-PLAN.md` in the factory checkout (C:\Dev\Projects\factory, branch `docs/reference`) and write Part II as it describes. Follow its process, its budgets and its rules against filling. Stop and report when the part is committed.

The session then reads, in this order:
1. this plan;
2. the preface, `docs/reference/README.md`, above all the table *Words with one meaning*, which every chapter obeys;
3. Part I, `01-why-a-factory`, `02-concepts`, `03-principles`: the concepts the part builds on and the voice to match;
4. the v1 sources listed for the part's chapters below. Code is the truth; v1's own documents are partly stale (see *Known facts*).

## The book in one paragraph

A reference to the factory for two readers at once: a skilled professional who wants to understand it, and a planning agent that will plan a better implementation from it. Part I is general (idea, concepts, principles P1–P17). Every later chapter goes **concept → *In v1* → v1 limits**: a short general model, then v1's exact behavior, then where v1 falls short. The concepts are what any implementation must keep; v1's choices are what the next one may change.

## The outline, with budgets

The budgets are in words, tables included. Together they come to about 40,000 words, roughly 100 printed pages on top of Part I's 50, so the whole book lands near 150. A chapter may overrun its budget by 15% when its mechanism needs it; beyond that, cut or justify in the report. Figures are planned, not mandatory: draw one only where a picture carries what a table cannot, and keep it **at most 850 px wide** so it prints upright in the text.

### Part II · The machine (8 chapters, about 21,000 words)

**4. Work items** · `04-work-items` · 2,600
- *Concept:* the work-item model; a story's sections and their owners; the state fields; the log's entry format; lifecycle by location; identifiers and order; validation of the form.
- *In v1:*
  - the folder layout `factory/features/<F0001-slug>/{FEATURE.md, drafts/, ongoing/, done/}`;
  - the id patterns (`watch.ID_PATTERN`, `FEATURE_PATTERN`);
  - `template/TICKET.md` and `template/FEATURE.md` section by section;
  - the frontmatter fields and their fixed order (`story.FIELDS`, `TRAILING` for the acceptance);
  - the log entry format: numbering, indented continuation, the prefixes `role:`, `human (pull request comment, <date>):`, `done (pull request merged); cost: …`;
  - `story.append` / `with_log` / `insert_under`;
  - the format check (`story.check`, `check_place`, `_criteria`, `_demo`) and `factory-check-story`.
- *Limits:*
  - log prefixes are parsed back as data (`dispatch._reason_given`, `stage.COST`, `stage._last_by`);
  - the id format is fixed;
  - the leftover `claimed_at`.
- *Figure:* the anatomy of a story file, showing who writes which part.
- *Sources:* `src/factory/story.py`, `watch.py`; `template/`; story F0002-S0001 in factory-demo-todo; design decisions of 2026-10-04 (features and stories, frontmatter fields) and 2026-10-05 (form checked by code).

**5. The stage machine** · `05-stage-machine` · 3,000
- *Concept:* the stage table's schema, and the complete transition model, including the human's events and the factory's own moves.
- *In v1:*
  - `template/stages.yml` field by field: `version`, `root`, `lease_minutes`, `max_attempts`, `lanes`, and per stage `agent`, `next`, `checks`, `records`, `max_rounds`, `gate`;
  - **the full transition table** (from, trigger, to, counters), including:
    - a close at `accept` → `doing`, which costs a round and is compared with `demo`'s `max_rounds`;
    - a discard;
    - a merge before the gate;
    - `reject`;
    - the `feature` stage;
  - **every hard-coded stage or role name** with file and line (see *Known facts*).
- *Limits:*
  - the table is less configurable than it looks;
  - the `max_attempts` comment is stale;
  - `doing → tests` costs no round only because `tests` has no `max_rounds`.
- *Figure:* v1's state machine, laid out vertically to stay within 850 px.
- *Sources:* `template/stages.yml`, `watch.py`, `dispatch.py`, `stage.py`, `ops.py`, `docs/WATCH_CONTRACT.md`, `docs/diagrams/01-stages.svg` (v1's older drawing).

**6. The watcher** · `06-watcher` · 2,600
- *Concept:* readers plus a pure evaluation; the inputs; precedence as a contract; at most one event per tick; the tick's memory.
- *In v1:*
  - `docs/WATCH_CONTRACT.md` (version 5) as the specification, with its line table;
  - `scan_tickets` (branch tip → `origin/main` → working tree, merged branches ignored);
  - `acceptance_ticket` (due, in flight, merged but not booked);
  - `last_change` and `_rejected`;
  - `gh_pr_state`, which polls only stories at a gate or with a question posted;
  - `_runnable` (lowest id; at the attempts cap it emits `ask`);
  - the run record;
  - `--once`, `--follow` and `--board`; the fingerprint; `factory-last-line`.
- *Limits:*
  - `reject` checks only the last commit of the checked-out HEAD and only targets outside `next`;
  - `duplicate` and `error pr-lookup` reach only the tick log, and they stop the whole repository;
  - `--follow` is a leftover;
  - every tick makes one lookup per waiting story.
- *Figure:* the precedence ladder.
- *Sources:* `watch.py`, `docs/WATCH_CONTRACT.md`, `tests/test_watch.py`, `docs/diagrams/08-watcher.svg`.

**7. The dispatcher** · `07-dispatcher` · 3,000
- *Concept:* a handler per event, each with preconditions and effects; at most one commit and push; raise on the unknown; safe to repeat.
- *In v1:* each handler as a specification, preferably one table per handler:
  - `merged`;
  - `closed`, which branches into `_refused` (an acceptance), `_sent_back` (at `accept`: reopen, back to draft, copy comments, round + 1, reason or the three-option question) and `_discard`;
  - `ask` (the attempts-cap text against the last entry);
  - `answers` (copy human comments, unblock, reset attempts at the cap);
  - `reject`, `expired`;
  - `run` (checks the pull request first);
  - `duplicate`, `error`;
  - in `tick.py`: `needs_handling`, `only_own_comments`, the memo (line, HEAD, failures), `MAX_FAILURES = 3`, `give_up`, `outlived_claim`;
  - the `ops` helpers;
  - `github.py`: the marker, the wrapper, the fake used in tests.
- *Limits:*
  - `comments_seen` is a count, and every factory post skips earlier human comments;
  - posting happens before the commit, so a kill can double-post;
  - `gh` is reached three ways;
  - `give_up` needs a pull request.
- *Sources:* `dispatch.py`, `ops.py`, `tick.py`, `github.py`, `repo.py`, `tests/test_dispatch.py`, `tests/test_tick.py`, design decisions of 2026-10-05.

**8. One stage run** · `08-stage-run` · 3,000
- *Concept:* the stage protocol around one agent run; the task; the outcome schema; the lane undo; checks and reports; the hand-over.
- *In v1:*
  - `stage.run` step by step: `_prepare` (branch, fast-forward pull, merge `origin/main`, `_open` for stages that start on main, intake after an answer), `_ensure_pull_request`, the run record, `_task` (its exact lines), `schema()`;
  - `agent.run`: every CLI flag and why, `AGENT_ENV`, the budget resume (a quarter more, at least $0.50), the lease as timeout;
  - after the agent: the branch check, `_undo_out_of_lane`, `_keep_the_dispatchers_parts`, `_outcome`, `_apply`, `_decide`;
  - `_hand_over` and the description templates;
  - the fixed texts: `STORY_CLOSING`, `ACCEPTANCE_CLOSING`, `CAP_QUESTION`, `SENT_BACK_QUESTION`. Quote the exact strings; the planner needs them.
- *Limits:*
  - `--agent` does not apply agent files in print mode (the spike in `docs/deterministic-core.md`);
  - leftovers bypass the undo;
  - agents inherit the environment (point to chapter 15).
- *Figure:* the sequence of one stage run.
- *Sources:* `stage.py`, `agent.py`, `ops.py`, `tests/test_agent.py`, `docs/deterministic-core.md`.

**9. Agents, roles and skills** · `09-agents-and-skills` · 3,000
- *Concept:* the five parts of a role; instruction layers; the judgment each role owns; tuning by turns and reads.
- *In v1:*
  - a table of the seven agent files (model, effort, budget, tools);
  - **the R1–R15 table, moved here from Part I**: rule, short form, principles, enforcement in code;
  - every role and stage skill: its steps, the required contents of its log entry, its decisions;
  - `claude/settings.json`, allow and deny;
  - how `agent.load` builds the prompt; installation (image and entrypoint copy).
- *Limits:* the project guide's file name `CLAUDE.md`, and the skills naming `make`.
- *Sources:* `claude/agents/*.md`, `claude/skills/*/SKILL.md`, `claude/settings.json`, `agent.py`, design decisions of 2026-10-04 (intake on Sonnet, permission mode) and 2026-10-05 (fewer turns).

**10. The human at the gate** · `10-human-at-the-gate` · 2,200
- *Concept:* the pull request's life for one work item; what each human action means; the marker.
- *In v1:*
  - the title and body at creation; the hand-over description;
  - the closing paragraph;
  - the cost-table comment;
  - every kind of comment the factory posts, quoted: the question, a stall, an expired run, the attempts cap, the round cap, the send-back question, `give_up`;
  - the format of copied comments;
  - the marker, and the old `factory:` prefix;
  - merge commits only.
- *Limits:*
  - human comments while the stages work can be skipped;
  - review comments on diff lines are never read;
  - nobody can request changes on their own pull request;
  - the reverted review-comments plan (`docs/review-comments.md`).
- *Sources:* `stage.py`, `dispatch.py`, `github.py`, `tick.py`, `docs/review-comments.md`, demo pull request #35.

**11. Feature acceptance** · `11-feature-acceptance` · 2,200
- *Concept:* judging a complete feature; when an acceptance is due; proposals as drafts; the outcome as the feature's status (later, the gate for a release).
- *In v1:*
  - the due rule (`acceptance_ticket`);
  - the acceptor and its eight checks;
  - the `ACCEPTANCE.md` format (`stories`, `outcome`, Verdict, sections 1–8, Proposed stories);
  - `_open` for an acceptance;
  - `_acceptor_facts` (next free number; cost sum by regex);
  - what happens on a merge and on a close;
  - the board's statuses;
  - `make mutants`;
  - examples from the demo: F0002 "accepted with drafts"; F0001 accepted three times; run 3's refusal over the unpaired-surrogate crash.
- *Limits:*
  - a cascade of test-only follow-up stories (`docs/mutants-in-story-loop.md`, parked);
  - the cost sum is parsed from log text.
- *Sources:* `watch.py`, `stage.py`, `dispatch.py`, the `role-acceptor` and `stage-feature` skills, `factory/features/*/ACCEPTANCE.md` in factory-demo-todo.

### Part III · Around the machine (4 chapters, about 9,000 words)

**12. The project contract** · `12-project-contract` · 2,400
- *Concept:* the control surface, lanes, the project guide, reader documentation, the forms, protected paths, and how another kind of project plugs in (another language; a library; infrastructure).
- *In v1:*
  - `template/` in full: the lanes, the Makefile targets (`check`, `lint`, `test`, `sast`, `secrets`, `licenses`, `mutants`), the sections of `CLAUDE.md`, the README;
  - `demo/project` as the first instance (FastAPI, import-linter, 90% branch coverage, `make openapi`);
  - the guard's never-lists;
  - where the engine assumes `uv`.
- *Sources:* `template/`, `demo/project/`, `guard.py`, `preflight.py`, `entrypoint.sh`, design decisions of 2026-10-04 and 2026-10-05 (the gate grows).

**13. Git and GitHub** · `13-git-and-github` · 1,800
- *In v1:*
  - `docs/branching.md` as the specification;
  - who commits where, including the factory's own commits on `main` (archive, discard, refusal record);
  - merge commits only (a squash reads as `reject`);
  - branch names and their deletion;
  - fetch, fast-forward-only pulls, merging `main` in before each stage;
  - `docs/github-settings.md`: rulesets, tokens, noreply identity.
- *Sources:* `docs/branching.md`, `docs/github-settings.md`, `repo.py`, `dispatch.py`, `entrypoint.sh`.

**14. The runtime** · `14-runtime` · 2,800, including costs and observability (the planned chapter 16 is folded in here)
- *In v1:*
  - `Dockerfile`, `compose.yml`;
  - the entrypoint loop: prepare, lock removal, `FACTORY_STARTED_AT`, the trap, pacing 2 s, then 15 s doubling to 120 s;
  - the tick's flow: lock, preflight stamp (daily, version, hash of `stages.yml`), dirty-tree recovery, fetch, `sync_main`, evaluate, `outlived_claim`, `needs_handling`, `handle_line`;
  - every state file under `.git/`;
  - the preflight's checks;
  - the cost record's format, `costs.py`, the bill at the gate and in the archive entry;
  - the tick log; the board; the changes made on measured grounds (connectors, fewer turns).
- *Limits:*
  - one machine, repositories in turn, one agent run per machine;
  - an agent run killed by a restart leaves no cost record;
  - the records are lost with the volume.
- *Sources:* `Dockerfile`, `compose.yml`, `entrypoint.sh`, `tick.py`, `preflight.py`, `costs.py`, `docs/diagrams/06-*`, `07-*`, `09-*`.

**15. Safety** · `15-safety` · 1,800
- *In v1:*
  - lanes: the guard hook on Edit and Write, and the undo after the stage;
  - the allow and deny lists; `permissionMode: auto`; `--permission-prompts none`;
  - the container user;
  - token scope.
- *Limits (the substance of this chapter; state each with its code location):*
  - agents inherit `GH_TOKEN` (`agent.subprocess_process` passes `os.environ`);
  - `Bash(curl *)` is allowed;
  - `gh auth setup-git` installs a credential helper;
  - `git -C . push` does not match the deny rule `git push*`;
  - shell writes outside the work tree (`.git/hooks`, `~/.claude`) are never undone;
  - leftovers skip the undo;
  - prompt injection can come through story text or dependencies.
- *Sources:* `guard.py`, `stage.py`, `claude/settings.json`, `agent.py`, `entrypoint.sh`, `Dockerfile`.

### Part IV · Looking back (2 chapters, about 5,500 words)

**16. Evidence and verification** · `16-evidence` · 3,000 (the planned chapter 17, Verification, is folded in here)
- *Verification:*
  - the test suite: count, fakes, the pure watcher, throwaway origins;
  - the demo; `scripts/demo-check.sh`;
  - hardening mode and its paths 1–12.
- *Evidence:*
  - the four runs (generation, date, stories, pull requests, agent runs, cost, what they showed);
  - **the 17 fixes as a table** (number, what failed, where the fault sat, the fix);
  - run 4 per story (data below);
  - what is not yet verified: the pinned commit had no full run.
- *Sources:* `tests/`, `demo/README.md`, `scripts/demo-check.sh`, `docs/deterministic-core.md`, and the rebuild log in the local archive checkout `C:\Dev\Projects\factory-archived\docs\rebuild-log.md` (read-only, not public: the book must carry what it needs from it).

**17. Limits and backlog** · `17-limits-and-backlog` · 2,500
- every v1 limit in one table (limit, chapter, principle affected, severity), each pointing to the box that states it in full;
- `docs/backlog.md`;
- the parked and withdrawn plans (`fewer-commits`, `review-comments`, `mutants-in-story-loop`, the language server);
- the open decisions.

### Appendices (about 5,000 words)

- **A. Glossary** · `a-glossary` · 1,500: every term set in bold in the book, with a one-line definition and its chapter.
- **B. v1 file map** · `b-v1-file-map` · 1,000: every tracked file of v1, its purpose, and the chapter that explains it.
- **C. Decision index** · `c-decision-index` · 2,500: every entry of `docs/decisions.md` with an id (D01…), its date, one line, and the chapters citing it.

### The introduction (last)

Complete `docs/reference/README.md`: keep the preface as its front part and add what the book covers, a map of the parts, and how each of the two readers should read it.

## Rules against filling

1. **Every paragraph adds information** that is nowhere else in the book. Anything that restates becomes a cross-reference.
2. **The concept section of a Part II–IV chapter is at most a page.** It gives only the general model this mechanism needs and never re-explains Part I; it points to the chapter and the principle instead.
3. ***In v1* is specification, not narration.** Prefer tables (states, transitions, handlers, fields, formats). Quote exact strings only where the planner needs the exact text; otherwise name the file and the function and link to the file.
4. **Each limit is stated once, in full**, in the chapter of its mechanism, in a `v1 limit` box. Chapter 17 collects them as a table with pointers.
5. **Numbers live in chapter 16.** Elsewhere, cite them; do not repeat the evidence.
6. **The Planner box** at each chapter's end lists what is essential, what is incidental to v1, and what to watch for, as specific and testable items. It is not a summary of the prose.
7. **Every fact is verified against the code**, not against v1's documents. Where a document disagrees with the code, the code is what v1 does, and the book says so.
8. **Keep to the budget.** An overrun above 15% needs a reason in the report.

## Conventions (all already in force in Part I)

- **Voice and spelling:** O'Reilly voice; American spelling (judgment, behavior, labor); "42%", "$1.87".
- **Terms:** exactly as in the preface's table *Words with one meaning*:
  - *agent run*, never "run" alone for one;
  - *check* only for a project command;
  - *gate* only for the human's stage;
  - *event* for v1's "line";
  - *decision* for an agent's outcome; *design decision* for an entry in `docs/decisions.md`;
  - *pull request*;
  - *generation* (1–5) against *run* (1–4).
- **Typography:**
  - Bold once, where a term is defined.
  - Labels in lists and tables in italics.
  - Code, identifiers and file names in backticks.
- **Boxes:** `> [!NOTE]` for the reader; `> [!IMPORTANT]` starting with `**Planner:**`; `> [!WARNING]` starting with `**v1 limit:**`.
- **Links:**
  - to v1's files as relative links into the repository (the print export turns them into footnotes pinned to `537fc20`);
  - to other chapters as `../NN-slug/README.md`;
  - to chapters not yet written: still link, since the print shows them as plain text until they exist.
- **Figures** are triples beside the chapter:
  - `name.md`: the description, authoritative: elements, connections, layout, reading;
  - `name.py`: the generator, using `docs/reference/diagram_kit.py`;
  - `name.svg`.

  In the chapter, a figure is an image line followed by an italic caption paragraph `*Figure N-M. Title: …*`. The print export depends on exactly that shape.

## Process for each chapter

1. **Read the sources** listed for the chapter, the code above all. Note every fact you will state, with its file and function.
2. **Write the chapter** within its budget, following the rules above. Draft the figure descriptions (`.md`) where a figure earns its place.
3. **Draw the figures** with subagents, one per figure, in parallel, each with this brief:
   - read the description and the kit (`diagram_kit.py` docstring, `_sample/sample.py`);
   - write the `.py`; render; `check()` must report 0 warnings;
   - preview light and dark (`uv run python docs/reference/diagram_kit.py preview <svg> [--scale 2 --crop X,Y,W,H]`) and look at the PNGs; iterate at least twice;
   - keep the canvas ≤ 850 px wide;
   - run ruff and `mypy --strict` with `MYPYPATH=docs/reference`;
   - report every deviation from the description.

   Then review every render yourself, and update the description where the drawing changed the layout.
4. **Lecturer review**, one subagent per chapter, as a sparring partner. It reports and does not edit. Mandate:
   - understandability, style and structure;
   - the two audiences;
   - accuracy, checked against the code;
   - **cutting**: everything that is not new information.

   Verify its factual claims against the code before applying them. Apply what holds; push back where a suggestion blurs concept and v1.
5. When the whole part is written, run **one second-round lecturer review over the part**: terms against the preface table, consistency across chapters and with Part I, repetition, length.
6. **Check and print:**
   - `make check` must be green;
   - `make book BOOK_FLAGS=--pages`, then look at `docs/reference/_print/build/sheet.png` (the overview in spreads) and at a few pages up close (`typst compile --root docs/reference/_print docs/reference/_print/build/main.typ "docs/reference/_print/build/hi-{0p}.png" --ppi 100 --pages N`).
7. **Commit** per chapter on `docs/reference`, ending each message with the co-author line in use. Push only when the user says so.
8. **At the end of the part:**
   - update *Status* above and *Known facts* below (what is now placed);
   - send the user the PDF;
   - stop for their review if they want one.

## Data that is not in the repository

**Run 4** (2026-10-05, 16:49–19:36 UTC, generation 5): 59 agent runs, $15.89, from the cost records `.git/factory-dispatches.jsonl` in the container's work volume. That file is wiped by the next demo run; the user has not yet decided whether to keep it as a data file.

| Work item | Agent runs | Agent minutes | Cost | Notes |
| :- | -: | -: | -: | :- |
| F0001-S0001 | 11 | 6.1 | $2.85 | review → doing; the coder asked; approved test change (`doing → tests`) |
| F0001-S0002 | 6 | 2.5 | $1.31 | clean |
| F0001-S0003 | 6 | 4.0 | $1.54 | clean |
| F0001-S0004 | 8 | 5.0 | $1.94 | one review rework |
| F0001 acceptance | 1 | — | $1.59 | the first of three F0001 acceptances |
| F0002-S0001 | 7 | 2.8 | $1.36 | intake question, answered "(a)"; the running example of Part I |
| F0002-S0002 | 6 | 2.1 | $0.85 | clean |
| F0002-S0003 | 6 | 2.2 | $1.12 | clean |
| F0002 acceptance | 1 | 5.0 | $1.47 | accepted with drafts (S0004, S0005) |
| F0003-S0001 | 6 | 2.3 | $1.00 | clean |
| F0003 acceptance | 1 | 3.1 | $0.87 | |

- **Averages:**
  - clean stories average $1.16;
  - all eight stories average $1.50;
  - one acceptance costs $0.87–1.59.
- **After run 4:** further work ran on later commits.
  - F0001-S0005, S0006 and S0007 cost $0.97, $0.54 and $0.47, at 6 agent runs each.
  - Two more F0001 acceptances ran at 21:05 and 21:24 UTC, for $1.62 and $1.60.
  - The container image built at 20:59:48 UTC includes commit `8498e64`, the last code change before `537fc20`.
- **Run 2** (generation 4): a clean story cost $1.87, of which $0.78 was the dispatcher model (`docs/deterministic-core.md`).

## Known facts to place

Found while writing Part I, verified against the code. Each belongs in the chapter named.

- **WIP is one agent run per machine** (ch. 6, 14). `factory-tick` runs the agent synchronously while holding its lock, and the entrypoint ticks repositories in turn, so `busy` is almost never seen in the container. The run record matters for agent runs that died. `docs/WATCH_CONTRACT.md` says the run record enforces WIP 1, which is only half true.
- **A lower identifier can start between two stages of another story** (ch. 5, 6). Two stories are then in production, and the later one's merge of `main` can conflict, which is a stall.
- **The counters** (ch. 5):
  - attempts count per story across stages and are reset only by the human's answer at the cap;
  - rounds never reset;
  - the human's close at `accept` costs a round, compared with `demo`'s `max_rounds` (`dispatch.py`, `_sent_back`).
- **`comments_seen` is a count** (ch. 7, 10). Every factory post sets it to the count after its own post, so earlier unread human comments are skipped.
- **A kill can double-post** (ch. 7). `ask`, `expired` and `ops.stall` post before they commit.
- **A killed agent run leaves no cost record** (ch. 14, 16). `tick.record` writes only after `dispatch.handle` returns.
- **Two events are handled silently** (ch. 6, 7). `duplicate` and `error pr-lookup` return `Handled(True)` and reach only the tick log, and they outrank all other events.
- **`reject` sees little** (ch. 6). It checks only `HEAD~1..HEAD` of the checked-out branch and only targets outside `next`; merges and subjects containing "moved back" are exempt.
- **Hard-coded names** (ch. 5):
  - `watch.MAIN_STAGES` (`ready`, `feature`);
  - `dispatch._sent_back` (`accept`, `doing`, `demo`'s `max_rounds`);
  - `dispatch._reason_given` (`demo`);
  - `stage._task` (`tests`, `coder:`, `ready`);
  - `stage._story_body` (`tester`, `reviewer`, `documenter`, `demo`);
  - `stage.current` (`done`);
  - `ops.stall` (the default `ready`).
- **Safety gaps** (ch. 15): `GH_TOKEN` inherited by agents; `curl *` allowed; the credential helper; `git -C . push`; writes outside the work tree never undone.
- **Leftovers** (ch. 14, 15). `tick.recover_dirty_tree` commits an interrupted agent run's leftovers with `git add -A` and no lane undo.
- **`uv` is assumed** (ch. 12). The preflight requires `uv` and `.venv`, and the entrypoint runs `uv sync`. `guard.NEVER_FILES` names Python, uv, make and Claude Code files, and `NEVER_NAMES` blocks any `FEATURE.md`.
- **The `version:` field in `stages.yml`** went 1 → 2 → 4 → 5 (ch. 5, 16). Generation 3 changed the loop, not the contract.
- **Stale v1 documents** (ch. 16, 17). `README.md` still describes the dispatcher as a model session, `demo/README.md` still gives $1.50–2.20 a story, and the `max_attempts` comment in `stages.yml` is stale.
- **The reverted plans** (ch. 10, 17). Two plans of 2026-10-05 (*fewer commits*, *review comments*) were built and reverted the same day. The revert is in neither `docs/decisions.md` nor the history, because `main` was reset.
- **A restart wipes the tick's memory** (ch. 14). The entrypoint deletes `factory-tick.json` at start, so the last handled event is forgotten.

## Tools and pitfalls

- **Figures:**
  - the kit is `docs/reference/diagram_kit.py`; render with `uv run python docs/reference/diagram_kit.py render [script]`;
  - `mypy` finds the kit only with `MYPYPATH=docs/reference`;
  - the kit has no italic or inline emphasis yet, so `three_kinds_of_work.py` and `principles_map.py` add them by subclassing `Diagram`; fold this into the kit when a new figure needs it;
  - the SVG attribute `aria-labelledby` is spelled that way on purpose: never run a blanket spelling replacement over code.
- **Print:**
  - `make book` (pandoc and typst are installed on the PC with winget); `BOOK_FLAGS=--reader` for the edition without planner boxes; `--pages` for page images and the overview sheet;
  - new chapter folders `NN-slug` and appendix folders `a-slug` are picked up automatically;
  - `PARTS` in `_print/book.py` maps the first chapter of each part (Part IV starts at 16);
  - links to chapters that do not exist print as plain text.
- **Editing on this Windows machine:** heredocs that pass backslash escapes (`\n`) to Python or sed get mangled. Write scripts to a file with the Write tool, or use the Edit tool for exact replacements.
- **Repositories:**
  - the running container `factory-factory-1`: do not touch it; read-only `docker compose exec -T factory sh -c '…'` from `C:\Dev\Projects\factory` is fine;
  - `C:\Dev\Projects\factory-archived` (old history, rebuild log): read only; never pull or push there;
  - `C:\Dev\Projects\factory-demo-todo` (pkrahmer/factory-demo-todo): the demo's stories, acceptance reports and history; read only.

## Open decisions for the user

1. Add a design decision to `docs/decisions.md` for the reverted plans of 2026-10-05?
2. Keep run 4's cost records as a data file for chapter 16?
3. Redraw Part I's five figures at most 850 px wide, so that they print upright in the text instead of on pages of their own?
4. When to merge `docs/reference` into `main`?
