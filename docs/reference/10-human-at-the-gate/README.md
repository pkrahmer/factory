# 10. The human at the gate

[Chapter 2](../02-concepts/README.md) gave the meaning of each human action on a pull request; chapters [7](../07-dispatcher/README.md) and [8](../08-stage-run/README.md) specified how the factory answers each one and how it writes the description at the gate. This chapter takes the human's side: what the pull request shows over a work item's life, every kind of comment the factory posts there, and what the human cannot do.

## The concept

The pull request is the work item's face. The human never needs to open the repository, the log or the machine to follow or decide; everything they need arrives there, and everything they do there means one thing.

Three design rules follow, beyond those of chapters 2 and 8:

- *The state of the pull request says whose turn it is.* A draft means the factory is working or waiting for an answer; ready for review means the human decides.
- *Every stop produces exactly one post,* written so that it can be answered from a phone: what happened, and what each possible answer will do.
- *The human must be notified of every post.* A channel the human only sees when they happen to look is a dashboard, which P4 rules out.

The factory reads the human's comments only when it expects the human to act (P13). The human may comment at any time, but a comment written while the stages work has no defined meaning until the next stop.

## In v1

### The pull request's life

| Moment | State | Title and description | The factory posts |
| :- | :- | :- | :- |
| a story's first stage is due | draft, created | `F0002-S0001: Health endpoint`; the Assignment and the criteria as they stood at promotion | |
| a stage stalls | draft | unchanged | a stall note |
| an agent run ended without finishing (its run record expired) | draft | unchanged | an expired note |
| a stage asks, or the attempts cap is reached | draft | unchanged | the question |
| an illegal stage change is moved back (`reject`) | unchanged | unchanged | a correction note |
| the human answers | draft | unchanged | |
| the story reaches `accept` | ready for review | rewritten from the story ([chapter 8](../08-stage-run/README.md)) | the cost table |
| the human closes at the gate | reopened, draft | unchanged until the next hand-over | the send-back question, without a reason or past `demo`'s round cap |
| the human closes before the gate | closed | unchanged | |
| the human merges | merged | unchanged | |

The title is never updated after creation. The factory writes the draft flag and never reads it: marking a pull request ready by hand changes nothing. A merge is learned from the pull request's state, not from the history. The branch is deleted after a merge, a discard or a refusal. A pull request closed before the gate stays closed; if the human promotes the story again, the factory opens a new one, because it reuses only an *open* pull request of the branch. An acceptance's pull request follows the same life, except that a close at its gate refuses it and leaves it closed ([chapter 11](../11-feature-acceptance/README.md)).

The pull request must be merged with a merge commit, as the closing paragraph says: the watcher exempts only real merge commits from its check for illegal stage changes, so a squash merge can be misread as one ([chapter 13](../13-git-and-github/README.md)).

### What the factory posts

Every comment ends with the marker `<!-- factory -->`, invisible on GitHub. Comments posted before the marker existed began with `factory:`, and still count as the factory's own.

| Post | When | Text |
| :- | :- | :- |
| question | an agent ended with `question`, or code turned its decision into one (form findings, the round cap) | the agent's log entry, verbatim, with its prefix: `intake: Questions on F0002-S0001 …` |
| attempts-cap question | `attempts` reached `max_attempts` | quoted in [chapter 7](../07-dispatcher/README.md) (`ask`) |
| stall note | any stall (`ops.stall`) | "Stage *s* stalled (attempt *n* of *max*): *reason*. Retrying on the next tick." |
| expired note, correction note | an expired run record; `reject` | quoted in [chapter 7](../07-dispatcher/README.md) |
| send-back question | a close at `accept` without a reason, or past `demo`'s round cap | quoted in [chapter 7](../07-dispatcher/README.md) |
| cost table | after the agent run that reached the gate | "Cost of this ticket [work item] so far", then a table |
| give-up | a handler failed three times | quoted in [chapter 7](../07-dispatcher/README.md) |

A stall's *reason* is the factory's own sentence, among them: "`make check` is red after the stage:" followed by the last 15 lines of its output; "the story's form broke: …"; "merging main conflicts; merge aborted"; "*branch* cannot fast-forward to origin/*branch*"; "the agent gave no outcome"; "outcome *x* is not one of …"; "budget of $*b* spent, and the resume too"; "timed out after *n* min"; or, for `stuck`, the agent's own entry. A reason about the agent's result may end with the first denied tool call: "; denied: Bash: git push …".

The cost table has one row per agent that ran on the work item, keyed by the agent named in the `run` event, and a total:

```text
| stage | runs | min | turns | in | cached | out | USD |
|:-|-:|-:|-:|-:|-:|-:|-:|
| intake | … | … | … | … | … | … | … |
| … |
| **total** | … | … | … | … | … | … | … |
```

*in* is new input plus tokens written to the cache, *cached* the tokens read from it. Only agent runs that ended without an error are counted ([chapter 14](../14-runtime/README.md)). The tick, not a handler, posts the table, so it does not change `comments_seen` ([chapter 7](../07-dispatcher/README.md)).

### A question and its answer

The health endpoint's question, as the human saw it on pull request 35:

> intake: Questions on F0002-S0001 (format check passed; Interface, Demo, architecture and scope otherwise check out: …):
>
> 1. The Interface states a rule, "`build_app` passes "sqlite" when `TODO_DB` is set and not empty, else "memory"", but criterion 3 only tests `{}` and a real path. The failing side, `TODO_DB` set to the empty string, has no criterion, so nobody will test it. Options: (a) extend criterion 3 with `build_app({"TODO_DB": ""})` answering `"storage": "memory"`, or (b) add it as a new criterion before the two closing ones. I would choose (a).

The human's comment, `(a): extend criterion 3 with …`, became log entry 3, `human (pull request comment, 2026-10-05): (a): …`; intake ran again, carried the change into criterion 3, and named entry 3 as its source.

> [!WARNING]
> **v1 limit:** the factory's posts may notify nobody. It posts with the human's own token, and GitHub does not notify a user of their own activity, so a question, a stall or a give-up appears on the pull request without a notification to the human. The demonstration runs had a simulated human and did not test this. P4's claim that the pull request notifies the human holds only for a factory with an identity of its own.

> [!WARNING]
> **v1 limit:** the factory reads only the conversation under the pull request (`gh pr view --json comments`). Reviews (`--json reviews` of the same command) and comments on lines of the diff (the API's `pulls/<n>/comments`) are never read. The human's only tools at the gate are merge and close with free text, which has to name files and lines in prose. And the human cannot request changes on, or approve, the factory's pull requests at all: the factory opens them with the human's token, so GitHub treats the human as their author.

> [!WARNING]
> **v1 limit:** a comment written while the stages work has no defined meaning. If a handler posts before the next stop, the comment is counted as seen and never copied ([chapter 7](../07-dispatcher/README.md)); a question always posts first, so a comment written before it is always lost. If it survives until the gate, it is copied after the demo agent's entry, so it counts as the reason for a later close, even a close without a comment. The human has no way to redirect a story in flight short of closing it.

> [!WARNING]
> **v1 limit:** a human comment that starts with `factory:` counts as the factory's own and is never copied into the log.

> [!WARNING]
> **v1 limit:** the stall and expired notes say "Retrying" even at the last attempt, when the next tick asks the human instead.

> [!WARNING]
> **v1 limit:** the description is the factory's. While the stages work it shows the Assignment and criteria as they were at promotion, even after intake carried in a change; at the gate it is overwritten, and so is anything the human wrote there.

> [!NOTE]
> On 2026-10-05 a plan to make review comments count (`docs/review-comments.md`) was built and reverted the same day. "Request changes" was to be the rework path, with line comments copied into the log and answered on the diff by the coder; a plain review comment was to start the reviewer in an answer mode. It was reverted because it added conditional rules only a model could follow, which no test could check before a live run; its rework path would also have needed a factory identity of its own. The plan's document still reads as if nothing had been built; neither the build nor the revert is in the history, because the main branch was reset ([chapter 17](../17-limits-and-backlog/README.md)).

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - one channel per work item, opened before the first stage;
>   - the pull request's state mirrors whose turn it is: draft while the factory works or waits for an answer, ready at the gate, reopened as a draft on a send-back;
>   - every stop produces exactly one post that says what each possible answer does;
>   - no human comment is ever classified as the factory's, and no factory post as the human's;
>   - a merge is detected from the hosting service's state, not from the history.
> - **Incidental to v1:** GitHub and `gh`; the wording of the posts; the cost table's columns.
> - **Watch for:**
>   - give the factory an identity of its own: it makes every post notify the human, and it lets the human approve or request changes;
>   - read reviews and line comments;
>   - give a comment written while the stages work a defined meaning;
>   - keep the title and description current while the stages work, or say on them that they are not;
>   - say "retrying" only when the factory will retry.
