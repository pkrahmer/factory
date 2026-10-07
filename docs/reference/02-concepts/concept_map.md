# Figure 2-2. The concepts and how they relate

Files: [`concept_map.svg`](concept_map.svg) (the figure), [`concept_map.py`](concept_map.py) (its generator), this description. Used in [chapter 2](README.md).

## What it shows

The factory's vocabulary as one map, in five clusters:
- **the work:** project, feature, story, log, branch, feature acceptance;
- **the line:** stage table, stage, role, lane, check;
- **the agent run:** stage agent, task, instructions, outcome;
- **the control loop:** tick, watcher, event, dispatcher, run record;
- **the human's side:** the human, the pull request.

The relations say which concept contains, defines, reads, starts or acts on which. The relation table below is the authoritative description; the figure may leave out an edge it cannot draw cleanly.

## Elements

| Id | Cluster | Kind | Label | Body text |
| :- | :- | :- | :- | :- |
| project | the work | concept | Project | the repository being built |
| feature | the work | concept | Feature | goal, scope, out of scope |
| story | the work | concept | Story | specification · state · memory |
| log | the work | concept | Log | append-only, numbered |
| branch | the work | concept | Branch | one per work item, until the merge |
| acceptance | the work | concept | Feature acceptance | judges a complete feature |
| table | the line | concept | Stage table | the factory's program |
| stage | the line | concept | Stage | role · next · checks · caps |
| role | the line | concept | Role | instructions · model · tools · budget |
| lane | the line | concept | Lane | the paths a role may write |
| check | the line | concept | Check | a control-surface command |
| agent | the agent run | agent | Stage agent | one role, one stage, one work item |
| task | the agent run | agent | Task | the facts of this run |
| instructions | the agent run | agent | Instructions | rules · role · stage · project guide |
| outcome | the agent run | agent | Outcome | decision + log entry |
| tick | the control loop | code | Tick | wakes on a schedule |
| watcher | the control loop | code | Watcher | snapshot → one event |
| event | the control loop | code | Event | first match wins |
| dispatcher | the control loop | code | Dispatcher | a handler per event |
| run | the control loop | code | Run record | which work item, since when |
| human | the human's side | human | The human | intent and acceptance |
| request | the human's side | store | Pull request | merge · close · comment |

## Relations

| From | To | Kind | Label |
| :- | :- | :- | :- |
| project | feature | plain | contains |
| feature | story | plain | contains |
| feature | acceptance | plain | when complete |
| story | log | plain | has |
| story | branch | plain | lives on |
| branch | request | plain | proposed by |
| project | table | plain | carries |
| table | stage | plain | defines |
| story | stage | plain | is in |
| stage | role | plain | names |
| stage | check | plain | moves forward only after |
| role | lane | plain | may write |
| role | instructions | plain | defined by |
| agent | role | plain | plays |
| agent | story | plain | works on |
| task | agent | flow | given to |
| agent | outcome | flow | ends with |
| tick | watcher | flow | runs |
| watcher | project | plain | reads |
| watcher | request | plain | reads |
| watcher | event | flow | yields |
| event | dispatcher | flow | handled by |
| dispatcher | agent | flow | starts |
| dispatcher | run | flow | records |
| outcome | dispatcher | flow | applied by |
| dispatcher | request | flow | opens · posts · hands over |
| human | story | flow | writes · promotes |
| human | request | flow | merges · closes · comments |

## Layout

A canvas 848 px wide and 1256 px tall, in two columns of clusters above a strip:
- **Right column, top:** the work, as one chain on its left (project, feature, story, log), with the feature acceptance beside the feature and the branch beside the story. Below it, in the same column, the human's side: the pull request under the branch, the human to its left.
- **Left column, top:** the line, to the left of the work: the stage table, the stage and the role in one column, with the check beside the stage and the lane beside the role. Below it the agent run: the task above the stage agent, the instructions below the role and the outcome beside the stage agent.
- **Bottom strip:** the control loop, read from right to left: the watcher under the human's side, then the event, then the dispatcher under the agent run. The tick stands under the watcher and the run record under the dispatcher.

Containment edges run vertically inside a cluster. The story sits level with the stage, so "is in" is one short line; the project's "carries" line bends over the top of the line to the stage table. The watcher's "reads" line to the project runs up the right edge; its line to the pull request is the short one above it. The dispatcher's line to the pull request runs between the human's side and the loop. The figure leaves out one relation it cannot draw without crossing: stage agent → story ("works on"). The table above is complete.

Colors follow the kinds: the work and the line in calm slate (data), the agent run in blue (the model), the loop in green (code), the human in amber, and the pull request as a store. A legend goes at the bottom.

## Reading

- The work and the line are data: files in the project.
- The agent run is the only place a model appears.
- The control loop is code. It is the only thing that writes a story's state and, apart from the human, the only thing that talks to the pull request.
