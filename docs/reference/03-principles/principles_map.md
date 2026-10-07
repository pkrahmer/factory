# Figure 3-1. Where the principles act

Files: [`principles_map.svg`](principles_map.svg) (the figure), [`principles_map.py`](principles_map.py) (its generator), this description. Used in [chapter 3](README.md).

## What it shows

The parts of the factory from Figure 1-1 (the human, the repository, the pull request, the factory's code, the stage agent), each labeled with the principles that govern it. A bottom row adds three things that belong to the factory as a whole: the project contract, the cost records and the decision log. P1, the sorting rule, applies to the whole picture: the colors of the boxes are its three kinds of work.

## Elements

| Id | Kind | Shape | Title | Tag (principles) | Body |
| :- | :- | :- | :- | :- | :- |
| human | human | box | The human | P3 · P4 | starts and accepts · acts in two places |
| repo | store | cylinder | Repository | P2 · P6 · P8 | the only truth · the story is the memory · specified down to the failing side |
| pr | store | document | Pull request | P4 · P9 | the human's channel · where questions go |
| tick | code | box | Tick | P13 | spends on events, not on time |
| watcher | code | box | Watcher | P5 | lowest identifier first; work in flight bounded |
| dispatcher | code | box | Dispatcher | P10 · P11 · P12 · P14 | enforces · observes · stops on the unknown · recovers |
| agent | agent | box | Stage agent | P7 · P9 | does not judge its own work · asks instead of guessing |
| contract | concept | box | Project contract | P15 | control surface · lanes · project guide |
| records | code | cylinder | Cost records | P16 | every agent run measured |
| decisions | concept | document | Decision log | P17 | why, and what was rejected |
| codegroup | group | — | The factory's code | — | encloses tick, watcher and dispatcher |
| banner | text | — | P1 Sort every step: amber the human, blue a model, green code | — | a one-line note under the subtitle or above the content |

## Connections

The same as in Figure 1-1, without labels; they only orient the reader:

| From | To | Kind |
| :- | :- | :- |
| human | repo | flow |
| human | pr | flow |
| tick | watcher | flow |
| watcher | dispatcher | flow |
| dispatcher | agent | flow |
| agent | dispatcher | flow |
| dispatcher | repo | flow |
| dispatcher | pr | flow |

## Layout

A narrow figure, 848 px wide, read from the top down:

- the one-line P1 banner under the subtitle;
- a row of three: the pull request on the left, the human in the middle, the repository on the right; the human's two arrows run left to the pull request and right to the repository;
- below it the factory's code as a group in one full-width row, with the tick, the watcher and the dispatcher from left to right; the dispatcher's two writes leave its top, one straight up to the repository, the other along the channel under the row of three to the pull request;
- the stage agent under the dispatcher, outside the group, with the two arrows between them;
- at the foot, in a shaded band headed "The factory itself", a row of three: project contract, cost records, decision log.

The principle numbers are the tag line of each box (for example "P3 · P4 · P5"), and the body names each principle in a few words. Keep the edges few and quiet; they are context, not content. Legend: human, model, code, store, concept.

## Reading

- Every principle has a home in the picture; none floats free.
- The code group carries the most principles (P5, P10–P14), because that is where order and enforcement live.
- The stage agent carries only two: the models' principles are mostly about what the work item and the human give them.
