# 17. Limits and backlog

The earlier chapters state every limit of v1 once, in full, in a box beside its mechanism. This chapter collects them, so that a plan can be checked against all of them at once, and adds what v1 left open: documents that disagree with the code, the backlog and the design decisions a next implementation has to take.

## Every limit

Each limit has a number for citing, a short form, the chapter whose box states it, the principle it weakens ([chapter 3](../03-principles/README.md)), and a severity:

- *High:* work can reach the main branch, or something can act in the human's name, without the human; an agent can defeat a rule v1's code claims to enforce (a lane, the undo, a check); or the human's comment or close on the pull request is lost or undone without a word.
- *Medium:* a work item stops, loops or is misreported, and the human is not told, or a project cannot use v1 as intended; found, it can be repaired.
- *Low:* a leftover, a narrow constraint, or a wrong word, with no wrong result.

Limits of the evidence (L1, L72 to L74) are rated by what they leave unproven. A limit fixed since keeps its number and is marked *Fixed*, because plans cite the numbers. Chapter 3's boxes under P2, P12, P15 and P16, and two of the three items under P14, sum up limits stated in full elsewhere; they appear here under their own chapters.

| # | Limit | Ch. | Principle | Severity |
| -: | :- | -: | :- | :- |
| L1 | The evidence is narrow: one project, stories written in advance, a simulated human, one machine | [1](../01-why-a-factory/README.md) | P17 | Medium |
| L2 | Scope beyond a story's assignment is held by instructions alone | [3](../03-principles/README.md) | P3 | Medium |
| L3 | Every story role may edit the criteria its work is judged by | [3](../03-principles/README.md) | P7 | Medium |
| L4 | Some rules have no code: story numbers in code, commit subjects, the contents of a log entry | [3](../03-principles/README.md) | P10 | Low |
| L5 | A restart is charged to the story as a failed attempt | [3](../03-principles/README.md) | P14 | Low |
| L6 | The reverted plans were missing from the decision log until 2026-10-07 | [3](../03-principles/README.md) | P17 | Fixed |
| L7 | Log text is parsed back as data in four places; a renamed role or cost line breaks them silently | [4](../04-work-items/README.md) | P1 | Medium |
| L8 | The identifier format is fixed in code | [4](../04-work-items/README.md) | P15 | Low |
| L9 | Renaming a story in production orphans its branch, state and costs | [4](../04-work-items/README.md) | P2 | Low |
| L10 | Headings are found without regard to code fences | [4](../04-work-items/README.md) | P8 | Low |
| L11 | A draft's own frontmatter wins; a draft promoted with a later `stage:` is never opened, and only the factory's log file says so | [4](../04-work-items/README.md) | P12 | Medium |
| L12 | The feature form is not validated | [4](../04-work-items/README.md) | P8 | Low |
| L13 | The stage table is less configurable than it looks: stage and role names in code; dropping `demo` changes behavior silently | [5](../05-stage-machine/README.md) | P15 | Medium |
| L14 | `stages.yml` has no schema and `version` is never read; a missing `lease_minutes` fails every tick, other errors surface when reached; the factory's own commits need `done` and `doing` in `accept`'s `next` | [5](../05-stage-machine/README.md) | P12 | Medium |
| L15 | An acceptance merged before its gate loops between `merged` and `reject` | [5](../05-stage-machine/README.md) | P12 | Medium |
| L16 | The `max_attempts` comment describes contract version 4 | [5](../05-stage-machine/README.md) | — | Low |
| L17 | `doing → tests` costs no round only because `doing` has no cap | [5](../05-stage-machine/README.md) | — | Low |
| L18 | `reject` sees only the last commit of the checked-out branch, and only targets outside `next` | [6](../06-watcher/README.md) | P10 | Medium |
| L19 | `duplicate`, `error pr-lookup` and an `ask` without a pull request stop the repository and reach only the factory's log file | [6](../06-watcher/README.md) | P12 | Medium |
| L20 | Only the first waiting work item's pull request is read | [6](../06-watcher/README.md) | P4 | Low |
| L21 | A repeated acceptance can trip `reject` and stay `due` forever, silently | [6](../06-watcher/README.md) | P12 | Medium |
| L22 | `--follow` is a leftover | [6](../06-watcher/README.md) | — | Low |
| L23 | `comments_seen` is a count: the factory's own posts swallow the human's comments | [7](../07-dispatcher/README.md) | P2 | High |
| L24 | Posts can repeat after a kill or a failed count | [7](../07-dispatcher/README.md) | P14 | Low |
| L25 | `pr` events bypass the memo: a failing `answers` handler is retried on every tick, and from the third failure the give-up is posted each time | [7](../07-dispatcher/README.md) | P12 | Medium |
| L26 | The give-up message's promise is false, and a failure without a pull request reaches only the factory's log file | [7](../07-dispatcher/README.md) | P12 | Medium |
| L27 | A close at the gate can be undone silently | [7](../07-dispatcher/README.md) | P4 | High |
| L28 | An event without a handler is "nothing to do" | [7](../07-dispatcher/README.md) | P12 | Low |
| L29 | `gh` is reached three ways | [7](../07-dispatcher/README.md) | — | Low |
| L30 | Agent files are not applied as files; six of their keys do nothing | [8](../08-stage-run/README.md) | P10 | Low |
| L31 | The lane is read from the work tree the agent can change | [8](../08-stage-run/README.md) | P10 | High |
| L32 | The undo runs only when the protocol completes; leftovers and the agent's edits to the state fields and the log are committed as they are | [8](../08-stage-run/README.md) | P10, P14 | High |
| L33 | A failed hand-over is never retried; the pull request stays a draft | [8](../08-stage-run/README.md) | P12 | Medium |
| L34 | Each agent call and check gets the full lease as its timeout | [8](../08-stage-run/README.md) | P14 | Low |
| L35 | The instruction layers name `CLAUDE.md`, `make`, `uv` and the factory's own `docs/branching.md` | [9](../09-agents-and-skills/README.md) | P15 | Low |
| L36 | Instructions and code are kept in step by hand, and have drifted | [9](../09-agents-and-skills/README.md) | P10 | Low |
| L37 | Role boundaries rest on lanes alone: one shell vocabulary for all; the documenter can edit generated documentation | [9](../09-agents-and-skills/README.md) | P7 | Medium |
| L38 | The factory's posts may notify nobody, since they come from the human's own token | [10](../10-human-at-the-gate/README.md) | P4 | Medium |
| L39 | Reviews and comments on the diff are never read; the human cannot request changes | [10](../10-human-at-the-gate/README.md) | P4 | Medium |
| L40 | A comment written while the stages work has no defined meaning | [10](../10-human-at-the-gate/README.md) | P4 | Medium |
| L41 | A human comment starting with `factory:` counts as the factory's | [10](../10-human-at-the-gate/README.md) | P2 | Low |
| L42 | Stall notes say "Retrying" at the last attempt | [10](../10-human-at-the-gate/README.md) | P4 | Low |
| L43 | The description is stale while the stages work and overwritten at the gate | [10](../10-human-at-the-gate/README.md) | P4 | Low |
| L44 | Test-only drafts cascade, one acceptance after another | [11](../11-feature-acceptance/README.md) | P12 | Medium |
| L45 | An acceptance's cost line sums every acceptance of its feature | [11](../11-feature-acceptance/README.md) | P16 | Medium |
| L46 | Any draft holds an acceptance back; none can be asked for early | [11](../11-feature-acceptance/README.md) | P3 | Low |
| L47 | The report and the proposed drafts are not validated | [11](../11-feature-acceptance/README.md) | P10 | Low |
| L48 | The acceptor's lane reaches other features and the human's drafts | [11](../11-feature-acceptance/README.md) | P3 | Medium |
| L49 | An acceptance's result holds nothing back: there is no release step | [11](../11-feature-acceptance/README.md) | P3 | Low |
| L50 | The project's toolchain is whatever the factory's image holds | [12](../12-project-contract/README.md) | P15 | Medium |
| L51 | Protected paths are the engine's, exact and at the root | [12](../12-project-contract/README.md) | P15 | Medium |
| L52 | A check can be weakened from inside a lane | [12](../12-project-contract/README.md) | P11 | High |
| L53 | The demonstration project's `layers` target cannot fail | [12](../12-project-contract/README.md) | P11 | Medium |
| L54 | The template does not run as shipped | [12](../12-project-contract/README.md) | P15 | Medium |
| L55 | Nothing verifies a project's setup before the first story | [12](../12-project-contract/README.md) | P12 | Medium |
| L56 | The factory has no identity of its own; it acts on GitHub with the human's token | [13](../13-git-and-github/README.md) | P4 | Medium |
| L57 | The main branch accepts any push the token can make | [13](../13-git-and-github/README.md) | P3 | High |
| L58 | A rejected push stops the work item, mostly in silence | [13](../13-git-and-github/README.md) | P12 | Medium |
| L59 | Nothing checks the GitHub settings | [13](../13-git-and-github/README.md) | P11 | Low |
| L60 | One machine does one thing at a time, across all its repositories | [14](../14-runtime/README.md) | P5 | Medium |
| L61 | Two repositories of the same name share a checkout | [14](../14-runtime/README.md) | — | Low |
| L62 | The bill misses killed and failed agent runs | [14](../14-runtime/README.md) | P16 | Medium |
| L63 | The records live and die with the work volume | [14](../14-runtime/README.md) | P2 | Medium |
| L64 | The machine's own stops never reach a pull request | [14](../14-runtime/README.md) | P12 | Medium |
| L65 | The preflight's probe judges the checked-out branch's code | [14](../14-runtime/README.md) | P12 | Medium |
| L66 | The machine is not reproducible: Claude Code and the base image float | [14](../14-runtime/README.md) | P17 | Medium |
| L67 | Every agent holds the human's GitHub token | [15](../15-safety/README.md) | P3 | High |
| L68 | The allow list does not describe what runs under auto mode | [15](../15-safety/README.md) | P10 | High |
| L69 | Writes outside the tracked work tree outlive the agent run | [15](../15-safety/README.md) | P10 | High |
| L70 | Text from outside reaches the agents unfiltered, comments by anyone included | [15](../15-safety/README.md) | P3 | High |
| L71 | Refused actions are not recorded | [15](../15-safety/README.md) | P16 | Low |
| L72 | Nothing tests the containment or a project's checks | [16](../16-evidence/README.md) | P11 | Medium |
| L73 | Most hardening paths ran live only on generation 4; `reject` never ran live | [16](../16-evidence/README.md) | P17 | Medium |
| L74 | The evidence is not in the repository | [16](../16-evidence/README.md) | P2 | Low |

The ten high limits fall into three groups, and a plan that closes the groups closes most of them:

- *One token for everyone* (L57, L67, L70; its medium cousins are L38, L39 and L56). The factory, every agent and the human act on GitHub as one identity, so nothing on GitHub can tell them apart or protect the main branch against any of them. L70's other half is about authors: a stranger's comment counts as the human's.
- *What an agent's shell can reach* (L31, L32, L52, L68, L69). Lanes are enforced on tracked paths after the stage, and checks trust files inside the lanes; what the shell reaches beyond them, changes before the undo reads them, or plants inside a lane to weaken a check is not enforced.
- *The human's words* (L23, L27). The factory acts on the pull request before it has recorded what the human did there, so its own post or a failed checkout can drop a comment or undo a close (P2).

## Documents that disagree with the code

v1's code changed for three days; its documents did not keep up. Where they disagree, the code is what v1 does (the preface, *What "v1" means*):

| Document | What it says | Chapter |
| :- | :- | -: |
| `README.md` | the dispatcher is a model session; `uv` is "the only tool assumption left" | [12](../12-project-contract/README.md) |
| `demo/README.md` | a story costs $1.50 to $2.20 (generation 4's figures) | [16](../16-evidence/README.md) |
| `docs/WATCH_CONTRACT.md` | the attempts cap sits with the other `ask`; the code tests it later, in `_runnable` | [6](../06-watcher/README.md) |
| `template/stages.yml` | `max_attempts` counts stage runs without a commit (L16) | [5](../05-stage-machine/README.md) |
| `template/TICKET.md` | the demo stage pastes its output below each command | [4](../04-work-items/README.md) |
| `template/README.md`, `template/Makefile` | "lint, types, tests", and a type check that `check` lacks (L54) | [12](../12-project-contract/README.md) |
| `template/CLAUDE.md` | the pipeline knows only three targets (L36) | [9](../09-agents-and-skills/README.md) |
| `stage-review` skill | the factory runs `make check` after the reviewer (L36) | [9](../09-agents-and-skills/README.md) |
| `docs/branching.md` | intake and the acceptor create branches; an answer lands on the main branch; a rejected push is a stall | [13](../13-git-and-github/README.md) |
| `src/factory/preflight.py`, docstring | the dispatcher may offer to run the fixes | [14](../14-runtime/README.md) |
| `docs/diagrams/README.md`, §06 | a running tick finishes before `docker stop`; chapter 14 states the opposite | [14](../14-runtime/README.md) |
| `docs/backlog/README.md` | `doing → tests`, the attempts cap and two stories in production as never run live, though run 3 walked all three and run 4 the first | [16](../16-evidence/README.md) |

## The backlog

v1's open ideas and plans are in the folder `docs/backlog/`, whose [`README.md`](../../backlog/README.md) is the index; built and withdrawn plans are in `docs/archive/`, whose `README.md` marks them as history. Nothing below is in v1's code.

*Plans with a document of their own:*

- **Review comments** ([`docs/backlog/review-comments.md`](../../backlog/review-comments.md)): built and reverted on 2026-10-05; to be replanned with code over rules; its rework path needs an identity of its own (L39, L56; [chapter 3](../03-principles/README.md), P10; [chapter 10](../10-human-at-the-gate/README.md)). Its third path, notes from the human while the stages work, is v1's only proposal for L40.
- **Mutation testing in the story loop** ([`docs/backlog/mutants-in-story-loop.md`](../../backlog/mutants-in-story-loop.md)), parked: `make mutants` after the coder in every story, instead of the cascade (L44; [chapter 11](../11-feature-acceptance/README.md)).

*Ideas:*

- **A development instance**: a second checkout on the main branch serving the application, which the demo stage and the pull request could point to.
- **Releases**: a release step that ships only accepted features, with versions from the changelog's categories and a tag in the archive commit (L49).
- **A changelog**, one user-facing line per story, written by the documenter.
- **Mutation survivors** of the first product repository: material for stories.
- **A language server for the agents**: not now, because agents find code cheaply with `grep`; if it comes back, one type checker for both the agent and the check. Trigger: agents that search in several rounds.
- **Running the Demo blocks in code**, part E of the deterministic core: not built, because a misbehaving block is where a model recovers. Trigger: a demo agent that alters a command.
- **Paths never run live**: v1's list is stale (see the documents table); what stands is L73.
- **Not covered elsewhere**: a watchdog for a dead container (L64), Claude Code's version pinned in the image (L66), browser applications.

*History:* the *fewer commits* plan was built, reverted and withdrawn on 2026-10-05 ([chapter 3](../03-principles/README.md), P10).

## Design decisions left open

v1 left these to the human, or settled them only for itself. A plan puts each one to the human with options and a recommendation, and records the answer and why (P17):

| Design decision | What v1 did, or found | Limits | Where |
| :- | :- | :- | :- |
| *An identity for the factory* | used the human's token; the review-comments plan needs another account or another signal | L38, L39, L56, L57, L67, L70 | [10](../10-human-at-the-gate/README.md), [13](../13-git-and-github/README.md), [15](../15-safety/README.md) |
| *Where a stop the pull request does not show goes* | to the factory's log file or the container's output; P4 allows no third place, P12 wants every stop seen | L11, L19, L26, L33, L55, L58, L64, L65 | [3](../03-principles/README.md), [14](../14-runtime/README.md) |
| *The factory's commits on the main branch* | promotion is the human's commit there, archives and discards the factory's, so no ruleset can require a pull request | L57 | [13](../13-git-and-github/README.md) |
| *Where the bill lives* | machine state until the archive; P2 against P16 left open | L62, L63, L74 | [3](../03-principles/README.md), [14](../14-runtime/README.md) |
| *Leftovers and the undo* | partial work kept without the undo; P14 against P10 left open | L32 | [3](../03-principles/README.md), [8](../08-stage-run/README.md) |
| *Containment* | lanes after the stage, lists before it; Claude Code's sandbox unused and untested in the image | L31, L32, L52, L68, L69, L72 | [15](../15-safety/README.md) |
| *Work in flight* | one agent run per machine; a planned second machine never set up | L60 | [3](../03-principles/README.md) (P5), [14](../14-runtime/README.md) |
| *A project's toolchain* | the factory's image; nothing declares it | L50, L51, L54 | [12](../12-project-contract/README.md) |
| *The agent runtime as a dependency* | `CLAUDE.md`, flags and result format built in; its version unpinned | L30, L35, L66 | [8](../08-stage-run/README.md), [9](../09-agents-and-skills/README.md), [14](../14-runtime/README.md) |
| *The hosting service as a dependency* | GitHub reached three ways; identity, notifications and settings are GitHub's | L29, L38, L56, L59 | [7](../07-dispatcher/README.md), [10](../10-human-at-the-gate/README.md), [13](../13-git-and-github/README.md) |
| *A configurable line* | names fixed in code; roles installed with the image | L8, L13, L14 | [5](../05-stage-machine/README.md) |
| *Comments while the stages work* | no meaning; the human can only close | L23, L40 | [10](../10-human-at-the-gate/README.md) |
| *Mutation testing* | at the acceptance, as drafts; in the story loop, parked | L44 | [11](../11-feature-acceptance/README.md) |

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Every row of the limit table is an acceptance test for a plan**: the plan closes it, keeps it with a reason, or shows it no longer applies. A row is closed only when every clause of its box is. Keeping a high limit needs the human's explicit design decision.
> - **Limits of the evidence** (L1, L72 to L74) are not closed by a mechanism; the plan names the verification that closes them (the Planner box of [chapter 16](../16-evidence/README.md)).
> - **The groups are testable:**
>   - no plan closes L57, L67 or L70 while one token serves the factory, the agents and the human;
>   - no plan closes L31, L32, L52, L68 or L69 without a test that starts an agent and tries a shell write outside the lane, outside the tracked tree, into the lane's configuration and into a check's configuration (L72);
>   - the human's comment or close is recorded in the work item before the factory posts or checks out (L23, L27);
>   - every stop in L11, L19, L26, L33, L55, L58, L64 and L65 reaches the human, or the plan says where else it goes.
> - **The documents table is a warning:** read none of v1's documents as specification where the book or the code says otherwise; read `docs/archive/` as history only, as its `README.md` says.
> - **The backlog is not a plan.** Take the two ideas with triggers only when the trigger is seen; the rest the human picks, in the backlog's own words.
