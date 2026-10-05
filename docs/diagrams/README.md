# Diagrams

How one story moves through a repository's build, how a finished feature is accepted, and the frame that drives both. Boxes say what happens, arrow labels say what triggers the move; read left to right. Each diagram carries its own legend: blue is an agent stage, amber the human, grey the dispatcher (a model), green deterministic code. The text under each heading holds what the picture leaves out. Click a diagram to open it at full size. The diagrams follow the viewer's light or dark mode (`prefers-color-scheme`) and bring their own background in both, so they stay readable even where a page's theme and the system's differ.

The SVGs are generated: change `draw.py`, then run `uv run python docs/diagrams/draw.py`. Every position is set by hand, so a new box needs room made for it.

## One story in a build

### 01 · Stages

![Stages](01-stages.svg)

- Every arrow is one edit of the `stage` field. A move not listed under `next` in `stages.yml` is rejected by the watcher and moved back by the dispatcher.
- Every way back ends in `doing`, and the story runs the main line again from there. `round` counts all returns together; once it passes `max_rounds` (2), the stage asks the human instead (04).
- Closing the pull request at `accept` sends the story back with your comment as the coder's reason. Without a comment, the dispatcher asks first (04). Requesting changes in a review does the same without a close: your comments on the lines are the coder's findings, and it replies to each.
- Closing it earlier discards the story: the dispatcher checks the pull request before every stage starts. A merge before `accept` counts as acceptance.
- Failing sides are part of the story: intake asks when a rule in the Interface has no criterion for the input it rejects, the tester tests every stated limit on both sides, and the reviewer names a missing failing-side criterion as a finding against the story.
- When the archived story was the feature's last (nothing left in `ongoing/` or `drafts/`), the feature's acceptance is due (05).

### 02 · Lanes

![Lanes](02-lanes.svg)

- A lane is a list of glob patterns under `lanes:` in `stages.yml`. Every agent may also write its own story file. A hook on each agent (`factory-guard <agent>`) refuses any edit outside its lane.
- No lane reaches the human's files: `.claude/`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/stages.yml`, `factory/TICKET.md` and every `FEATURE.md`. No story stage writes `drafts/` or `done/`; only the dispatcher moves a story between folders.
- The acceptor (05) has a lane of its own: the feature's `ACCEPTANCE.md` and new files in `drafts/`, on its branch. They reach `drafts/` on `main` only when the human merges.
- The pull request is not a lane: intake and demo write it with `gh`, which the guard does not cover.
- Rework rounds and questions are not drawn here; they write in the same lanes.

### 03 · One stage run

![One stage run](03-stage-run.svg)

- The acceptor (05) runs the same way: like intake it starts on `main` and creates its branch.
- The claim is a commit that is not pushed. The commit that moves on, sends back or asks amends it and pushes, so the claim never reaches GitHub. Intake and the acceptor push their claim because the pull request needs the branch, and the coder's claim stays under its work commits (R6).
- The agent's task message names the story, its stage, the allowed next stages, the branch and the pull request.
- `make check` must be green before the stage changes. The only exception is `tests`, which leaves the new tests red on purpose.
- An agent that runs out of turns is told once to commit what it has and hand back; only then does the run count as a stall.
- Stalls and rework rounds have separate counters: `attempts` (cap `max_attempts`, 2) and `round` (cap `max_rounds`, 2). Every stall is also a comment on the pull request.

### 04 · Asking the human

![Asking the human](04-asking-the-human.svg)

- `blocked: question` means an agent wrote a question; `blocked: asked` means it is on the pull request. Only while a question is asked does the watcher read the pull request outside `accept`.
- Your three answers:
  - Comment: copied into the log, and the stage that asked runs again. After a close at `accept` that is the coder. After a stall question, "retry" resets `attempts`.
  - Close: discards the story. Your original text goes back to `drafts/`, and the branch is deleted.
  - Mark ready and merge: accepts the story as it is.
- Intake runs again on its existing branch and writes your answer into the story, citing the log entry.
- At `accept`, a comment without a close, on a line or in the conversation, is a question: the reviewer answers it on the pull request and changes nothing. Comments written while the stages work reach the next agent as notes.

## One feature

### 05 · Feature acceptance

![Feature acceptance](05-feature-acceptance.svg)

- Due when the feature has stories in `done/`, none in `ongoing/` or `drafts/`, and no `ACCEPTANCE.md` whose `stories` list matches the archived ones. The report's file is the acceptance's ticket: same seven fields plus `stories`, its own branch `acceptance/<feature>`, its own pull request.
- It runs after the feature's stories in id order (`F0001-S0009 < F0001-todo-service`), and like any stage it can ask, stall or be retried (03, 04).
- The eight checks: scope against `FEATURE.md`, a feature demo run end to end, `make mutants` with the survivors grouped, everything the stories logged as "noticed, not touched", the documentation read as a whole, the decisions taken for the human, slow checks, cost.
- Verdict: `accepted`, `accepted with drafts` or `not accepted`, with reasons. It is a recommendation; your merge or close decides, and the dispatcher records it as `outcome` in the report.
- The proposed stories follow `TICKET.md`, one per coherent change. After a merge they are your drafts: refine them and promote what you want. Nothing starts by itself.
- A close keeps the findings: the report goes to `main` with your comment as the reason, and the next acceptor reads it. Only the proposed drafts are dropped; your comment is the brief for the stories you write instead.
- The acceptance is not a gate on `main`: the stories' code is already there, merged one at a time. `outcome` is the feature's status. `factory-watch --board` shows it per feature as `-`, `due`, `running`, `accepted` or `refused`, and a later release stage will ship only accepted features.

## The frame around it

### 06 · The machine

![The machine](06-machine.svg)

- A single container (`compose.yml`): checkouts live in the `work` volume, the Claude login in `claude-home`.
- After a restart, whatever ran before was killed. Its locks would idle the repository for lease + 10 minutes, so they go; the start time lets the tick expire claims made before it (07).
- Repositories are ticked one after another, never in parallel. `docker stop` ends the wait at once; a running tick finishes first.

### 07 · One tick

![One tick](07-tick.svg)

- State lives under `.git/`, never tracked: `factory-tick.lock`, `factory-tick.json` (last line, HEAD, failures), `factory-preflight-ok`, `factory-tick.log`, and `factory-dispatches.jsonl` (turns, tokens and dollars per dispatcher run).
- The lock is released at the end of every tick. A lock older than lease + 10 minutes belongs to a dead tick and is removed.
- The dispatcher runs as `claude -p "/factory <line>"`: Sonnet, permission mode `auto`, no permission prompts, at most 80 turns. Whatever would have prompted is denied, and the denial is reported on the pull request.
- Exit 3 makes the entrypoint tick again after 2 seconds instead of waiting out the interval: the next stage is probably due.
- Leftovers of an interrupted run are committed on a `ticket/` or `acceptance/` branch; on `main` the tick stops and waits for a human.

### 08 · The watcher

![The watcher](08-watcher.svg)

- The order of the checks is the contract in `docs/WATCH_CONTRACT.md`. `evaluate()` is a pure function, tested without git or GitHub.
- One ticket at a time: a claimed story or acceptance answers `busy` before anything else can run. Ids sort feature by feature, story by story, then the feature's acceptance: `F0001-S0001 < F0001-S0002 < F0001-todo-service < F0002-S0001`.
- A due acceptance is listed with stage `feature` before its `ACCEPTANCE.md` exists; `run acceptor <path> main` follows, and the acceptor creates the file.
- A ticket is read from its branch (`ticket/…` or `acceptance/…`), else from `origin/main`, else from the working tree. A branch already merged into `main` counts as gone.
- A pull request is read only while the human is expected to act. Its `pr` line counts everything written on it (conversation, comments on the diff, review texts) and carries the verdict of the reviews since the story reached `accept`. A change request stands until an approval.
- The watcher only reads: no fetch (the tick fetches), no commit, no checkout, no model. It looks into `drafts/` and `done/` only for the acceptance rule and to count them for the board.

### 09 · The preflight

![The preflight](09-preflight.svg)

- All six checks run every time, so the log names everything missing at once. A check whose tool is missing counts as missing too.
- "agents" covers every agent `stages.yml` names, the acceptor included: a repository whose stage table is newer than the image fails here, not halfway through a feature.
- `make lint`, not `make check`: a ticket branch may be red on purpose, and the probe judges the machine, not the code.
- The fix lines are per platform (apt, dnf, brew, winget). Nothing installs them, and nobody is asked: the human reads the tick log.

## Branches

### 10 · Branches

![Branches](10-branches.svg)

- One trunk, one short branch per ticket, merge commits only. `docs/branching.md` explains it, including who commits where and why a squash merge breaks the watcher.
- The GitHub settings that keep it so are in `docs/github-settings.md`.
