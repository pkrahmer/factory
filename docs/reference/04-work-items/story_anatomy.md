# Figure 4-1. The anatomy of a story file

Files: [`story_anatomy.svg`](story_anatomy.svg) (the figure), [`story_anatomy.py`](story_anatomy.py) (its generator), this description. Used in [chapter 4](README.md).

## What it shows

A story file in production, drawn as one tall document divided into its parts from top to bottom, with the writers of each part on the right. Three bands group the parts by owner: the factory's state at the top, the human's specification in the middle, and the shared log at the bottom. Arrows from the writers to the parts show who may write what. The point of the figure: every part has one owner, agents write only inside the specification (and only in narrow cases), and the log is written only by the factory, on behalf of whoever speaks.

## Elements

The document, on the left, about 400 px wide, is a stack of part boxes inside one document outline (shape `document`, kind `store`, title "F0002-S0001-health-endpoint.md", tag "ONGOING/"). The part boxes, top to bottom:

| Id | Band | Kind | Title | Body |
| :- | :- | :- | :- | :- |
| front | State | code | Frontmatter | `stage` `pr` `blocked` `comments_seen` `round` `attempts` |
| title | Specification | human | `# Health endpoint` | the title |
| assign | Specification | human | `## Assignment (as of log entry 1)` | the current meaning |
| iface | Specification | human | `## Interface` | modules, signatures, errors |
| crit | Specification | human | `## Acceptance criteria` | numbered; last two fixed: `make check` · `docs:` |
| demo | Specification | human | `## Demo` | command blocks, each with `Expect:` |
| log | Log | code | `## Log (append only)` | `1. … human: created.` · `2. intake: …` · `3. human (pull request comment, …): …` · `… done (pull request merged); cost: …` |

The writers, on the right, stacked to line up with the bands:

| Id | Kind | Shape | Title | Tag | Body |
| :- | :- | :- | :- | :- | :- |
| factory | code | box | The factory | CODE | writes state and log; restores both after every agent run |
| human | human | box | The human | HUMAN | writes the draft; speaks in the log through pull request comments |
| roles | agent | box | Stage agents | MODEL | change the specification only to carry in an answer or a changed meaning |

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| factory | front | flow | only writer |
| factory | log | flow | appends every entry |
| human | assign (the whole specification band) | flow | writes the draft |
| roles | assign | dashed | rewritten when a log entry changes the meaning |
| roles | crit | dashed | intake carries in an answer (also into the Interface and the Demo's expectations; drawn once) |
| roles | log | ask | entry text, via the outcome |
| human | log | ask | comments, copied by the factory |

## Layout

- Canvas 848 × 936 px. The document on the left (x 40 to 400) is a rounded outline captioned `ONGOING/F0002-S0001-health-endpoint.md`; the writers are a column on the right (x 560 to 760).
- Three tinted groups inside the document hold the parts, captioned at their top left: *State · the factory's*, *Specification · the human's*, *Log · append-only*. The part boxes are set in monospace.
- The factory box sits level with the frontmatter; its second arrow runs down the far-right channel into the log. The human box sits level with the title; its arrow ends at the specification group's border, and its comment arrow runs down a second channel into the log. The stage-agents box sits level with the Assignment and the criteria; its dashed arrows end at those two parts, and its entry arrow drops into the log.
- The three arrows into the log enter from the right at three heights: entry text (stage agents), comments (the human), appends every entry (the factory).
- Legend in two rows: stage agents, the human's, the factory's; writes, speaks through the factory, may write in narrow cases.

## Reading

- The frontmatter and the log are the factory's alone; an agent's edits there are undone after every agent run.
- The specification is the human's; an agent changes it only to carry in the human's answer, or to keep the Assignment true to the log.
- Everyone speaks in the log, but only the factory writes it, under the next number, with the speaker's prefix.
