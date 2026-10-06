# Figure 2-1. The shape of a stage table

Files: [`stage_table_shape.svg`](stage_table_shape.svg) (the figure), [`stage_table_shape.py`](stage_table_shape.py) (its generator), this description. Used in [chapter 2](README.md).

## What it shows

The general pattern of a stage table, using v1's line as the example. A story starts as one of the human's drafts. When promoted, it passes a forward line of stages: vet the story, write the tests, write the code, review, document, demonstrate. It then reaches the human's gate and is archived when accepted. Three stages can send the story back to the coding stage, and so can the human at the gate. That is rework, and it costs a round. The coding stage can return the story to the tests stage once the human has approved a test change; that costs no round. Any working stage can stop with a question to the human, and the answer returns to the same stage. While the story is in production, the human can discard it by closing its pull request, which returns it to the drafts untouched. Each box names what happens in the stage, the role that does it, and v1's key for the stage. The feature acceptance, a separate short line of its own, is not drawn here.

## Elements

| Id | Kind | Shape | Title | Tag (role · v1 key) | Body |
| :- | :- | :- | :- | :- | :- |
| drafts | human | document | Draft | HUMAN · drafts/ | the human's text; not worked on |
| intake | agent | box | Vet the story | INTAKE · ready | buildable? exact interface, testable criteria, failing sides |
| tests | agent | box | Write the tests | TESTER · tests | one test per criterion, red on purpose |
| doing | agent | box | Write the code | CODER · doing | until the full check is green; refactor once |
| review | agent | box | Review | REVIEWER · review | the diff against the story and the architecture |
| docs | agent | box | Document | DOCUMENTER · docs | what the reader must know; stale text fixed |
| demo | agent | box | Demonstrate | DEMO · demo | run the commands, compare with the expected output |
| gate | human | box | Accept | GATE · accept | the human merges, or sends back |
| done | end | pill | Archived | done | |
| human | ask | pill | The human answers | QUESTION | on the pull request; the stage that asked runs again |

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| drafts | intake | flow | promoted |
| intake | tests | flow | buildable |
| tests | doing | flow | checks green (lint) |
| doing | review | flow | checks green (full) |
| review | docs | flow | no findings |
| docs | demo | flow | checks green (full) |
| demo | gate | flow | output as expected |
| gate | done | flow | merged |
| review | doing | back | findings · round + 1 |
| docs | doing | back | code contradicts the story · round + 1 |
| demo | doing | back | output wrong · round + 1 |
| gate | doing | back | closed with a reason · round + 1 |
| doing | tests | back | approved test change · no round |
| (any working stage) | human | ask | question |
| human | (the same stage) | ask | answer |
| (any stage before the gate) | drafts | discard (red, dashed) | closed before the gate: discarded |

## Layout

The forward line wraps once, after the tests stage.
- **Top row:** Draft → Vet the story → Write the tests. The question pill sits above Demonstrate, and Archived sits above Accept.
- **Bottom row:** Write the code → Review → Document → Demonstrate → Accept. The columns are aligned with the top row.
- **The wrap:** the arrow `tests → doing` ("checks green (lint)") runs from the tests box down to the code box. The back arrow `doing → tests` ("approved test change · no round") rises beside it without crossing.
- **Rework arcs:** the four arcs run below the bottom row and nest without crossing. Review's arc is the innermost and the gate's the outermost. Their labels form a staircase.
- **Questions:** one representative question/answer pair, drawn as dashed purple arrows, connects Demonstrate with the pill. The pill's body says it comes "from any working stage".
- **Discard:** the arrow starts just before the gate (marked "any stage before the gate"), runs along the bottom, climbs the left edge and enters Draft.
- **Legend:** agent, the human, question, end; forward, rework, question and answer, discard.

## Reading

- Forward moves need the stage's checks green, and the factory runs those checks itself.
- Every rework returns to the stage that writes the code. All reworks share one round counter, including the human's send-back at the gate.
- Nothing moves a story but an agent's decision applied by the factory, or a human action on the pull request.
