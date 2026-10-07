# Figure 13-1. Branches

Files: [`branches.svg`](branches.svg) (the figure), [`branches.py`](branches.py) (its generator), this description. Used in [chapter 13](README.md).

## What it shows

The branches of one clean story and of its feature's acceptance, in time order: one long-lived main branch, and a short branch per work item that leaves the main branch when the work item's first stage is due and comes back by the human's merge commit. Each commit is drawn as a dot colored by who makes it: the human, the coder (the only agent that commits), or the factory's code. Beside each work item's branch runs its pull request's state, draft and then ready.

The figure redraws v1's own picture, [`docs/diagrams/10-branches.svg`](../../diagrams/10-branches.svg), which runs left to right at 2,100 px. Deviations from it, each checked against the code:
- *The merge of the main branch* is drawn once, after the main branch has moved, and labeled "only when `main` moved". v1's picture labels it "every stage"; `stage._prepare` calls `repo.merge_main` before every stage on an existing branch, but `git merge` makes a commit only when `origin/main` has moved.
- *The merge comes before the coder's commits*, because it happens before the `doing` stage's agent starts.
- *Commit labels are the subjects' second halves*, as the factory writes them (`ticket <id>: ready → tests`); m5 and m7 drop the subject's tail "(pull request merged)". v1's picture abbreviates some.
- *The booking of the acceptance* names the field it writes, `outcome: accepted`.

## Elements

Three lanes, each a vertical line with its branch name at the top:

| Id | Lane | Label | Meaning |
| :- | :- | :- | :- |
| ticket | left | `ticket/<file stem>` | One story's branch; exists from `intake starts` until the archive deletes it |
| main | middle | `main` | The trunk; runs the full height |
| acceptance | right | `acceptance/<feature>` | One feature's acceptance; exists from `acceptance starts` until the booking deletes it |

Commits, top to bottom, one row each:

| Id | Lane | Who | Label | Meaning |
| :- | :- | :- | :- | :- |
| m1 | main | human | drafts and `FEATURE.md` | The human writes the feature and its stories as drafts |
| m2 | main | human | promote: `git mv` into `ongoing/` | Starting the story is a commit on the main branch |
| t1 | ticket | factory | `intake starts` · draft pull request | `stage._open`: branch from `main`, state fields written, draft pull request opened |
| t2 | ticket | factory | `ready → tests` | Intake's decision applied |
| t3 | ticket | factory | `tests → doing` | The tester's decision applied, after the lint |
| m3 | main | human | another draft | The main branch moves while the story is on its branch |
| t4 | ticket | factory | `merge main` · only when `main` moved | `repo.merge_main` before the `doing` stage; a conflict would be a stall |
| t5 | ticket | coder | `feat(<layer>): …` | The coder's work commit |
| t6 | ticket | coder | `refactor: …` | The coder's refactor, if any |
| t7 | ticket | factory | `doing → review` | After `make check` passed |
| t8 | ticket | factory | `review → docs` | The reviewer's decision applied |
| t9 | ticket | factory | `docs → demo` | After `make check` passed |
| t10 | ticket | factory | `demo → accept` · ready | The hand-over: the description written, the pull request marked ready |
| m4 | main | human | merge commit, never a squash | The human accepts on GitHub |
| m5 | main | factory | `accept → done`: archived into `done/` · branch deleted | `dispatch.merged`; the ticket lane ends here |
| a1 | acceptance | factory | `acceptance starts` · draft pull request | The feature is complete, so its acceptance is due; `stage._open` again |
| a2 | acceptance | factory | `feature → accept` · ready | The acceptor's report and proposed drafts, handed over |
| m6 | main | human | merge commit: report and drafts | The human accepts the report; its drafts land in `drafts/` |
| m7 | main | factory | `accept → done`, `outcome: accepted` · branch deleted | `dispatch.merged` books the acceptance; the acceptance lane ends here |

Pull request bands, each a narrow vertical bar beside its lane:

| Id | Beside | Spans | Label |
| :- | :- | :- | :- |
| pr-story-draft | ticket | t1 to t10 | draft |
| pr-story-ready | ticket | t10 to m4 | ready |
| pr-acc-draft | acceptance | a1 to a2 | draft |
| pr-acc-ready | acceptance | a2 to m6 | ready |

## Connections

| From | To | Kind | Meaning |
| :- | :- | :- | :- |
| m2 | t1 | branch line | The story's branch leaves the main branch at the promotion |
| m3 | t4 | merge line | The main branch merged into the story's branch |
| t10 | m4 | merge line | The human's merge commit |
| m5 | a1 | branch line | The acceptance's branch leaves the main branch after the last archive |
| a2 | m6 | merge line | The human's merge of the report |

Consecutive commits on a lane are joined by the lane's line; the ticket and acceptance lanes are drawn only between their first and last commit.

## Layout

Canvas 850 × 1,128 px, top to bottom; the kit's title ("Branches: one trunk, a short branch per work item") and subtitle on top, which the print crops. Three lane columns 192 px apart: `ticket/<file stem>` on the left, `main` in the middle, `acceptance/<feature>` on the right, each headed by its branch name. The main branch is a thick line the full height; the two work items' lanes are solid only between their first and last commit, with a faint dotted guide from the branch name down to the first commit. One row per commit, 48 px apart, in the order of the table. Commit dots are circles filled in the color of who made them: amber for the human, blue for the coder's work (a model), green for the factory's code, as in Part I's figures. Labels are one or two lines: the ticket lane's to its left, right-aligned; the acceptance lane's to its right; the main branch's on the side away from the diagonal at that row (m5 and m6 on the left, the others on the right). Branch and merge lines are straight diagonals between the dots, without arrowheads; the colors of the dots show who acted. The pull request bands are narrow dashed bars right beside their lanes, on the outer side, with the labels beyond them; draft in a neutral fill, ready in the amber of the human's turn, each with its word set vertically inside. Legend at the bottom: the human, the coder's work, the factory's code; pull request, draft; pull request, ready.

## Reading

- One trunk, one short branch per work item, and merge commits only: everything a work item does stays on its branch until the human merges.
- Almost every commit on a work item's branch is the factory's; the coder's work commits are the only ones an agent makes.
- In this figure the factory commits on the main branch only after the human's merge: the archive, then the booking. Chapter 13's table adds the refusal record, the discard and `reject`'s correction.
- A clean story leaves seven commits of the factory's on its branch, the first and one per stage result, plus a merge of the main branch when it moved, and the coder's.
