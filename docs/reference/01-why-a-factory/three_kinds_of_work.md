# Figure 1-2. Three kinds of work

Files: [`three_kinds_of_work.svg`](three_kinds_of_work.svg) (the figure), [`three_kinds_of_work.py`](three_kinds_of_work.py) (its generator), this description. Used in [chapter 1](README.md).

## What it shows

Every step in producing software is one of three kinds of work, and each kind has one owner. Two questions sort a step.
1. Does the choice decide what is wanted, or whether a result is accepted? If yes, it is intent or acceptance, and it belongs to the human.
2. If not: given the state, is there exactly one right result, and can code reach it without open-ended recovery in the outside world? If yes, it is bookkeeping, and it belongs to code.

Everything else is judgment and writing, and it belongs to a model. Below the questions, each owner's column lists the steps of the health-endpoint story from chapter 1 that fell to it.

## Elements

The decision part, across the top:

| Id | Kind | Shape | Label |
| :- | :- | :- | :- |
| step | concept | pill | A step in the work |
| q1 | concept | diamond | Decides what is wanted or accepted? |
| q2 | concept | diamond | One right result, reachable by code? |

The three columns, below. Each is a group with a header, the example steps, and a footer saying why this owner:

| Column | Kind | Header | Example steps (from the health-endpoint story) | Footer |
| :- | :- | :- | :- | :- |
| human | human | The human: intent and acceptance | start the story · answer "(a)" · merge | Only the human holds the purpose and the accountability |
| model | agent | A model: judgment and writing | is it buildable? · which tests · which code · is it good? · what must a reader know? · does the output match? | Many acceptable results; choosing well takes understanding |
| code | code | Code: bookkeeping | branches · state · commits · posts · checks · counts · the bill | One right result; it must be exact and cheap |

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| step | q1 | flow | |
| q1 | human column | flow | yes |
| q1 | q2 | flow | no |
| q2 | code column | flow | yes |
| q2 | model column | flow | no |

## Layout

The decision flow runs across the top, left to right: the step pill, then q1, then q2. Under it sit three equal columns, left to right: human, model, code. q1 stands above the human column, or between the human and model columns. Its "yes" goes down to the human column, and its "no" goes right to q2. q2 stands above the boundary between the model and code columns. Its "yes" goes down-right to the code column, and its "no" goes down-left to the model column. Arrange the arrows so that none cross.

Each column has:
- a header box in the owner's color;
- the example steps as a compact list, one step per line or small box;
- the footer as a note line in italics.

No legend is needed beyond the column headers. The diamonds hold their questions in two or three short lines; the question text may be shortened to fit, as long as the meaning stays: "Decides what is wanted?" and "One right answer, reachable by code?".

## Reading

- The human's column is short on purpose: three acts in a whole story.
- The model's column is where the judgment lives, and the only place a model works.
- The code column is everything with one right answer.
