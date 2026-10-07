# Figure 8-1. The stage protocol

Files: [`stage_run_sequence.svg`](stage_run_sequence.svg) (the figure), [`stage_run_sequence.py`](stage_run_sequence.py) (its generator), this description. Used in [chapter 8](README.md).

## What it shows

The steps of one stage in v1, top to bottom, around one agent run: the factory's code in the middle column, the stores it reads and writes on the left (the pull request, the Git checkout and its remote, the run record under `.git/`), and the exits on the right. The agent run is one step; everything above and below it is the factory's. Three exits lead off the main path: a stall, a question, and a failure of the factory itself.

## Elements

Main column, top to bottom (kind `code` unless noted):

| Id | Kind | Title | Body |
| :- | :- | :- | :- |
| prep | code | Prepare the branch | first stage: create it, open a draft pull request · else: fast-forward, merge `main` |
| form1 | code | Validate the form | |
| task | code | Compose the task | |
| rec | code | Write the run record | `.git/factory-run.json` |
| agent | agent | The agent run | `claude -p` · works in its lane · ends with `{outcome, entry}` |
| clear | code | Remove the run record | whatever happened |
| verify | code | Verify the branch | still on the work item's branch? |
| undo | code | Undo outside the lane | paths changed since the start commit |
| restore | code | Restore state and log | |
| outcome | code | Read the outcome | allowed? `stuck`? an error? |
| form2 | code | Validate the form again | a new finding is a stall |
| decide | code | Decide | question · rework · checks, then move |
| commit | code | Commit and push | `<stage> → <next>` |
| hand | code | Hand over at a gate | the description from the story; ready for review |

Side elements:

| Id | Kind | Shape | Title | Body |
| :- | :- | :- | :- | :- |
| gh | store | box | Pull request | draft, then ready |
| git | store | cylinder | Git | the branch, `origin` |
| runrec | store | document | Run record | path, started |
| failure | stall | pill | Failure | counted, retried; the factory's fault |
| stall | stall | box | Stall | attempts + 1, partial work committed, a note on the pull request |
| question | ask | pill | Question | `blocked: question` |

A free note beside the agent run: "the only step where a model runs".

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| prep → form1 → task → rec → agent → clear → verify → undo → restore → outcome → form2 → decide → commit → hand | (next) | flow | |
| prep | gh | plain | open the draft |
| prep | git | plain | checkout, merge |
| rec | runrec | plain | write |
| clear | runrec | plain | remove |
| verify | failure | stall | agent left the branch |
| prep | stall | stall | cannot fast-forward or merge |
| outcome | stall | stall | not kept |
| form2 | stall | stall | form broke |
| decide | stall | stall | a check red |
| decide | question | ask | question, form findings, round cap |
| commit | git | plain | push |
| hand | gh | plain | description, ready |

## Layout

- Canvas 850 × 1,272 px. The main column at x 312 to 560, boxes 248 px wide, 16 px apart; steps without a body are 48 px tall, others 64 px or more.
- Left column: the pull request and Git at the top, beside `prep`; the run record between `rec` and `clear`, with bent lines "write" and "remove"; the failure pill level with `verify`. The return lines from `commit` (push) and `hand` (description, ready) run in the left margin up into Git and the pull request, so each store appears once.
- Right side: the four stall lines join one dashed rail at x 632 that runs from `prep` down to the stall box beside `form2`; the question pill below it, beside `decide`; a key in one column under the question.
- Brackets at the far right: "before the agent" from `prep` to `rec`, "after the agent" from `clear` to `hand`.

## Reading

- The agent run is one step; every other step is code with one right answer.
- Everything that can go wrong ends in a stall (the work item's, counted as an attempt), a question (the human's), or a failure (the factory's, counted and retried); never in a silent move.
