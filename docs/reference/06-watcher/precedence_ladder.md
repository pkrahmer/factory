# Figure 6-1. The order of events

Files: [`precedence_ladder.svg`](precedence_ladder.svg) (the figure), [`precedence_ladder.py`](precedence_ladder.py) (its generator), this description. Used in [chapter 6](README.md).

## What it shows

The watcher's evaluation as a ladder read from the top: seven rungs, each a rule with the events it can return. The first rung that matches returns its event and the evaluation stops. Rungs are grouped in four bands by what they protect: corrections and integrity, the human's signals, the agent at work, new work. A side note marks which events the tick hands to the dispatcher and which it never handles.

## Elements

The rungs, top to bottom, each a box spanning most of the width, with the rule's name as tag, a one-line condition as title and the events as body:

| Id | Band | Kind | Tag | Title | Body (events) |
| :- | :- | :- | :- | :- | :- |
| r1 | Corrections and integrity | stall | `_rejected` | an illegal stage change in the last commit | `reject` |
| r2 | Corrections and integrity | stall | `_duplicated` | two work items with one identifier | `duplicate` |
| r3 | The human's signals | human | `_pull_requests` | the first waiting work item's pull request | `error pr-lookup` · `merged` · `closed` · `pr` |
| r4 | The human's signals | ask | `_asking` | a question to post, or a gate without `pr` | `ask` |
| r5 | The agent at work | code | `_leased` | a run record exists | `busy` · `expired` |
| r6 | New work | agent | `_runnable` | the lowest identifier in a stage with an agent | `ask` (attempts cap) · `run` |
| r7 | New work | quiet | | nothing matched | `idle` |

Notes on the right:

| Id | Kind | Text |
| :- | :- | :- |
| n_never | quiet | never handled by the tick: `busy`, `idle`, and `pr` without new human comments |
| n_hold | human | a waiting work item makes rung 3 match on every tick, so nothing below it runs |

## Connections

| From | To | Kind | Label |
| :- | :- | :- | :- |
| r1 | r2 | plain | no match |
| r2 | r3 | plain | no match |
| r3 | r4 | plain | no match |
| r4 | r5 | plain | no match |
| r5 | r6 | plain | no match |
| r6 | r7 | plain | no match |
| each rung | (right edge) | flow | match: the event |

## Layout

- Canvas 848 × 812 px. Two columns under bold headings, *the rule* (each rung: the rule's name as tag, the condition as one line of body text) and *the event* (a small box per rung, in the rung's color, holding its events; `error pr-lookup` and `ask (attempts cap)` wrap onto their own line).
- Rungs are 56 px tall, 32 px apart, joined by thin "no match" arrows; a solid arrow runs from each rung to its event box.
- Four shaded bands span both columns, labeled at the left: *Corrections and integrity* (rungs 1–2), *The human's signals* (3–4), *The agent at work* (5), *New work* (6–7).
- The two notes stand outside the bands at the far right, without connectors: `n_hold` level with rung 3, `n_never` level with rungs 5 to 7.
- Legend: new work, the human, agent at work, asks the human, a correction, nothing; match: the event, no match: the next rung.

## Reading

- The first match wins: a correction outranks everything, and the human's signals outrank new work.
- Only one event leaves the watcher per evaluation; the tick decides whether it needs handling.
