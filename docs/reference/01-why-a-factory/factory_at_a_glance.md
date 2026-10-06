# Figure 1-1. The factory at a glance

Files: [`factory_at_a_glance.svg`](factory_at_a_glance.svg) (the figure), [`factory_at_a_glance.py`](factory_at_a_glance.py) (its generator), this description. Used in [chapter 1](README.md).

## What it shows

The factory's parts and how they connect. On one side is the human, who works only through two places: the repository, where they write and start stories, and the pull request, where they answer questions and accept or refuse results. On the other side is the factory's own code, which runs on a schedule. It reads both places, decides the one next thing to do, and either does the bookkeeping itself or starts a stage agent for one stage of one story. The agent is the only place a model runs. It reads the repository, changes files in its lane, and hands back an outcome; the code then commits, pushes and updates the pull request. The human and the agents never talk directly.

## Elements

| Id | Kind | Label | Body text | Meaning |
| :- | :- | :- | :- | :- |
| human | human | The human | writes stories · decides what starts · answers questions · merges or closes | The only source of intent and acceptance |
| repo | store (cylinder) | Repository | features and stories · code, tests, docs · `main` and one branch per story | Git: the single source of truth |
| pr | store (document) | Pull request | one per story · questions and answers · the result, waiting | The human's channel |
| tick | code | Tick | on a schedule: seconds after activity, up to two minutes when quiet · fetches, then evaluates | Wakes the factory; while nothing changes it costs a fetch and no model |
| watcher | code | Watcher | repository and pull request state → the one next event | Reads a snapshot, then decides by a pure function; writes nothing |
| dispatcher | code | Dispatcher | handles the event · branches, checks, commits, pushes, posts | All bookkeeping |
| agent | agent | Stage agent | one stage of one story · reads the story · writes its lane · ends with an outcome | Judgment and writing; the only model |
| codegroup | group | The factory's code | (caption) | Encloses tick, watcher and dispatcher |

## Connections

| From | To | Kind | Label | Meaning |
| :- | :- | :- | :- | :- |
| human | repo | flow | writes and starts stories | The human commits stories and promotes one |
| human | pr | flow | answers · merges · closes | The human acts only on the pull request |
| tick | watcher | flow | evaluate | Each tick runs the watcher once |
| watcher | repo | plain | reads | Branches, story frontmatter, commits |
| watcher | pr | plain | reads | State and comments, only while the human is expected to act |
| watcher | dispatcher | flow | one event | First match wins; at most one event per tick |
| dispatcher | agent | flow | starts, with a task | Only for a "stage is due" event |
| agent | dispatcher | flow | outcome + log entry | Structured: next stage, question or stuck |
| dispatcher | repo | flow | commits, pushes | Every change to the story is the dispatcher's commit (except the coder's work commits) |
| dispatcher | pr | flow | opens · comments · marks ready | Every post carries a hidden marker |
| pr | repo | dashed | a merge lands on `main` | Acceptance moves the story's work into the main line |

## Layout

Three columns, left to right: the human on the left; the two places (pull request at the top, repository at the bottom) in the middle; the factory's code on the right, as a group with tick → watcher → dispatcher in a row along its top and the stage agent below the dispatcher, just outside or at the edge of the group, so it reads as "called by the code, not part of it". Edges from the human go right to the two places; the watcher's reads and the dispatcher's writes go left to the two places. Legend at the bottom: human, model (agent), code, store; flow, reads, dashed.

## Reading

- A model runs in exactly one box.
- The human touches exactly two things, and both are ordinary developer tools.
- All arrows into the repository and the pull request, except the human's, come from code.
