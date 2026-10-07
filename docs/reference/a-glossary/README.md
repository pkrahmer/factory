# A. Glossary

This appendix lists every term the book sets in bold where it defines it, and the words of the preface's table *Words with one meaning*, each in one line with the chapter that defines it. Where v1 calls a thing by another word, the entry gives it. The words sort by their noun: *the human* under H.

| Term | Meaning | Chapter |
| :- | :- | :- |
| *acceptance criteria* | A story's numbered criteria, each testable by one test. | [2](../02-concepts/README.md) |
| *acceptor* | The role that judges a whole feature in its feature acceptance. | [2](../02-concepts/README.md) |
| *agent run* | One start of one stage agent, from task to outcome; never *run* alone, *session* or *stage run*. | [Preface](../README.md) |
| *archive* | The factory's move of an accepted story into the archive, setting its last stage (v1: `done/`). | [2](../02-concepts/README.md) |
| *assignment* | What to build and why, in a paragraph that always states the story's current meaning. | [2](../02-concepts/README.md) |
| *attempt* | One stall, counted against the story; at the project's cap, the human is asked whether to retry. | [2](../02-concepts/README.md) |
| *blocked* | Of a story with an open question, recorded and committed first, then posted (v1: `blocked: question`, then `blocked: asked`). | [2](../02-concepts/README.md) |
| *bookkeeping* | Steps with exactly one right result, which code can reach without open-ended recovery in the outside world; code's. | [1](../01-why-a-factory/README.md) |
| *branch* | A work item's own branch, from its first stage to its acceptance, unseen by the main branch until the human merges. | [2](../02-concepts/README.md) |
| *budget* | How much one agent run of a role may cost. | [2](../02-concepts/README.md) |
| *check* | A project command that must succeed before a forward move; not the human's decision, nor v1's form validation. | [Preface](../README.md) |
| *clean* | Of a story: every stage passed the first time, with no question and no rework. | [16](../16-evidence/README.md) |
| *comments read* | How many comments on the pull request the factory has taken in (v1: `comments_seen`). | [2](../02-concepts/README.md) |
| *complete* | Of a feature: archived stories and nothing else, no drafts, nothing in production. | [2](../02-concepts/README.md) |
| *contract* | The project contract; the watcher's contract is always named in full. | [Preface](../README.md) |
| *control surface* | The few commands through which the factory reaches a project's tools: a full check, a lint, a test run (v1: `make` targets). | [2](../02-concepts/README.md) |
| *cost records* | One line per agent run with its duration, tokens and cost, giving each story its bill (v1: `.git/factory-dispatches.jsonl`). | [2](../02-concepts/README.md) |
| *decision* | The first part of an outcome: a next stage, `question` or `stuck` (v1's JSON field `outcome`, not `ACCEPTANCE.md`'s); not the human's, nor a design decision. | [2](../02-concepts/README.md) |
| *demonstration* | Commands to run, each followed by the output it must show. | [2](../02-concepts/README.md) |
| *design decision* | An entry in a decision log (v1's is `docs/decisions.md`); not an agent's decision. | [Preface](../README.md) |
| *discard* | The factory's return of an abandoned story to the drafts, untouched; its branch is deleted. | [2](../02-concepts/README.md) |
| *dispatcher* | What handles the event, with one handler per kind. | [2](../02-concepts/README.md) |
| *docs criterion* | One of the two criteria closing every story: what a reader must know after it, if only `none` with a reason. | [2](../02-concepts/README.md) |
| *draft* | A story that is still the human's text; the factory does not work on it (v1: `drafts/`). | [2](../02-concepts/README.md) |
| *end-to-end run* | The factory building a real project, with a person or an agent playing the human; its real test suite. | [16](../16-evidence/README.md) |
| *entry* | The second part of an outcome: the text of the agent's log entry. | [2](../02-concepts/README.md) |
| *event* | The one next thing to do, as the watcher determines it (v1: a *line*). | [2](../02-concepts/README.md) |
| *the factory* | The whole system: its code, its agents and its rules (v1's documents also say *the pipeline*). | [Preface](../README.md) |
| *the factory's log file* | Where the tick writes what it did, one time-stamped line each, also in the container's output (v1: the tick log, `.git/factory-tick.log`). | [14](../14-runtime/README.md) |
| *failing sides* | Errors, limits and rejected inputs, which the criteria cover too. | [2](../02-concepts/README.md) |
| *failure* | The factory's, not the story's: a handler could not handle an event; retried a fixed number of times. | [2](../02-concepts/README.md) |
| *feature* | A coherent piece of value with a goal, a scope and an explicit *out of scope*. | [2](../02-concepts/README.md) |
| *feature acceptance* | The work item due when a feature is complete: the acceptor's stage, then a gate (v1: `ACCEPTANCE.md`). | [2](../02-concepts/README.md) |
| *forward move* | The first stage listed in a stage's *next*; kept only if the stage's checks succeed. | [2](../02-concepts/README.md) |
| *gate* | A stage where the human, not an agent, decides, declared explicitly; not the checks. | [2](../02-concepts/README.md) |
| *generation* | One of the five shapes v1 went through, 1 to 5 (its decision log: *versions*); not a run, nor the stage table's `version:`. | [1](../01-why-a-factory/README.md) |
| *handler* | The code for one kind of event, specified by its preconditions, effects and result. | [7](../07-dispatcher/README.md) |
| *hardening run* | An end-to-end run whose stories carry deliberate defects, one per path the factory must handle. | [16](../16-evidence/README.md) |
| *the human* | The person the factory works for, who promotes stories and accepts results by merging. | [1](../01-why-a-factory/README.md) |
| *identifier* | The sortable id of a feature or story; the sort order is the only priority (v1: `F0002`, `F0002-S0001`). | [2](../02-concepts/README.md) |
| *in production* | The lifecycle state of a promoted story; only then does it have a stage (v1: `ongoing/`). | [2](../02-concepts/README.md) |
| *instructions* | What a role does, judges and never does, in four layers. | [2](../02-concepts/README.md) |
| *intent and acceptance* | Steps that decide what is wanted or whether a result is accepted; the human's. | [1](../01-why-a-factory/README.md) |
| *interface* | Exact module paths, names, signatures, error types and routes, which the tests are written against. | [2](../02-concepts/README.md) |
| *judgment and writing* | Every step that is neither intent and acceptance nor bookkeeping; a model's. | [1](../01-why-a-factory/README.md) |
| *lane* | The list of paths a role may write, enforced by refusing the write and by an undo afterwards. | [2](../02-concepts/README.md) |
| *lease* | The maximum duration of an agent run; one older than it, or one a restart left behind, is dead (v1: `lease_minutes`). | [2](../02-concepts/README.md) |
| *lifecycle* | A story's coordinate saying whose it is, shown by location: draft, in production, archived. | [2](../02-concepts/README.md) |
| *the line* | The sequence of stages a story moves through; not the main branch. | [2](../02-concepts/README.md) |
| *log* | A work item's append-only, numbered record; not v1's decision log or the factory's log file. | [2](../02-concepts/README.md) |
| *machine* | What the factory runs on, with the tools, the agent runtime and the credentials (v1: a Docker container). | [2](../02-concepts/README.md) |
| *main branch* | The long-lived branch every accepted change lands on. | [2](../02-concepts/README.md) |
| *marker* | The hidden mark on everything the factory posts, telling its comments from the human's. | [2](../02-concepts/README.md) |
| *memo* | The tick's note per project: the last event handled, the repository state, the handler's failures (v1: `.git/factory-tick.json`). | [7](../07-dispatcher/README.md) |
| *model* | The model that plays a role, with its reasoning effort. | [2](../02-concepts/README.md) |
| *move back* | Any other stage listed in *next*: a move to a stage that can fix what was found. | [2](../02-concepts/README.md) |
| *outcome* | A stage agent's structured answer in a fixed shape: a decision and an entry (v1: JSON `{outcome, entry}`). | [2](../02-concepts/README.md) |
| *preflight* | What verifies the machine before it works: tools, identity, hosting service, installed agents, control surface. | [2](../02-concepts/README.md) |
| *project* | The repository the factory builds; the factory never owns it. | [2](../02-concepts/README.md) |
| *project contract* | What a project provides so the factory can build it: stage table, forms, guide, control surface, reader documentation, hosting service. | [2](../02-concepts/README.md) |
| *project guide* | The project's own architecture, conventions and things nobody may do without asking (v1: `CLAUDE.md`). | [2](../02-concepts/README.md) |
| *promote* | The human's act that starts a draft (v1: moving it into `ongoing/` and pushing). | [2](../02-concepts/README.md) |
| *protected paths* | The files that decide how a project is built and judged; no lane reaches them. | [12](../12-project-contract/README.md) |
| *pull request* | The reviewable proposal to merge a work item's branch, with its description and comments (GitLab: *merge request*). | [2](../02-concepts/README.md) |
| *question* | A choice handed to the human, by an agent ending with `question` (its entry is the question) or by the factory at a cap. | [2](../02-concepts/README.md) |
| *reports* | Project commands run after a stage whose result is only noted (v1's stage-table key: `records`; not the cost records). | [Preface](../README.md) |
| *rework* | A move back because the work is not good enough, to the stage that can fix it; it costs a round. | [2](../02-concepts/README.md) |
| *role* | A responsibility on the line, defined by its instructions, model, tools, budget and lane. | [2](../02-concepts/README.md) |
| *role instructions* | The layer that says what one role is and what it checks (v1: the `role-*` skills). | [2](../02-concepts/README.md) |
| *round* | What each rework costs, per story; each sending stage has its own cap. | [2](../02-concepts/README.md) |
| *rules* | The layer of instructions every agent works under (v1: the skill `factory-rules`). | [2](../02-concepts/README.md) |
| *run* (alone) | One of v1's four end-to-end runs on the demonstration project, 1 to 4; not an agent run. | [Preface](../README.md) |
| *run record* | The factory's note that an agent run is in progress (v1: `.git/factory-run.json`; earlier generations: the field `claimed_at`, the *claim*); not the cost records. | [2](../02-concepts/README.md) |
| *runtime* | Everything around the control loop that is not the project: machine, checkouts, scheduler, state outside version control; not the agent runtime. | [14](../14-runtime/README.md) |
| *scheduler* | The only permanent part: what wakes the factory again and again. | [2](../02-concepts/README.md) |
| *stage* | A state in which at most one role acts; a story has one only while in production. | [2](../02-concepts/README.md) |
| *stage agent* | One fresh agent run: a model playing one role, for one stage, of one work item. | [2](../02-concepts/README.md) |
| *stage instructions* | The layer for one stage: its steps, its entry, which decisions mean what (v1: the `stage-*` skills). | [2](../02-concepts/README.md) |
| *stage protocol* | The factory's steps around every agent, the same, in the same order, for every stage. | [2](../02-concepts/README.md) |
| *stage table* | The configuration a project carries: stages, roles, allowed moves (v1: `factory/stages.yml`). | [2](../02-concepts/README.md) |
| *stall* | A stage that ended without a result the factory can keep; it costs an attempt. | [2](../02-concepts/README.md) |
| *story* | The unit of production, small enough for one pass: specification, state and memory in one document. | [2](../02-concepts/README.md) |
| *task* | The factory's short message to a stage agent, naming everything it already knows. | [2](../02-concepts/README.md) |
| *tick* | One wake-up: fetch, evaluate, handle at most one event; not the scheduler. | [2](../02-concepts/README.md) |
| *tools* | What a role may use: read, search, edit, write, run commands. | [2](../02-concepts/README.md) |
| *transition* | A move between stages: an agent's decision applied by the factory, or the human's action; the factory's own moves are in chapter 5. | [2](../02-concepts/README.md) |
| *trunk-based development* | One long-lived main branch and a short branch per work item. | [13](../13-git-and-github/README.md) |
| *unit test* | A test of the code against fakes of the hosting service and the agent runtime. | [16](../16-evidence/README.md) |
| *verdict* | The acceptor's recommendation; the human's merge or close, not the verdict, decides the feature's status. | [11](../11-feature-acceptance/README.md) |
| *wait* | Of a work item: it has a pull request and is at a gate or has its question posted (v1: `blocked: asked`). | [6](../06-watcher/README.md) |
| *watcher* | Readers that take a snapshot, and a pure function that turns it into exactly one event. | [2](../02-concepts/README.md) |
| *where the fault sat* | Each defect's place: code, a model on a step with one right result, a protocol only prose described, or wording. | [16](../16-evidence/README.md) |
| *work item* | Anything that moves through the line: a story, or a feature's acceptance (v1: *ticket*). | [2](../02-concepts/README.md) |
| *work-in-progress limit* | The cap on what is in flight; v1's is one agent run per project, in practice one per machine. | [2](../02-concepts/README.md) |
