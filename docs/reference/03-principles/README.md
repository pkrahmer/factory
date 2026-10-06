# 3. Principles

Concepts say what the parts are. Principles say why they are shaped the way they are, and they are what a second implementation must keep when it changes everything else. This chapter states seventeen of them. About half were learned the hard way, by watching a simpler design fail in a real run; the rest were convictions from the first day that the runs tested and did not overturn. Each comes with its reasoning, what it rules out, and the evidence from v1. [`docs/decisions.md`](../../decisions.md) records each lesson on the day it was learned.

The families follow chapter 1's division of labor. Two foundations come first; then come the principles that govern the human, the models and the code; then those that govern the factory as a whole. They are numbered P1 to P17 so that later chapters and later plans can cite them.

| Family | Principles |
| :- | :- |
| *Foundations* | P1 Sort every step: human, model or code · P2 Versioned files are the only truth |
| *The human* | P3 Nothing starts and nothing lands without the human · P4 The human acts where they already are · P5 Bounded work in flight, in the human's order |
| *The models* | P6 The work item is the memory · P7 Whoever makes something does not judge it · P8 Specify first, down to the failing side · P9 Ask, don't guess |
| *The code* | P10 Code enforces, instructions explain · P11 Believe what you observe, not what an agent reports · P12 Loud over lucky · P13 Spend on events, not on time · P14 Recover by construction |
| *The factory itself* | P15 The project owns how it is built · P16 Measure every agent run · P17 Change by evidence, and write down why |

![Figure 3-1. Where the principles act](principles_map.svg)

*Figure 3-1. Where the principles act: the parts of Figure 1-1, each with the principles that govern it.*

## Foundations

### P1. Sort every step: human, model or code

**Ask of every step: does the choice decide what is wanted or accepted? Then it is the human's. Given the state, is there exactly one right result, reachable by code without open-ended recovery in the outside world? Then it is code's. Everything else is a model's.**

Chapter 1 told the story behind this principle. Every defect the runs found sat in the machinery around the work, and the part of the machinery that a model carried out was also the most expensive part. The decisive detail is how the defects behaved after they were fixed: the bugs in code stayed fixed, while the model's protocol errors came back after their instructions were corrected. The fix was not better prose. It was moving every step with one right answer into code, where a test checks it before it runs.

The principle cuts both ways. Code should not judge either. Carrying the human's free-text answer into a story's criteria looks like copying, but it maps prose onto a structure, and that is judgment. Deciding whether an answer calls for a test change is judgment too. Running a demonstration stays with a model under the rule's own recovery clause, for the reasons chapter 1 gives. All three stay with models in v1.

*Rules out:* a model doing bookkeeping (counting, numbering, routing, posting, committing, deciding whether a check passed); code interpreting free text.

*In v1:* the dispatcher and the stage protocol are code. Agents end with a structured outcome and cannot push, switch branches or talk to the hosting service. Their task names every fact the factory knows (the round, whether this is an approved test change, the result of the format validation, the next free story number, the cost so far), so no agent works anything out from version control or the hosting service. The record is [`docs/deterministic-core.md`](../../deterministic-core.md), with its table of where each fault sat, and the design decisions of 2026-10-05 ("the dispatcher is code"; "the stage protocol is code"; "the story's form is checked by code").

### P2. Versioned files are the only truth

**Everything that matters about the work lives in version control: what to build, where each piece stands, what was decided and what was learned. The hosting service is an inbox: what the human says there is copied into the work item before the factory acts on it. Everything else is machine state, which is either disposable or rebuilt from the truth.**

v1's second generation kept the factory's control in a long-running agent session that watched the repository and remembered what it had done. When the session died, what it knew died with it. The lesson generalizes. Any state outside version control is state the human cannot see, cannot fix with ordinary tools, and loses when the process holding it goes away.

So the stage is a field in the story, not a fact in anyone's head. A transition is a commit, which records its own time and author. An answer from the human becomes a log entry before any stage acts on it, because a comment the factory has not copied is a comment the next stage will not see. What is left as machine state is demoted to its proper place:
- a lock while a tick runs;
- the run record;
- the memory of the last event handled;
- the cost records.

Each lives beside the repository and is never committed. The lock and the tick's memory are disposable, and the run record is read once more after a restart, to expire the agent run it names. The cost records are neither disposable nor rebuilt; see the limit below.

*Rules out:* a database, a dashboard or a long-lived session as the place where a story's status lives; any action taken on a comment before it is in the log.

*In v1:* machine state lives in `.git/` (the lock, `factory-run.json`, the tick's memory, the cost records). After a restart the locks and the tick's memory are removed, and a run record left behind expires its agent run at once. See the design decisions of 2026-10-04 ("Version 3: no dispatcher session"; "questions … only through the pull request") and 2026-10-05 ("the claim left Git").

> [!WARNING]
> **v1 limit:** two things in v1 fall short of this principle.
> - The cost records are machine state too. Losing them, for example with the container's work volume, loses the bill of every story not yet archived.
> - A comment the human writes while the stages work can be skipped entirely: every post of the factory's own advances the count of comments read ([chapter 10](../10-human-at-the-gate/README.md)).

## The human

### P3. Nothing starts and nothing lands without the human

**The human promotes every story into production and accepts every result. Agents may propose work, never start it, and their output reaches the main branch only through the human's merge.**

Autonomy is not the goal; leverage is. The human's two decisions, *build this now* and *this is what I wanted*, are where intent and accountability live. They take the human minutes, because the pull request puts everything those decisions need on one page: the criteria, the tester's mapping, the reviewer's verdict, the demonstration's output. Everything between the two decisions is delegated. When the feature acceptance finds gaps, it writes *drafts* for the human to refine and promote, or not. The factory carries out what follows from the human's acts (the archive after a merge, the discard or the recorded refusal after a close) and decides none of it.

*Rules out:* an agent starting a story, creating a feature, or extending a story beyond its assignment; a result reaching the main branch without the human's merge.

*In v1:* promotion is a commit on the main branch that moves a file into `ongoing/`; acceptance is a merge. No story stage's lane reaches `drafts/`. Scope is held by the instructions, the reviewer and the human's merge, not by code. See the design decision of 2026-10-05 on feature acceptance ("nothing is *started* without the human").

> [!WARNING]
> **v1 limit:** nothing in v1's code stops an agent from going beyond its story's assignment. The reviewer and the human's merge are the only safeguards.

### P4. The human acts where they already are

**The human works in two places they already use: the repository, where they write and promote stories, and the pull request, where they answer, accept and send back. There is no third.**

The factory runs while the human is elsewhere. A channel that needs a terminal, a dashboard or a chat session at the right moment is a channel the human misses. The pull request is already on the human's phone, already notifies them, and already carries the code, so it carries everything else too:
- the story, as its description;
- each question, as a comment;
- the result at the gate;
- the bill.

A second conversational channel would split the record. An answer given in a chat never reaches the log, and the agent waiting for it blocks.

*Rules out:* questions in a chat or an email; a dashboard the human must watch; any action the human can only take at a keyboard while the factory works.

*In v1:* everything on the pull request is posted by code, with a hidden marker so the factory never mistakes its own words for the human's under the same account. The pull request's closing paragraph says what each action does at this stage. See the design decisions of 2026-10-04 ("a branch per ticket … the human accepts from their phone"; "questions … only through the pull request") and 2026-10-05 ("the closing line says what the human's actions do"; "every comment the factory posts carries a hidden marker").

### P5. Bounded work in flight, in the human's order

**Work is taken in identifier order, and the agent runs in flight are bounded.**

A fixed order gives the human complete control over priority without a priority field. A small bound on the agent runs in flight is the strongest simplification of all. With one agent run at a time, every stage builds on the main branch as it stands when the stage starts, one checkout serves every stage, and nothing runs in parallel that could interfere. The bound is on agent runs, not on stories. A story promoted with a lower identifier can start between two stages of another, so two stories can be in production at once, and the later one's merge of the main branch can then fail, which is a stall.

The price is throughput, and v1 pays it on purpose. A story takes a few minutes of machine time and then waits for the human's merge, which nearly always takes longer. More stories in parallel would put more work in front of the same human; they would not make the human faster. A higher bound is a legitimate choice for a later implementation, but it reopens what the bound closes: parallel checkouts, conflicts between stories, an order of merges, a shared check.

*Rules out:* a priority field the factory interprets; an unbounded number of agent runs in flight.

*In v1:* one agent run at a time per machine, because the tick waits for its agent and the machine ticks its projects one after another. A story waiting for the human outranks all new work in the watcher's precedence, so the factory usually finishes a story and then waits for the merge. Numbering is the only priority. See the design decisions of 2026-10-04 ("one checkout and WIP 1 are enough") and 2026-10-05 ("Trunk-based stays").

## The models

### P6. The work item is the memory

**Agents remember nothing. A stage starts from the committed state and carries nothing over, and everything a later stage needs is written into the work item by the stage that knows it: what was done, why, what was rejected, and what is open.**

Every stage agent starts blank, and that is a feature. A fresh agent cannot be confused by a stale context, does not drift, and can be replaced by another model without migration. But the story must then carry everything forward:
- The tester writes which test covers which criterion, so the reviewer can check the mapping.
- The coder writes its main design decision and the alternative it rejected.
- Every stage writes what it noticed but did not touch, so that someone who later sees the whole feature can collect it.

The log is append-only and numbered; a later entry corrects an earlier one. When the human's answer changes the meaning of the story, the stage that receives it rewrites the assignment and cites the log entry the change came from. The story always says what it means *now*, and the log says how it got there.

The memory runs one way only. Stories point to code by path and commit; code and tests never name a story or a criterion. A test named `test_criterion_3` says nothing to the next reader.

*Rules out:* agent sessions resumed across stages; summaries kept outside the work item; story numbers in code.

*In v1:* in run 4, the reviewer of the HTTP API story noted, outside its findings, that an exception no handler maps would reach the client as a plain-text error instead of the promised error shape. The documenter and the demo agent carried the remark forward in their entries. Three stages passed it on, and none owned it. The feature acceptance collected it from the archived log and proposed a draft, which the human promoted: story `F0001-S0005` of [factory-demo-todo](https://github.com/pkrahmer/factory-demo-todo) mapped every unexpected error to the documented shape.

### P7. Whoever makes something does not judge it

**Every artifact is judged by a role that did not make it. The separation is held by instructions, by write permissions and by a fresh context.**

v1's first reviewer could write code, and it used that freedom. It spent most of its 23 minutes planting 37 bugs in the code to see whether the tests caught them. A judge that can act will act, and an author who checks their own work checks it against their intentions rather than against the specification. So each step has a maker and a separate judge:
- **The tester writes the tests before the code exists**, from the criteria alone, so that the tests encode what was asked rather than what was built.
- **The coder cannot change a test.** A test it believes is wrong becomes a question to the human. If the human agrees, the tester makes exactly the approved change.
- **The reviewer reads the diff against the story and writes no code.**
- **The documenter reads the result as a newcomer would**, because the author of the code does not have the reader's perspective.
- **The demonstration runs the story's commands** against expectations written before the code existed.
- **The feature acceptance looks at the whole**, which agents who each saw one story could not.

Separation costs agent runs, and agent runs cost money. Refactoring shows where the boundary lies: it stays inside the coder's stage, because it is the same perspective on the same work in the same warm context. A separate refactoring agent would re-read everything for no new point of view.

*Rules out:* a coder that writes its own tests; a reviewer that can fix what it finds; one agent session that plays several roles.

*In v1:* lanes in the stage table keep the coder out of the tests and the reviewer out of the code. See the design decisions of 2026-10-03 ("Tests are written by a separate tester stage"; "the reviewer reads and runs checks; it writes no code"; "Refactor is a step inside the coder stage"), 2026-10-04 ("A wrong test goes back to the tester"; "A docs stage") and 2026-10-05 ("Feature acceptance").

> [!WARNING]
> **v1 limit:** every story role may edit the story itself, so that a human's answer can be carried into the criteria. Nothing in code stops a coder from loosening the criterion its tests encode. Only the reviewer, reading the diff, and the human, before merging, would see it.

### P8. Specify first, down to the failing side

**A story states exactly what will be built and how it will be checked before anyone builds it: an exact interface, numbered criteria each testable by one test, including what must fail, and a demonstration with expected output. It is small enough for one pass.**

Agents are good at filling gaps, which is the problem. Two good agents fill the same gap differently, and both pass the tests they wrote. The factory therefore removes the gaps before the work starts. The first stage refuses to proceed while the story is ambiguous: an interface behavior without a criterion, a rule without its failing side, a demonstration without an expected output. The tester then turns each criterion into a test, and tests a stated limit on both sides of its boundary, because that is what the number says.

Failing sides belong in the specification because they are product choices. What happens with a blank title, an unknown identifier or a 201-character string is the human's call. A specification that states only the happy path leaves the error paths to whichever role reaches them first.

*Rules out:* stories that state only the happy path; tests of behavior no criterion names; criteria phrased as "nothing else changed" (they invite a test that breaks with the next story; say what must still hold instead).

*In v1:* two fixed criteria close every story: the full check stays green, and a docs criterion. The story's form is validated by code before the first stage and after every stage; intake judges what code cannot. In the health-endpoint story, intake caught exactly one missing failing side. See the design decisions of 2026-10-04 ("Every story ends with two fixed criteria") and 2026-10-05 ("Failure paths are criteria, not the tester's invention"; "The story's form is checked by code").

### P9. Ask, don't guess

**When the specification does not decide something that matters, the agent stops and asks the human. Asking is cheap, visible and normal.**

A question is a first-class outcome, beside "forward" and "back". It costs one short agent run and a wait. A guess costs a wrong build, a review, a rework round and the human's trust, or worse, it passes unnoticed. What the criteria leave open, the tester neither tests nor decides: it asks. The project guide adds a list of things nobody does without asking, whatever the story says:
- a new dependency;
- a new top-level package;
- a change to the factory's files or to a test someone else wrote;
- a marker that silences a security check.

The opposite of guessing is not refusing to work. An agent that asks about everything is as useless as one that asks about nothing. A good rule: ask when two reasonable readings lead to different behavior. A good question names the options and a recommendation, so the human can answer "(a)" from a phone.

*Rules out:* an agent deciding a product question; a stage that "makes a reasonable assumption" and moves on.

*In v1:* any role can end with `question`, and the factory posts the question. The tester's bar is strict: any criterion it had to interpret is a question. The cost stayed small. Run 2 asked nothing, and the health endpoint's question cost one more intake run, seven cents, and a wait. (The human in those runs was simulated, as chapter 1 says; the runs show that a question with options can be answered in one line, not how fast a person answers.) See the design decisions of 2026-10-04 ("Questions from the tickets go to the human only through the pull request"; "A wrong test goes back to the tester").

## The code

### P10. Code enforces, instructions explain

**Every rule that can be checked is checked by code, before or after the agent. Instructions tell an agent why and what; they are never the only thing that stands between a rule and its violation.**

An instruction is a request. A model follows it most of the time, and "most of the time" is not a property a production system can be built on. So every rule has two layers: the instruction, which makes compliance likely and explains the purpose, and code, which makes a violation impossible or reversible.

| Rule | Enforcement in v1 |
| :- | :- |
| A stage changes only by a decision the table allows | The factory applies the decision and checks it against the table; a disallowed change committed by hand is detected and moved back |
| A role writes only its lane | A hook refuses the write while the agent works; after the stage the factory undoes any change outside the lane, shell writes included |
| The story's state fields and log are the factory's | Whatever the agent did to them is restored before the factory writes its own entry |
| The story keeps its form | A format validation before the first stage and after every stage; a stage that broke the form stalls |
| Agents do not push, switch branches or call the hosting service | Those commands are denied to the agent, and the factory confirms the agent is still on its branch |

This is also how the factory stays changeable. A new rule in prose cannot be tested before an expensive live run, and it adds a new way to fail. A new rule in code is a unit test.

*Rules out:* a rule whose only defense is a sentence in an agent's instructions, when code could check it.

*In v1:* see the design decisions of 2026-10-04 ("Write lanes are enforced by a PreToolUse hook") and 2026-10-05 ("The stage protocol is code"). Two plans of 2026-10-05, *fewer commits* and *review comments*, were built and reverted the same day although both worked, because each added a conditional rule only a model could follow and nobody could test before a live run. The plans are in [`docs/fewer-commits.md`](../../fewer-commits.md) and [`docs/review-comments.md`](../../review-comments.md); the first now carries a later note that withdraws it for another reason (the claim left Git). The build and the revert are not in the repository's history, because the main branch was reset, and not in the decision log either.

> [!WARNING]
> **v1 limit:** some rules have no enforcement in code:
> - no story or criterion numbers in code (only review checks it);
> - scope (P3);
> - the coder's commit subjects;
> - the contents a stage's log entry must have.

### P11. Believe what you observe, not what an agent reports

**"Green" means the project's check command succeeded when the factory ran it, "done" means the factory found an outcome it could keep, and "on the right branch" means the factory looked. An agent's claim is never evidence.**

In v1's second generation, `make` was missing on the machine. The coder and the reviewer, both capable and both trying to help, ran the commands from the Makefile one by one, found them green, and reported the check green. A check is not its contents. It is one command whose exit status the factory reads. Running its parts by hand skips whatever the command adds: ordering, flags, a check someone added last week.

So the factory observes for itself. It runs the stage's checks after the stage and before it keeps a forward move. It reads the agent's structured outcome rather than the agent's prose. It checks the branch the agent left. The agents still run the checks while they work, because that is how they find their mistakes. But their report that a check passed carries no weight.

*Rules out:* a forward move on an agent's word; a check run by hand in place of the command; an agent run that "reports success" but leaves nothing the factory can keep.

*In v1:* the full check runs after the code and after the documentation; the lint runs after the tests, whose new tests are red on purpose. A red check holds the story and counts a stall, with the last lines of its output in the log. A missing tool is a stall, and so is an agent's `stuck`; installing tools is not a stage's business, and the preflight checks the machine before work starts. See the design decisions of 2026-10-03 ("`make check` is a hard gate", where v1 says *gate* for the full check), 2026-10-04 (the preflight) and 2026-10-05 ("A stage run that ends without a stage change or a question is a stall, whatever the agent says").

### P12. Loud over lucky

**A state no handler was written for stops the line and is reported to the human. Retries are bounded, loops are capped, and every stall is visible where the human looks.**

A system that improvises past the unexpected hides its defects until someone reads the transcripts. When v1's dispatcher was a model, an answered question went through a path the protocol did not cover, because two agents improvised their way past it. It worked, and the gap stayed hidden for a whole run. In code, the same gap raises an error. The tick counts it as a failure, retries it a few times, and then posts on the pull request that the factory has given up and a human must look. Lucky does not stay lucky.

The work's own loops end the same way. Rework rounds and failed attempts are both capped per story, and both caps end in a question to the human, not in another lap. Every stall is a comment on the pull request when it happens, not only when the cap is reached.

P9 is this principle for agents: when the specification is silent, ask. P12 is the same principle for code: when the handlers are silent, stop and report.

*Rules out:* a catch-all that carries on; unbounded retries; a failure only the log file knows about.

*In v1:* a handler's unexpected error is a counted failure, tried three times on the same event and repository state and then reported (commit `57fe24f`). See the design decisions of 2026-10-04 ("Every stall is a pull request comment") and 2026-10-05 ("The dispatcher is code": "a situation no handler knows raises").

> [!WARNING]
> **v1 limit:** two events stop the line but reach only the factory's log file, not the pull request:
> - two stories with the same identifier;
> - a pull request the factory cannot read.

### P13. Spend on events, not on time

**The factory spends nothing while nothing changes. A tick is cheap, a model runs only when a stage is due, and the pace adapts to when the next event is likely.**

A watching agent burns tokens to watch. An idle tick in v1 costs one fetch, plus one lookup on the hosting service for each story that waits for the human. No model starts. When a tick has handled something, the next tick follows at once, because the next stage is usually due. After that the pause starts short and doubles to a ceiling, because the human tends to act right after the factory has, and then not for a while.

Spending only on events has a price, and v1 paid it once. The watcher reads a pull request only while the human is expected to act, so a pull request closed while the stages worked went unnoticed until the gate. Every stage in between ran for nothing. The fix kept the principle: the factory now checks the pull request once before it starts an agent, which is an event it meets anyway.

*Rules out:* a model on a timer; an agent session that watches; polling every pull request on every tick.

*In v1:* the tick sleeps 2 seconds after a handled event, then 15 seconds, doubling to 120. See the design decisions of 2026-10-04 ("Version 3": "Tokens are spent on events, not on time") and 2026-10-05 ("the dispatcher asks GitHub for the story's pull request state" before an agent; "The pause between ticks starts short and doubles").

### P14. Recover by construction

**Any agent run, and any tick, can die at any moment. The factory resumes from versioned state without a human, and calls a human only when the same thing fails again.**

Machines restart, processes are killed and networks drop. A factory that needs a human to clean up after each of those is not unattended. v1's recovery is not one big mechanism but a set of small, specific ones:
- **Locks are reclaimable.** A lock older than its lease belongs to a dead tick and is removed. After a restart every lock is removed at once, because nothing can be running yet.
- **Agent runs are leased and recorded outside the work.** A run record left behind by a killed agent run marks that agent run dead. After a restart it is dead at once, whatever its age.
- **Partial work is kept.** An interrupted agent run's changes on a story's branch are committed as they are, so the next attempt sees them.
- **Every handler tolerates being run twice, and the factory avoids running it twice anyway.** It remembers the last event it handled and the repository state it saw, and handles the same event in the same state once.

*Rules out:* a cleanup step only a human can do; a lease so long that a restart idles the line; state that a killed process leaves inconsistent.

*In v1:* in the restart tests, the container was killed while a stage held a story. On its first tick after the restart the factory expired the agent run and ran the stage again. See the design decisions of 2026-10-05 ("A restart recovers by itself"; "The dispatcher does not second-guess a line", where a *line* is v1's word for an event).

> [!WARNING]
> **v1 limit:** three gaps remain in v1's recovery:
> - **A restart is charged to the story.** It counts as a failed attempt, so two interruptions, or one interruption and a red check, ask the human.
> - **Leftovers bypass the lane undo.** An interrupted agent run's leftovers are committed without it, so an out-of-lane write by a killed agent survives.
> - **A kill can double-post.** Handlers that post on the pull request post before they commit, so a kill between the two posts again.

## The factory itself

### P15. The project owns how it is built

**The factory never knows a project's language, framework or tools. It reaches a project only through a small control surface, a set of lanes and a project guide, all owned by the project.**

v1's first three generations lived inside its first project and knew far too much about it. The cut came on the second day. The instructions now call only `check`, `lint` and `test`. Lanes are path patterns in the project's own stage table. The test framework, the layout and the architecture rules live in the project guide, which every agent reads. From then on, the same engine and the same agents could serve any project that provides the contract.

The boundary also runs the other way. The project's documentation is written for the project's readers, not for the factory: the template README describes the application and mentions the factory in one closing paragraph.

*Rules out:* an engine that names a language, a tool, a file or a path of the project; instructions that run a project's tools directly.

*In v1:* a new kind of project brings its own stage table, its own control surface behind the same names, and its own guide; the engine does not change. See the design decisions of 2026-10-04 ("The pipeline no longer knows how this project is built"; "The pipeline moved out"; "Lanes are glob patterns").

> [!WARNING]
> **v1 limit:** v1 keeps this principle in its structure but not completely in its code:
> - **`uv` is assumed.** The preflight requires `uv` and a `.venv` in every project, and the entrypoint runs `uv sync`.
> - **File names are hard-coded.** The lane guard never lets an agent write `pyproject.toml`, `uv.lock`, `Makefile` or `CLAUDE.md`, which are the file names of Python, uv, make and Claude Code.
> - **Stage and role names are hard-coded** in several places.
>
> [Chapter 12](../12-project-contract/README.md) and [chapter 19](../19-limits-and-backlog/README.md) list them.

### P16. Measure every agent run

**Every agent run is recorded with its duration, turns, tokens and cost. Every story carries its bill, and changes to the factory are judged by the numbers.**

The largest saving in v1's history came from one row of a cost table: the coordinating model, $0.78 of a clean story's $1.87. When it became code, a clean story fell to $1.16. Without the records, nobody would have known where to look, or whether the change paid off. The records show:
- what a story costs, and whether it was worth it;
- which stage to tune;
- whether a change to the factory helped.

*Rules out:* cost known only from the monthly bill; a change to the factory justified by intuition.

*In v1:* the records are free, because the agent runtime reports them with every agent run. They come as one line per agent run, summed per story and per stage. The bill is posted on the pull request when the story reaches the gate, and written into the log when the story is archived. The feature acceptance reads the sum.

Two later changes were made on measured grounds; [chapter 16](../16-cost-and-observability/README.md) has them. See the design decisions of 2026-10-04 ("What a ticket costs is recorded by the tick").

> [!WARNING]
> **v1 limit:** the cost record is written when an agent run returns. An agent run killed by a restart leaves no record, so its cost is missing from the bill.

### P17. Change by evidence, and write down why

**The factory changes in response to what its runs show, one design decision at a time, each recorded with its reason and what was rejected. A change that adds failure modes for a small gain is not made, or is taken back.**

The factory's runs are its real test suite. Each generation of v1 was provoked by specific failures in specific runs. Each design decision in its log says what happened, what was decided, why, and what was rejected. Plans are written before they are built and approved by the human. Two plans that, once built, added rules only a model could follow, for a small gain, were removed again, although both worked (P10). The bar is not "does it work" but "is the factory more solid with it than without it".

Two habits keep this honest. Every end-to-end run is also a hardening run: every defect counts as a factory defect until proven otherwise, and is fixed at its cause. And every reason that lasts goes into the decision log, so that a later reader, or a later planner, knows which alternatives were already tried.

*Rules out:* a change made because it is clever; a design decision recorded without the alternatives it beat.

*In v1:* [`docs/decisions.md`](../../decisions.md) is append-only, with rejected alternatives. [`demo/README.md`](../../../demo/README.md), *Hardening mode*, is the procedure for runs.

> [!WARNING]
> **v1 limit:** the reverted plans under P10 are not in the decision log.

## Where the principles pull against each other

Principles that never conflict are not saying much. These do, and the factory's shape is where each tension was settled.

| Principle | Pulls against | Where v1 settled it |
| :- | :- | :- |
| P7 Whoever makes something does not judge it | Cost: every separate perspective is a separate agent run | Separate where the perspective differs (tester, reviewer, documenter, demonstration); together where it does not (refactoring stays with the coder) |
| P9 Ask, don't guess | Throughput: every question blocks the story | Questions are posted at once and answered in a line; the pace adapts to the answer (P13); a stated limit is tested on both sides without asking, because the number already says it |
| P1 and P10, code over prose | Flexibility: code cannot improvise past a gap | Loud over lucky (P12): a gap becomes a reported failure and a fix in tested code |
| P5 One story at a time | Throughput | Accepted for v1: the human is the slower part of the loop |
| P10 Code enforces | Simplicity: enforcement is more code | Accepted: code is tested before it runs, prose only by live runs |
| P3 Nothing without the human | Momentum: the line stops when the human is away | The human's acts take minutes on a phone; finished work waits safely |
| P14 Recover without the human | P12 Stop and report | Known kinds of failure recover (dead agent runs, locks, leftovers); unknown states stop and report |
| P14 Keep partial work | P10 Lanes enforced after every stage | Unresolved in v1: an interrupted agent run's leftovers are committed without the lane undo |
| P2 Truth in version control | P16 Measure every agent run | Unresolved in v1: the bill lives in machine state until the story is archived |
| P6 The work item is the memory | Cost: every agent turn re-reads the whole story | P6 won: giving agents slices of the story was rejected, because code would decide what of a story matters |

Where v1 settled a tension, control, truth and enforcement won over throughput and cost, except where a separation would have added no new perspective: refactoring stays with the coder. Within that winning group v1 sets no order. The unresolved rows above are conflicts between its own principles, and there a plan must choose and record why (P17).

## Testing a design against the principles

A principle is useful to a planner only if a design can fail it. Each question below is phrased so that *yes* means the design keeps the principle. The last column says where v1 stands.

| | Question (*yes* keeps the principle) | v1 |
| :- | :- | :- |
| P1 | Is every step with exactly one right result done by code, and is every interpretation of free text left to a model? | Holds; the demonstration stays with a model under the rule's own recovery clause |
| P2 | After deleting all machine state and restarting on a fresh checkout, does every story continue? Is every human statement copied into a work item before the factory acts on it? | Partial: the cost records are lost; a comment written while the stages work can be skipped |
| P3 | Does every story enter production, and every result reach the main branch, only through a human act? | Holds for work; the factory's own bookkeeping commits go to the main branch |
| P4 | Can the human do everything from the work-item store and the pull request alone? | Partial: two events reach only the factory's log file; setting up the machine aside |
| P5 | Are the agent runs in flight bounded, and is work taken strictly in identifier order? | Holds: one agent run per machine; a lower identifier can start between two stages of another story |
| P6 | Can a fresh agent rerun any stage from the repository alone? | Holds |
| P7 | Is every artifact judged by a role that could not write it? | Partial: every story role may edit the story's criteria |
| P8 | Is a story without testable criteria, failing sides or expected output stopped before any code is written? | Holds: format validation in code, plus intake's judgment |
| P9 | Can every role end with a question that reaches the human? | Holds |
| P10 | Does every instruction have code that prevents, detects or reverses its violation, or a stated reason why not? | Partial: see the limits under P10 |
| P11 | Does the factory act only on what it observed itself, never on an agent's claim? | Holds |
| P12 | Does every unforeseen state stop and reach the human, and does every retry and every loop end there? | Partial: two events reach only the factory's log file |
| P13 | While nothing changes, does the factory spend nothing on models? | Holds |
| P14 | Killed at any instruction, does the factory resume without a human, without duplicated effects, and with its rules intact? | Partial: a restart costs an attempt; a kill can double-post; leftovers skip the lane undo |
| P15 | Is the engine free of every language, tool, file name and path of the project? | Partial: `uv`, `.venv`, Python and Claude Code file names, stage names |
| P16 | Is every agent run recorded with time, tokens and cost, and attributable to a work item and a stage? | Partial: an agent run killed by a restart leaves no cost record |
| P17 | Is every lasting design decision recorded with its reason and the alternatives it beat? | Partial: the reverted plans of 2026-10-05 |

v1 gives its agents the principles as fifteen rules, R1 to R15, in the `factory-rules` skill. [Chapter 9](../09-agents-and-skills/README.md) maps each rule to its principles and to the code that enforces it.

> [!IMPORTANT]
> **Planner:** what this chapter fixes for any implementation.
> - **Essential:** all seventeen principles. A design that departs from one says so explicitly, with the reason and the evidence, in the style of P17. The test table above is the acceptance test for a plan: every answer should be *yes*.
> - **The strongest constraints:**
>   - P1: no step with one right result is left to a model;
>   - P10: every checkable rule is enforced in code;
>   - P2: nothing that matters lives outside version control;
>   - P3: the human starts and accepts.
> - **Precedence:** control, truth and enforcement win over throughput and cost. Conflicts inside that group are open; choose and record:
>   - P14 against P12;
>   - P14 against P10;
>   - P2 against P16.
> - **Explicitly open for change:**
>   - the work-in-progress bound of P5;
>   - the stage table's contents (P15);
>   - the hosting service behind P4;
>   - the agent runtime behind P1.
> - **A replacement agent runtime must offer:**
>   - a headless start with a task message;
>   - allow and deny lists for tools;
>   - a hook that can refuse a write, or else reliance on the undo after the stage;
>   - a budget per agent run;
>   - output constrained to a schema;
>   - cost, token and turn reporting per agent run;
>   - resuming a stopped agent run.
> - **A replacement hosting service must offer:**
>   - draft pull requests, switchable between draft and ready;
>   - reopening a closed pull request;
>   - comments that can carry a hidden marker;
>   - a state query (open, closed, merged);
>   - merges with a merge commit.
> - **Protected paths.** The general mechanism is a list of paths no lane reaches, declared by the project. v1 hard-codes the file names of Python, `uv`, `make` and Claude Code (`pyproject.toml`, `uv.lock`, `Makefile`, `CLAUDE.md`). That counts against P15, but it also enforces part of the "Not without asking" list: a new dependency needs a file no agent may write.
> - **Known v1 shortfalls**, each in a limit box above:
>   - P2: cost records, skipped comments;
>   - P3: scope;
>   - P7: editable criteria;
>   - P10: unenforced rules;
>   - P12: two events that reach only the log file;
>   - P14: three recovery gaps;
>   - P15: Python, `uv` and stage names in the engine;
>   - P16: no record of a killed agent run;
>   - P17: the unrecorded reverts.
