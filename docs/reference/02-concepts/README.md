# 2. Concepts

Chapter 1 followed one story, the health endpoint, through the factory in a few paragraphs. This chapter follows it again, slowly, and names each concept at the moment the story meets it: where the story lives, the line it moves along, who notices that it has been started, what happens in one of its stages, what happens when a stage cannot move it forward, how the human talks to it, and what happens when its feature is complete.

Every concept here is general. It does not depend on a language, a toolchain, a hosting service or an agent runtime. The health-endpoint story was built by v1, so its details are v1's: file names, folder names, numbers. Where they appear, they are examples. A table at the end of the chapter maps every concept to its place in v1 and to the chapter that has the details.

## The work

### Project, feature, story

A **project** is the repository the factory builds: its code, its tests, its documentation, and the files that tell the factory how to work on it. The factory never owns a project. It is a guest with a narrow set of permissions, and the project's own files say how the project is built.

The human plans the work as **features**. A feature is a coherent piece of value with a goal, a scope, and an explicit *out of scope*. The health endpoint belongs to a feature called *Operations*, whose goal is "an operator can tell from outside whether the service is up, which version runs and with which storage, and how many todos are open and done". Its scope lists three things: a health endpoint, a version command and statistics. Its out of scope names metrics export, logging configuration and deployment, so that no story drifts there.

A feature is too large to build in one step and too vague to test, so it is cut into **stories**. A story is the unit of production: small enough that one pass through the stages builds it, typically a few minutes of agent time and a few dozen to a few hundred lines of change. The health endpoint is the first of the Operations stories.

### The story as a document

A story is also a document, and the document has three jobs at once.

*Specification.* It says what to build, and how to know when it is built:
- an **assignment**: what is to be built and why, in a paragraph, always stating the story's *current* meaning;
- an **interface**: exact module paths, names, signatures, error types and routes, because the tests are written against it;
- numbered **acceptance criteria**, each testable by one test;
- a **demonstration**: commands to run, each followed by the output it must show.

*State.* Where the story stands: its stage, its pull request, whether it waits for an answer, how many rounds and failed attempts it has spent. This is a handful of fields at the top of the document, and only the factory writes them.

*Memory.* An append-only, numbered **log**. Every stage, the human and the factory itself append entries to it: what was done, why, what was rejected, what is open. Agents start fresh for every stage and know nothing that is not in the repository. The log is how one stage tells the next what it needs.

Two criteria close every story, whatever it is about. The project's full check stays green, and a **docs criterion** says what a reader must know after this story. Documentation that no criterion asks for does not get written, so every story must say what it needs, if only `none` with a reason.

The criteria cover the **failing sides** too. If an interface says a title is at most 200 characters, a criterion says what happens with 201. Errors, limits and rejected inputs are product choices, and product choices are the human's, so they belong in the specification and not in a tester's imagination. The health endpoint's first draft missed exactly one: its interface said that an empty storage setting means in-memory storage, but no criterion tested it. That gap is what the first stage asked about.

### Work items

Most of what moves through the factory is stories, but not all of it. A feature's acceptance (described below) goes through the same machinery. A **work item** is anything that moves through the line: a story, or a feature's acceptance. v1 calls every work item a *ticket*: its story form is `TICKET.md`, its story branches are named `ticket/…`, and its rules for agents say "ticket" throughout.

### Order

Features and stories carry **identifiers** that sort: feature `F0002`, story `F0002-S0001`. The sort order is the priority. The factory works on the lowest identifier first, feature by feature, story by story, and a feature's acceptance sorts after its stories. There is no other prioritization, so the human controls the order completely, by numbering and by choosing what to start.

### Two coordinates: lifecycle and stage

A story has two coordinates, and they must not be confused.

Its **lifecycle** says whose it is, and the factory shows it by location:
- A **draft** is the human's text, which the factory does not work on.
- The human **promotes** a draft to start it, and the story is then **in production**. In v1, promoting means moving the file into the feature's `ongoing/` folder and pushing; that is how the health endpoint was started.
- When the human accepts the result, the factory **archives** the story (in v1, into `done/`).
- If the human abandons the story on the way, the factory **discards** it: the file goes back among the drafts, untouched, so the human's text survives.

Only a story in production has the second coordinate, its *stage*: where it is on the line. Promotion moves the story into production without setting a stage; the first stage starts from there. Archiving sets the last stage and moves the story into the archive in the same commit.

A feature is **complete** when it has archived stories and nothing else: no drafts, nothing in production.

### A branch per work item

From its first stage to its acceptance, a story lives on a **branch** of its own. Its work, its state and its log are committed there, and the **main branch** sees none of it until the human merges. That is why a merge is acceptance and a discard deletes the branch. It is also why every stage begins by bringing the story's branch up to date with the main branch: each stage builds on whatever has been accepted since. The health endpoint lived on `ticket/F0002-S0001-health-endpoint` for eight minutes.

### The state of a story in production

Six facts describe a story in production completely. All six are kept in the story's own fields, and only the factory writes them.

| State | Values | Changes when | Resets when |
| :- | :- | :- | :- |
| *stage* | one of the stages in the stage table | the factory applies an agent's decision, or the human acts at a gate | — |
| *pull request* | its number, once opened | the factory opens it before the first stage | — |
| *question* | none · *recorded* · *posted* | *recorded* when an agent asks or the factory needs the human; *posted* once it is on the pull request | back to none when the human's answer is copied into the log |
| **comments read** | how many comments on the pull request the factory has taken in | whenever the factory reads or posts | — |
| *rounds* | a count | each time a stage sends the story back for rework, and each time the human sends it back at the gate | never; it is capped instead (see below) |
| *attempts* | a count | each time a stage ends without a result the factory can keep | when the human answers the question the attempt cap raised |

## The line

### Stages

A promoted story moves through **stages**. A stage is a state in which at most one role acts. The sequence of stages is **the line**. The line v1 ships with:

| Stage (v1 key) | Role | What happens |
| :- | :- | :- |
| Vet the story (`ready`) | intake | Is it buildable: an exact interface, testable criteria, failing sides, a runnable demonstration, within the feature's scope? |
| Write the tests (`tests`) | tester | One test per criterion, written before the code exists, red on purpose |
| Write the code (`doing`) | coder | Until the tests pass and the full check is green; refactor once |
| Review (`review`) | reviewer | The diff against the story, the architecture and security |
| Document (`docs`) | documenter | What the reader must know now; stale documentation fixed |
| Demonstrate (`demo`) | demo | Run the story's commands, compare the output with what the story expects |
| Accept (`accept`) | none: a gate | The human merges, or sends the story back |
| Archived (`done`) | none: the end | — |
| Judge the feature (`feature`) | acceptor | Once per complete feature (see *The feature's acceptance*) |

### The stage table

The stages, the role that acts in each and the moves allowed out of each are not code. They are configuration, in a **stage table** that the project carries. The stage table is the factory's program. For each stage it says:

| Entry | Meaning |
| :- | :- |
| *role* | Who works in this stage. A stage without a role is either a gate or the end of the line. |
| *gate* | Marks a stage where the human, not an agent, decides. A **gate** is declared explicitly; a missing role alone does not make one. |
| *next* | The stages the story may move to. The first entry is the **forward** move; the others are moves **back**, to a stage that can fix what was found. |
| *checks* | Project commands that must succeed before the factory keeps a forward move. A failing check holds the story where it is. |
| *reports* | Project commands the factory runs after the stage and notes in the log, passing or failing, without holding anything. |
| *max rounds* | How many rework rounds the story may have spent when this stage sends it back, before the human is asked instead. |

A move between stages is a **transition**, and transitions happen for exactly two reasons: an agent's decision, applied by the factory, or the human's action on the pull request. A stage change the table does not allow, such as a hand edit or a mistake, is detected and moved back. (How thoroughly v1 detects it is a matter for [chapter 6](../06-watcher/README.md).)

![Figure 2-1. The shape of a stage table](stage_table_shape.svg)

*Figure 2-1. The shape of a stage table: a forward line from the first stage to the human's gate, moves back to the stage that writes the code, and questions that leave the line for the human.*

The shape in Figure 2-1 is a pattern, not a law. It encodes a few convictions that [chapter 3](../03-principles/README.md) argues for:
- the specification is checked before anyone builds;
- tests are written before the code, by someone else;
- review, documentation and demonstration are separate perspectives;
- the human has the last word.

A project of another kind would carry another table built from the same parts: a library without a demonstration, a data pipeline with a validation stage, infrastructure code with a plan-and-apply step.

## The control loop

Nobody told the factory that the health endpoint had been started. The human pushed a commit, and the factory noticed. Noticing is the job of the control loop.

### Scheduler and tick

Nothing in the factory waits in memory between steps. A **scheduler**, the only permanent part, wakes the factory for each project in turn. One wake-up is a **tick**: fetch the latest state, evaluate it, and handle at most one thing. A tick that finds nothing to do costs a network fetch, plus one lookup on the hosting service for each story that waits for the human; no model runs. A tick that handled something is followed at once by another, because the next step is usually due. After that, ticks are spaced further and further apart, up to a ceiling.

The tick remembers the last event it handled and the repository state it saw, so the same event in the same state is handled only once. If handling fails, the tick retries a few times, and then reports the failure to the human (see *When a story does not move forward*).

### Watcher and events

The evaluation is the **watcher**'s job. It has two halves. Readers collect a snapshot of the repository and of the pull requests that wait for the human. A pure function then turns the snapshot into exactly one **event**: the one next thing to do. Because the function is pure, the same snapshot always yields the same event, and it can be tested case by case without a repository or a network. Neither half writes anything.

### Dispatcher

The **dispatcher** handles the event, with one handler per kind of event. The events, in the order in which they are checked (the first that applies wins), with what the dispatcher does about each:

| Event (first match wins) | What the dispatcher does |
| :- | :- |
| A stage change the table does not allow | Moves it back, and says so on the pull request |
| Two stories with the same identifier | Reports it; nothing moves until the human fixes it |
| A pull request the factory cannot read | Reports it; nothing moves until the hosting service answers |
| A pull request merged | Archives the story on the main branch; deletes its branch |
| A pull request closed | Sends the story back, discards it or records a refusal, depending on the stage |
| New comments on a pull request that waits for the human | Copies them into the log; an answer unblocks the story |
| A question recorded but not yet posted | Posts it on the pull request |
| An agent run in progress | Nothing: an agent is at work |
| An agent run that died | Clears its run record and counts a failed attempt; the stage will run again |
| A stage is due | Runs the stage protocol; the only event that starts a model |
| Nothing | Nothing |

The order is part of the watcher's contract. Corrections come first, then the human's signals, then new work. A story that waits for the human, at a gate or with a question posted, therefore stops all new work in its project until the human acts.

When the human pushed the promotion, the next tick's watcher found the health endpoint at its first stage with nothing outranking it: *a stage is due*. The dispatcher took it from there.

### Run record, lease and the work-in-progress limit

While an agent works, the factory keeps a **run record**: which work item, since when. The run record has a **lease**, a maximum duration. An agent run older than its lease, or one left behind by a machine that restarted, is dead; its story counts a failed attempt and the stage runs again.

The **work-in-progress limit** caps how much is in flight. v1's limit is one agent run, and in practice one per machine: the tick waits for its agent, and the machine ticks its projects one after another, so no second agent run starts anywhere while one is at work. The run record backs this up and catches the agent runs that died. Within a project, a story that waits for the human also outranks all new work in the event order. A story promoted with a lower identifier still goes first when it gets the chance, between two stages of another, so two stories can be in production at once: numbering is the only priority.

## One stage, one agent run

The health endpoint's first stage went like every other: one agent run, with the same parts around it.

### Roles and agents

A **role** is a responsibility on the line: intake, tester, coder, reviewer, documenter, demo, acceptor. A role is defined by five things:
- its **instructions**: what to do, what to judge, what never to do;
- the **model** that plays it, and how much reasoning effort it spends;
- the **tools** it may use: read, search, edit, write, run commands;
- its **budget**: how much one agent run may cost;
- its *lane*: the set of paths in the project it may write (below).

The factory ships the roles: their instructions, models, tools and budgets are the same for every project. The lane is the exception. Only the project knows where its tests and sources live, so lanes are part of the project's stage table.

A **stage agent** is one fresh run of a model, playing one role, for one stage, of one work item. It has no memory of earlier agent runs and no conversation with other agents. Everything it knows comes from three sources: its instructions, its task and the repository itself.

The **task** is a short message from the factory naming everything the factory already knows:
- the work item and its stage;
- the decisions the stage table allows;
- the branch and the pull request;
- the round;
- whatever facts this stage needs.

When intake ran again after the human's answer, its task said so, and it said whether the story's form had passed the factory's own format validation.

### Instructions in layers

Instructions come in layers, so each is written once and reused:
- the **rules** every agent works under, whatever its role: version control is the truth, the story is the memory, ask instead of guessing, touch no other role's files;
- the **role instructions**: what a tester is, what a reviewer checks and in what order;
- the **stage instructions**: the steps of this stage, what the log entry must contain, which decisions mean what;
- the **project guide**: the project's own architecture, test conventions, documentation layout, and its list of things nobody may do without asking. This layer belongs to the project, not to the factory.

v1 calls the first three *skills* and the fourth `CLAUDE.md`, after the conventions of its agent runtime ([chapter 9](../09-agents-and-skills/README.md)).

### Lanes

A **lane** is the list of paths a role may write. The tester writes tests, the coder writes source code and the files generated from it, the documenter writes prose. Every role that works on a story may also write that story's own document, outside its state fields and its log. Some files are in no lane at all, because they belong to the human:
- the stage table;
- the story form;
- the project guide;
- the build configuration;
- every feature description.

Lanes do two jobs. They keep roles honest: a coder that cannot write tests cannot make a failing test pass by changing it. And they limit the damage any one run can do. A lane is enforced twice: once while the agent works, by refusing the write, and once afterwards, by undoing any change outside the lane, however it was made.

### Outcomes

Every stage agent ends with an **outcome**: a small, structured answer in a fixed shape, not a sentence in prose. It has two parts:
- the **decision**: one of the stages the table allows next, or `question` (the agent needs the human), or `stuck` (it cannot finish, and says where it stopped);
- the **entry**: the text of the agent's log entry, which says what it did, why, what it rejected and what is open.

The agent decides; the factory applies. Agents do not change a story's state, do not push, and do not talk to the hosting service. They do not commit either, with one deliberate exception. A role whose commits are part of what the next role judges may commit its own work. In v1 that is the coder, because the reviewer reads how the work was split into commits. Even the coder never commits a stage change.

### The stage protocol

Around the agent, the factory runs the **stage protocol**: the same steps for every stage, in the same order.

Before the agent:
1. Bring the work item's branch up to date with the main branch. At the first stage, create the branch, write the story's state fields, and open a draft pull request.
2. Write the run record.
3. Compose the task.

Then start the agent, and wait for its outcome.

After the agent:
1. Check that the agent is still on its branch.
2. Undo every write outside its lane.
3. Restore the story's state fields and log to what they were.
4. Check the decision against the stage table.
5. Validate the story's form.
6. For a move back, count a round, and ask the human instead once the stage's cap is passed.
7. For a forward move, run the stage's checks, and hold the story if one fails. Run the stage's reports and note their results.
8. Append the entry to the log as the next numbered entry.
9. Commit and push.
10. If the story has reached a gate, write the pull request's description from the story and hand it over to the human.

When the health endpoint's tester ended with `doing`, the factory ran the project's lint as the stage's check (green) and its tests as the stage's report (red, as they had to be: the code did not exist yet). It noted both in the log under the tester's entry, committed, and pushed. Then the next tick started the coder.

## When a story does not move forward

A line that only goes forward is a line that hides its problems. The factory distinguishes four ways a story can fail to move forward, and keeps them apart because each needs a different response.

| | Rework | Stall | Question | Failure |
| :- | :- | :- | :- | :- |
| *What it is* | A judgment that the work is not good enough | A stage that ended without a result the factory can keep | A stage that needs the human to decide | The factory itself could not handle an event |
| *Who decides* | A role (reviewer, documenter, demo), or the human at the gate | The factory | A role, or the factory at a cap | The factory |
| *What is counted* | rounds, per story | attempts, per story | — | failures, per event and repository state |
| *Cap* | the sending stage's max rounds | the project's max attempts | — | a fixed number of retries |
| *At the cap* | the human is asked | the human is asked whether to retry | (goes to the human at once) | the human is told on the pull request, and retries stop |
| *Reset* | never | by the human's answer at the cap | — | when the repository state changes |

A **rework** sends a story back because the work is not good enough: the reviewer found a defect, the documenter found the code contradicting the interface, or the demonstration did not show what the story promised. The findings are the latest log entries, and the stage that can fix them, the coder's in v1, runs again with them in front of it. Each rework costs a **round**. A story has one round counter, shared by every stage that can send it back and by the human's send-back at the gate, and each stage compares it with its own cap. Not every move back is a rework. When the human approves a change to a test, the coding stage returns the story to the tests stage, and that costs no round.

A **stall** is a stage that ended without a result the factory can keep. That can happen in several ways:
- the agent ended with `stuck`, crashed, or ran out of budget;
- its agent run died, because the lease ran out or the machine restarted;
- it gave a decision the table does not allow;
- it broke the story's form;
- a forward move met a failing check;
- the factory could not prepare the stage, because the story's branch no longer merges with the main branch.

Each stall counts one **attempt** against the story, the story stays where it is, and the stage runs again. The count covers all stages together. At the cap the factory stops retrying and asks the human whether to try again; any answer is a retry, and resets the count. Every stall is also a message on the pull request: a stall only the machine knows about is a stall nobody knows about.

A **question** hands a choice to the human. Perhaps the story is ambiguous, a criterion contradicts the interface, a test seems wrong, or the project guide says to ask. The agent ends with `question`, and its entry is the question. The story is then **blocked**, in two steps that the factory keeps apart so that a crash between them loses nothing. First the question is recorded and committed; then it is posted on the pull request. The human's answer comes back as a log entry, and the stage that asked runs again with the answer in front of it. That is what happened to the health endpoint at its first stage. The factory asks questions of its own, too: when a cap is passed, and when the human closes a pull request at the gate without saying why.

A **failure** belongs to the factory, not to the story. A handler meets a situation it was not written for, or the hosting service does not answer. The tick counts the failure against the event and the repository state it saw, and tries again on the next tick. After a few failures it posts on the pull request that the factory has given up on this event, and it stops retrying until something in the repository changes.

Rounds measure quality, attempts measure reliability, questions measure ambiguity, and failures measure the factory. All four lead to the human: a question at once, the others when they pass their cap.

## The human's channel

Each work item in production has a **pull request**: the reviewable proposal to merge its branch into the main branch, with a description and comments. GitLab calls it a merge request; the concept is the same. The factory opens it as a draft when the work item starts. It is the one place the human needs to look, and the one place the human acts on work in progress. Each of the human's actions there means something precise:

| The human… | while the stages work | while a question waits | at the gate |
| :- | :- | :- | :- |
| *merges* | accepts the story as it is | accepts the story as it is | accepts the story; the factory archives it |
| *closes* | discards the story: back to drafts as written, branch deleted | discards the story | with a reason, sends it back to the coding stage (one round); without one, is asked whether to rework, discard or accept |
| *comments* | not read while the stages work | answers the question; the stage that asked runs again | goes into the log, and becomes the reason if the human then closes |

The health endpoint's "(a)" was a comment of the middle column: an answer to a posted question. The next tick copied it into the log and cleared the question; the tick after that started intake again.

When a story reaches the gate, the factory writes the pull request's description from the story itself: the assignment, the criteria, what the tester, reviewer, documenter and demonstration recorded, the commits, and what each of the human's actions will do now. It marks the pull request ready and posts the story's running cost. Everything the factory posts carries a hidden **marker**, so the factory can tell its own comments from the human's even when both are written under the same account.

## The feature's acceptance

When the last Operations story had been archived, the feature was complete, and one more work item became due: the **feature acceptance**. It has a stage of its own with its own role, the **acceptor**, followed by the human's gate. It also has its own branch and pull request.

The acceptor judges the whole feature, which no single stage saw:
- whether the stories together keep the feature's promise;
- a demonstration of the feature end to end;
- how many deliberately broken versions of the code the tests notice;
- what the stories noticed but did not touch;
- the documentation read as a whole.

It writes a report with a verdict, and it proposes draft stories for what it found. For Operations the verdict was "accepted with drafts". The demonstration showed the feature's goal end to end. Two drafts followed: one because no test would notice the version number going stale, and one for small gaps in the documentation as a whole.

The human's actions on an acceptance's pull request mean something slightly different:
- **merge** accepts the report, and its proposed drafts land among the feature's drafts, where they are the human's to refine and promote, or not;
- **close** refuses the feature: the report is recorded on the main branch as refused, with the human's reason, and the proposed drafts are dropped.

Either way, the outcome is the feature's status. A new acceptance becomes due when another story of the feature is archived. [Chapter 11](../11-feature-acceptance/README.md) has the details.

## The contract with a project

A project that wants to be built by the factory provides a small, fixed set of things, the **project contract**:

| Part | What it is |
| :- | :- |
| *Stage table* | The stages, roles, transitions, checks, reports, caps and lanes for this project |
| *Story and feature forms* | The sections every story and every feature must have |
| *Project guide* | Architecture, test conventions, documentation layout, the list of things nobody does without asking |
| *Control surface* | A few commands the factory and the agents call to check the project: a full check, a lint, a test run, and optional extras such as a mutation run |
| *Reader documentation* | A README and documentation for the project's own readers, which the documentation stage keeps current |
| *A hosting service* | Somewhere the pull requests live and the human acts on them |

The **control surface** is what makes the factory independent of languages and toolchains. The factory never runs a compiler, a test framework or a linter directly. It runs `check`, `lint` and `test`, and the project decides what those mean. (v1 falls short here: it assumes `uv` in every project; see P15 in [chapter 3](../03-principles/README.md).) In v1 they are `make` targets, because `make` is old, small, and indifferent to the language behind it. A project in another ecosystem keeps the same three names and puts its own tools behind them. The health endpoint met all three: its tester ran the tests while it worked, the factory then ran the lint as the stage's check and the tests as its report, and after the coder the factory ran the full check.

## The machine

The factory runs on a **machine**: in v1, a container that holds the tools, the agent runtime and the credentials, and keeps its own checkout of each project. A **preflight** checks the machine before it works:
- the tools are present;
- the identity is set;
- the hosting service is reachable;
- the agents the stage table names are installed;
- the control surface runs.

A missing tool is reported, never worked around. An agent that cannot run the full check does not get to run its parts by hand and call the result green.

The machine also keeps the factory's **cost records**: one line per agent run with its duration, tokens and cost. They give each story its bill and each stage its average, and they show whether a change to the factory made it better. The health endpoint's bill (seven agent runs, 2.8 minutes, $1.36) was summed from them.

## How the concepts fit together

![Figure 2-2. The concepts and how they relate](concept_map.svg)

*Figure 2-2. The concepts and how they relate.*

Read Figure 2-2 by its colors:
- **Slate: data.** The work (project, feature, story, log) and the line (stage table, stage, role, lane, check) are files in the project, readable and editable with ordinary tools.
- **Blue: the model.** The agent run is the only place a model appears. It reads that data and hands back an outcome.
- **Green: code.** The control loop is the only thing that writes the story's state, commits, and talks to the pull request.
- **Amber: the human.** The human acts on exactly two things: the story, which they write and start, and the pull request, where they answer and accept.

## Where each concept lives in v1

| Concept | In v1 | Chapter |
| :- | :- | :- |
| Feature | A folder `factory/features/F0002-operations/` with a `FEATURE.md` | [4](../04-work-items/README.md) |
| Story | A Markdown file `F0002-S0001-health-endpoint.md` with YAML frontmatter, fixed sections and `## Log (append only)` | [4](../04-work-items/README.md) |
| Work item | A *ticket*: a story, or a feature's `ACCEPTANCE.md` | [4](../04-work-items/README.md), [11](../11-feature-acceptance/README.md) |
| Lifecycle | The feature's subfolders `drafts/`, `ongoing/`, `done/` | [4](../04-work-items/README.md) |
| Story state | Six frontmatter fields: `stage`, `pr`, `blocked` (`question` or `asked`), `comments_seen`, `round`, `attempts` | [4](../04-work-items/README.md), [5](../05-stage-machine/README.md) |
| Branch per work item | `ticket/<file stem>`, and `acceptance/<feature folder>` for an acceptance | [13](../13-git-and-github/README.md) |
| Format check | `factory-check-story`, in `factory.story` | [4](../04-work-items/README.md) |
| Stage table | `factory/stages.yml`, `version: 5` of the watcher's contract (`docs/WATCH_CONTRACT.md`); *reports* are called `records` there | [5](../05-stage-machine/README.md) |
| Scheduler and tick | The container's entrypoint loop calling `factory-tick` | [14](../14-runtime/README.md) |
| Watcher and events | `factory-watch`; v1 calls an event a *line*: `reject`, `duplicate`, `error pr-lookup`, `merged`, `closed`, `pr`, `ask`, `busy`, `expired`, `run`, `idle` | [6](../06-watcher/README.md) |
| Dispatcher and stage protocol | `factory.dispatch`, `factory.stage`, `factory.ops` | [7](../07-dispatcher/README.md), [8](../08-stage-run/README.md) |
| Run record and lease | `.git/factory-run.json`; `lease_minutes` in `stages.yml` | [6](../06-watcher/README.md), [14](../14-runtime/README.md) |
| Roles and instructions | Seven agent files and their skills (`factory-rules`, `role-*`, `stage-*`) for Claude Code; the project guide is `CLAUDE.md` | [9](../09-agents-and-skills/README.md) |
| Stage agent | `claude -p`, started headless by `factory.agent` | [8](../08-stage-run/README.md), [9](../09-agents-and-skills/README.md) |
| Task and outcome | A task message composed by `factory.stage`; the outcome as JSON `{outcome, entry}` through `--json-schema` | [8](../08-stage-run/README.md) |
| Lanes | `lanes:` in `stages.yml`; the `factory-guard` hook; the undo after the stage | [8](../08-stage-run/README.md), [15](../15-safety/README.md) |
| Control surface | `make check`, `make lint`, `make test`, and `make mutants` | [12](../12-project-contract/README.md) |
| Pull request | A GitHub pull request, through the `gh` CLI; the marker `<!-- factory -->` | [10](../10-human-at-the-gate/README.md), [13](../13-git-and-github/README.md) |
| Feature acceptance | Stage `feature`, the acceptor agent, `ACCEPTANCE.md` with `stories` and `outcome` | [11](../11-feature-acceptance/README.md) |
| Machine and preflight | A Docker container; `factory-preflight` | [14](../14-runtime/README.md) |
| Cost records | `.git/factory-dispatches.jsonl`; `factory-costs` | [16](../16-cost-and-observability/README.md) |

> [!IMPORTANT]
> **Planner:** what this chapter fixes for any implementation.
> - **A story is specification, state and memory in one versioned document.** Its log is append-only and numbered, and only the factory writes its state.
> - **Two coordinates: lifecycle and stage.**
>   - Lifecycle: draft → in production → archived, or discarded back to draft.
>   - Only the human promotes; only the factory archives and discards, and it does so only on the human's merge or close.
>   - Stage applies only in production.
> - **Six state facts per story in production:** stage, pull request, question (none, recorded, posted), comments read, rounds, attempts (see the state table).
> - **A branch per work item.** It is brought up to date before every stage; a merge is acceptance.
> - **The stage table is configuration:** per stage the role, gate (explicit), next (first is forward), checks, reports and max rounds; per project the lease and max attempts; per role the lanes.
> - **Transitions** come only from an agent's decision applied by the factory, or from the human's action.
> - **The watcher** is readers plus a pure evaluation, with fixed precedence: corrections, then the human's signals, then new work. One event per tick. Handling is safe to repeat on the repository; after a kill, a post on the pull request can repeat (P14 in chapter 3).
> - **Work-in-progress.**
>   - There is a limit on agent runs in flight. v1's is one per machine: the tick runs its agent synchronously and the machine ticks its projects in turn. v1's own watcher contract says the run record enforces it; in the container the run record matters mainly for agent runs that died.
>   - Anything waiting for the human outranks new work in its project.
>   - Identifiers are the only priority, so a lower identifier can start between two stages of another story.
> - **Agents end with a structured outcome (decision + entry).** Only the factory applies it, through the stage protocol in the order listed.
> - **Four ways not to move forward** (rework, stall, question, failure), each with its own counter, scope, cap and reset (see the table).
> - **Each human action on a pull request has one meaning** per situation (see the table).
> - **Watch for:** v1's code knows several stage and role names by heart, so its stage table is less configurable than this chapter describes. [Chapter 5](../05-stage-machine/README.md) lists every place.
