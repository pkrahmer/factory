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

Three bands, left to right:
- **Left:** the work, with the human's side below it. The feature acceptance sits beside the feature, and the branch beside the story.
- **Center:** the line, with the agent run below it.
- **Right:** the control loop as one column (tick, watcher, event, dispatcher), with the run record beside the dispatcher.

Containment edges run vertically inside a cluster; cross-cluster edges bend around the clusters. The figure leaves out two relations it cannot draw without crossing: stage agent → story ("works on") and watcher → pull request ("reads"). The table above is complete.

Colors follow the kinds: the work and the line in calm slate (data), the agent run in blue (the model), the loop in green (code), the human in amber, and the pull request as a store. A legend goes at the bottom.

## Reading

- The work and the line are data: files in the project.
- The agent run is the only place a model appears.
- The control loop is code. It is the only thing that writes a story's state and, apart from the human, the only thing that talks to the pull request.
