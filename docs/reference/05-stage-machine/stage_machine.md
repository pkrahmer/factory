# Figure 5-1. v1's stage machine

Files: [`stage_machine.svg`](stage_machine.svg) (the figure), [`stage_machine.py`](stage_machine.py) (its generator), this description. Used in [chapter 5](README.md).

## What it shows

Every stage of v1's table with v1's keys, the moves between them, and who causes each move. A story runs down a vertical column from `ready` to `done`. The moves back to `doing` run up the right-hand side. The human's merge and close run down the left-hand side. The feature acceptance is a short line of its own at the bottom right. Questions and stalls do not change the stage; they are shown as two notes, not as arrows, because every agent stage has them.

## Elements

| Id | Kind | Shape | Title | Tag | Body |
| :- | :- | :- | :- | :- | :- |
| drafts | human | document | `drafts/` | HUMAN | the human's text |
| ready | agent | box | `ready` | INTAKE | the branch and draft pull request opened first |
| tests | agent | box | `tests` | TESTER | checks: lint · reports: test |
| doing | agent | box | `doing` | CODER | checks: check |
| review | agent | box | `review` | REVIEWER | max rounds 2 |
| docs | agent | box | `docs` | DOCUMENTER | checks: check · max rounds 2 |
| demo | agent | box | `demo` | DEMO | max rounds 2 |
| accept | human | box | `accept` | GATE | the pull request is ready for the human |
| done | end | pill | `done` | | moved to `done/` |
| feature | agent | box | `feature` | ACCEPTOR | due when the feature is complete |
| accept2 | human | box | `accept` | GATE | the report's pull request |
| booked | end | pill | `done` · accepted or refused | | the report on the main branch |
| note_q | ask | box | A question | QUESTION | any agent stage: `blocked`, the stage stays; the answer runs it again |
| note_s | stall | box | A stall | STALL | any agent stage: attempts + 1, the stage stays; at the cap the human is asked |

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| drafts | ready | flow | promoted (the human) |
| ready | tests | flow | |
| tests | doing | flow | |
| doing | review | flow | |
| review | docs | flow | |
| docs | demo | flow | |
| demo | accept | flow | hand-over |
| accept | done | flow | merged (the human) |
| review | doing | back | round + 1 |
| docs | doing | back | round + 1 |
| demo | doing | back | round + 1 |
| accept | doing | back | closed (the human) · round + 1 |
| doing | tests | back | approved test change · no round |
| any stage `ready` to `demo` | drafts | stall (red, dashed) | closed before the gate: discarded |
| any stage `ready` to `demo` | done | dashed | merged before the gate |
| feature | accept2 | flow | report written |
| accept2 | booked | flow | merged: accepted · closed: refused |

## Layout

- Canvas 850 × 1,160 px.
- *The main column* (x 224 to 400, boxes 176 px wide, 32 px apart) holds `drafts/`, then `ready` down to `accept` and `done`.
- *Right of the column:* the four back arrows into `doing` climb at x 472 to 544, nested so they do not cross: review's innermost and lowest port, the gate's outermost and highest. Each "round + 1" label sits on its arrow's first horizontal run. The `doing → tests` arrow rises right of the forward arrow between the two boxes.
- *Left of the column:* a thin bracket from the top of `ready` to the bottom of `demo`, labeled "any stage before the gate". The discard arrow (red, dashed) runs from its top end up to `drafts/`; the merge-before-the-gate arrow (grey, dashed) runs from its bottom end down to `done`.
- *Bottom right:* the acceptance's own column, `feature` → `accept` → `done · accepted or refused`, in a dashed group captioned "once per complete feature".
- *The two notes* sit at the top right, beside `ready` and `tests`, without arrows.
- Legend: agent stage, the human's gate, end; forward, rework, discard.

## Reading

- An agent's decision applied by the factory, or the human's action, moves a story; the factory's own corrections and a due acceptance are the only other moves (chapter 5 has the full table).
- Every rework goes back to `doing` and costs a round; the approved test change goes from `doing` to `tests` without one.
- Questions and stalls never change the stage: the same stage runs again after the answer or the retry.
