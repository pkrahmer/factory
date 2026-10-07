# The factory: a reference

## Preface

### Who this book is for

This book is for two readers at once. The first is a software professional who wants to understand the factory: why it is shaped the way it is, how its parts work together, and what its first implementation does in every detail. The second is a planning agent that will, one day, plan a better implementation from this text. Both read the same chapters. Where the second needs more precision than the first wants to read, a marked box carries it.

### What this book covers

The factory is a small production system around coding agents. The human decides what is built and accepts what was built; models judge and write; ordinary code keeps the books, enforces the rules and talks to the outside world. The book explains that division of labor, the parts that make it executable, and every detail of the first implementation, *v1*: its work items, its stage machine, the code that runs between the agents, the agents' instructions, the human's pull request, the project it builds, the machine it runs on, and how far its safety reaches. It ends with what v1's runs showed, every limit found on the way, and the decisions v1 left open.

The book is not a manual for running v1; v1's `README.md` and `demo/README.md` are. Nor does it teach the tools v1 is built on, such as Git, GitHub, Python or Claude Code; it names what v1 needs from each.

### A map of the book

| Chapter | What it answers |
| :- | :- |
| *Part I, The idea* | general throughout; v1 appears only as evidence and example |
| 1. [Why a factory](01-why-a-factory/README.md) | What does an agent session not give you, and how did v1 find its shape? |
| 2. [Concepts](02-concepts/README.md) | What are the parts: work items, the line, the control loop, the agent run, the human's channel? |
| 3. [Principles](03-principles/README.md) | Which seventeen principles hold the parts together, and how is a design tested against them? |
| *Part II, The machine* | one mechanism per chapter: the concept, *In v1*, v1's limits |
| 4. [Work items](04-work-items/README.md) | What is a story as a file, and who writes which part of it? |
| 5. [The stage machine](05-stage-machine/README.md) | Which moves does the stage table allow, and what does v1's code know by heart? |
| 6. [The watcher](06-watcher/README.md) | How is the one next event found, and in which order? |
| 7. [The dispatcher](07-dispatcher/README.md) | What does each event's handler do, and what happens when it fails? |
| 8. [The stage protocol](08-stage-run/README.md) | What happens before and after one agent run? |
| 9. [Agents, roles and skills](09-agents-and-skills/README.md) | What does each agent read, judge and write, and which rules does code enforce? |
| 10. [The human at the gate](10-human-at-the-gate/README.md) | What does the human see on a pull request, and what does each action mean? |
| 11. [Feature acceptance](11-feature-acceptance/README.md) | How is a whole feature judged, and what comes of the verdict? |
| *Part III, Around the machine* | |
| 12. [The project contract](12-project-contract/README.md) | What must a project provide, and where does v1 still know the project? |
| 13. [Git and GitHub](13-git-and-github/README.md) | Which branches exist, who commits where, and what must GitHub be set to? |
| 14. [The runtime](14-runtime/README.md) | What runs the ticks, what state does it keep, and what does it record? |
| 15. [Safety](15-safety/README.md) | What can an agent run reach, and where does v1's containment end? |
| *Part IV, Looking back* | |
| 16. [Evidence and verification](16-evidence/README.md) | How is v1 tested, and what did its four runs show? |
| 17. [Limits and backlog](17-limits-and-backlog/README.md) | Every limit of v1, the open plans, and the design decisions left open |
| *Appendices* | A, [a glossary](a-glossary/README.md); B, [a map of v1's files](b-v1-file-map/README.md); C, [an index of v1's design decisions](c-decision-index/README.md) |

### How to read this book

*As a professional reader,* read Part I in order: it is the argument, and every later chapter builds on its terms. After that, read what you need. Each chapter of Parts II to IV opens with its concept, which stands alone; *In v1* is specification, best read next to the code; the limit boxes say where v1 falls short. Chapter 2's table *Where each concept lives in v1* leads from any concept to its chapter, and the glossary from any term. The print comes in two editions, with and without the planner boxes.

*As a planning agent,* read everything, the planner boxes included; they separate what is essential from what is incidental to v1. Then use four parts of the book as instruments:
- chapter 3's table *Testing a design against the principles* is the acceptance test for a design: every answer should be *yes*;
- chapter 17's limits, L1 to L74, are a checklist: a plan closes each, keeps it with a reason, or shows it no longer applies;
- chapter 17's design decisions left open are questions for the human, each with the limits it would close;
- appendices B and C lead to v1's files and to the reasons recorded in its decision log.

Keep the two layers apart: the concepts are what any implementation must keep, and v1's choices are what the next one may change. Where the book and v1's code disagree, the code at the commit the book describes is what v1 does.

### What "v1" means

*v1* is the first implementation of the factory: the code, agent definitions and templates in this repository. The book describes it as of commit `930c61a` of 7 October 2026. Its code has not changed since 5 October apart from the default commit address, so the runs of chapter 16 ran on that code or its predecessors. Links to v1's files are relative links into this repository; if the files have moved on since, the commit is what the book describes. Where v1's own documents disagree with its code, the code is what v1 does, and the book says so.

v1 went through five *generations* in three days, which its decision log calls versions 1 to 5. (The stage table's `version:` field is something else: it versions the watcher's contract, and it skipped 3, because generation 3 changed the loop, not the contract.) v1 was exercised by four end-to-end *runs* against the same demonstration project, and run 4 was the first on generation 5. Generations and runs are numbered separately and should not be confused.

### Conventions used in this book

Terms are set in **bold** once, in the chapter where they are defined; this preface and [Appendix A](a-glossary/README.md) list them without bold. Labels in lists and tables are set in *italics*. File names, commands, configuration keys and v1's own identifiers are set in `code`.

Three kinds of boxes appear throughout:

> [!NOTE]
> A note is an aside for the human reader: background, a story from the runs, a comparison.

> [!IMPORTANT]
> **Planner:** a planner box speaks to the agent that will plan the next implementation. It separates what is essential from what is incidental to v1, names invariants and edge cases, and says where v1's code holds the exact behavior.

> [!WARNING]
> **v1 limit:** a limit box names something v1 does not do, does badly, or does only for its first project. Limits are facts about v1, not proposals.

Every figure is an SVG generated by a Python script, and every figure has a description in Markdown beside it, under the same name: `concept_map.svg`, `concept_map.py`, `concept_map.md`. The description is authoritative. It lists every element and connection, so an agent can read the figure without seeing it, and anyone can redraw it.

The person the factory works for is called *the human* throughout, in the book as in v1's own rules and fields: the factory is a pattern, not one person's tool. The text follows American spelling and the house style of technical publishers: *judgment*, *behavior*, *42%*, *$1.87*.

### Words with one meaning

A few words could mean several things in a book about a system built on Git. Each of them means exactly one thing here.

| Word | Means | Does not mean |
| :- | :- | :- |
| *the factory* | the whole system: its code, its agents and its rules | — (v1's documents also say *the pipeline*) |
| *the line* (with the article) | the sequence of stages a story moves through | the main branch; a line of text keeps its ordinary meaning |
| *main branch* | the long-lived branch every accepted change lands on | — |
| *work item* | anything that moves through the line: a story, or a feature's acceptance | — (v1 calls every work item a *ticket*) |
| *log* | a work item's append-only, numbered record | v1's decision log and the factory's log file, which are always named in full |
| *gate* | a stage where the human, not an agent, decides | the checks |
| *check* | a project command that must succeed before a forward move | the human's decision; v1's form validation of a story |
| *reports* | project commands run after a stage whose result is only noted | — (v1's key is `records`) |
| *scheduler* | what wakes the factory again and again | — |
| *tick* | one wake-up: fetch, evaluate, handle at most one event | the scheduler |
| *event* | the one next thing to do, as the watcher determines it | — (v1 calls it a *line*, because it is printed as one) |
| *agent run* | one start of one stage agent, from task to outcome | — (avoid *session* and *stage run*) |
| *run record* | the factory's note that an agent run is in progress | the cost records (v1: the *run file*; earlier generations: the *claim*) |
| *decision* | the first part of an agent's outcome: a next stage, `question` or `stuck` (v1's JSON field is named `outcome`) | the human's decisions, which are named as such; design decisions |
| *design decision* | an entry in a decision log (v1's is `docs/decisions.md`) | an agent's decision |
| *pull request* | the reviewable proposal to merge a work item's branch, with its description and comments (GitLab: *merge request*) | — |
| *contract* | the project contract: what a project provides so the factory can build it | the watcher's contract, which is always named in full |
| *generation* | one of v1's five versions, 1 to 5 | a run |
| *run* (alone) | one of v1's four end-to-end runs on the demonstration project, 1 to 4 | an agent run |

Quotations from v1 keep v1's own words; where they differ from this table, the book glosses them in brackets.
