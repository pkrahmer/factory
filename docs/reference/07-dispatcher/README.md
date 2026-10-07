# 7. The dispatcher

The watcher names the one next thing to do; the dispatcher does it. This chapter specifies the dispatcher's handlers one by one, then the tick's memo, which decides whether an event needs handling at all, and the helpers every handler shares. The `run` handler starts the stage protocol, the subject of [chapter 8](../08-stage-run/README.md).

## The concept

A **handler** exists for each kind of event. It is specified by three things:
- its *preconditions*: what it reads and expects, and what it does when the world disagrees;
- its *effects*: the changes to the work item, the commit, the push, the posts on the pull request;
- its *result*: handled, nothing to do, or a failure.

Each handler is one step from one consistent state to the next: at most one commit and one push, so that either the step happened on the remote or it did not. Effects outside Git, a post or a change to the pull request, cannot be part of that commit; they must come after it, or be safe to repeat. A handler meets a state it was not written for by raising, never by improvising (P12), and it tolerates being run twice (P14).

The tick keeps a small **memo** per project: the last event it handled, the repository state it saw, and how often the handler failed. It stops the factory from repeating a handler that changed nothing, and it bounds the retries of one that fails.

## In v1

`src/factory/dispatch.py` maps each event kind to a handler (`dispatch.LINES`; v1 calls an event a *line*, so the names say `line` throughout). Every handler takes a `Context`: the checkout's root, the parsed stage table, a GitHub client, a function that starts an agent, today's date, and `gate`, a function that runs a `make` target for the stage's checks and reports (not the human's gate). It returns `Handled(ok, summary, run)`: whether it succeeded, one sentence for the tick's log, and the agent run's result if it started one. An event kind without a handler returns `NOTHING`, "nothing to do", without raising.

Before the dispatcher sees an event, the tick has taken its lock, run the preflight, committed any leftovers of an interrupted agent run, fetched, fast-forwarded the main branch, evaluated, and turned an outlived run record into `expired` ([chapter 6](../06-watcher/README.md), [chapter 14](../14-runtime/README.md)).

### The handlers at a glance

| Event | Handler | Commits on | Commit subject (after `ticket <id>:`) | Posts | Sets `comments_seen` |
| :- | :- | :- | :- | :- | :- |
| `merged` | `merged` | main | `accept → done (pull request merged)` | nothing | no |
| `closed`, an acceptance | `_refused` | main | `closed by the human` | nothing | no |
| `closed`, a story at `accept` | `_sent_back` | the story's branch | `accept → doing (pull request closed)`, or `… (pull request closed; asked why)` | the send-back question, without a reason | yes |
| `closed`, a story elsewhere | `_discard` | main | `discarded (pull request closed)` | nothing | no |
| `ask` | `ask` | the story's branch | `question asked on the pull request` | the question | yes |
| `pr` | `answers` | the story's branch | `comments from the pull request` | nothing | yes |
| `reject` | `reject` | the checked-out branch | `illegal change <a> → <b>, moved back` | a note, with a pull request | yes |
| `expired` | `expired` | the story's branch | `run expired` | a stall note, with a pull request | yes |
| `run` | `run`, then `stage.run` | the work item's branch, or main when it hands over to `merged` or `_discard` | `intake starts`, `merge main`, `<stage> → <next>` and others ([chapter 8](../08-stage-run/README.md)) | stall notes | on a stall |
| `duplicate` | `_duplicate` | nothing | | nothing | no |
| `error pr-lookup` | `_pr_lookup` | nothing | | nothing | no |

Every commit is followed by a push of the same branch (`ops.commit_and_push`). The subject prefix is `acceptance <feature folder>:` for an acceptance. `run` is the exception to one commit per handler: at the first stage it pushes the new branch, merging the main branch adds a commit, and the stage's result is a third.

### `merged`: the human accepted

1. Check out the main branch and fast-forward it to `origin/main`; raise if it cannot.
2. Sum the cost records for the path the event named, before anything moves ([chapter 14](../14-runtime/README.md)).
3. A story: append `done (pull request merged); cost: …`, set `stage: done` and `blocked: null`, and `git mv` the file from `ongoing/` to `done/`. An acceptance: append the same entry and set `stage: done` and `outcome: accepted`; the file stays where it is.
4. Commit on the main branch and push; delete the work item's branch, locally and on the remote.

The handler trusts the event and does not read the pull request again. The file it edits is the main branch's copy, which the merge brought from the branch.

### `closed`: the human closed the pull request

An acceptance, recognized by its path, goes to `_refused`. A story is read from its branch: at `accept` it goes to `_sent_back`, anywhere else to `_discard`. A story whose file is missing on its branch reads as `ready`, and is discarded.

**`_refused`**, for an acceptance:
1. Read the report from the acceptance branch; raise if it is missing.
2. Read the human comments posted after `comments_seen`; their bodies, joined with spaces, are the reason, or `no reason given`.
3. Check out the main branch. Write the branch's report there with `stage: done` and `outcome: refused`, the line `Refused by the human on <date>: <reason>` as the first paragraph under `## Verdict`, and the entry `done (pull request closed by the human); cost: …`. Only the report is written: the proposed drafts on the branch are dropped.
4. Commit on the main branch and push; delete the branch.

**`_sent_back`**, for a story at `accept`:
1. Reopen the pull request. If GitHub refuses, return a failure: "pull request *n* could not be reopened; nothing changed".
2. Mark it as a draft again, and check out the story's branch.
3. Copy the new human comments into the log (`_copy_comments`, under `pr` below).
4. Set `stage: doing` and add 1 to `round`.
5. If a reason was given (`_reason_given`, defined in [chapter 5](../05-stage-machine/README.md)) and `round` is within `demo`'s `max_rounds`: clear `blocked`, commit and push. No log entry records the send-back; the commit subject does, and the human's comments are the last entries the coder reads.
6. Otherwise, append and post the question, set `blocked: asked`, commit and push. The question begins "The pull request was closed without a comment." or, past the cap, "This story has now been sent back *n* times, more than *cap*.", followed by `SENT_BACK_QUESTION`:

   > What should happen? 1. Comment what should change; the coder reworks the story with exactly that. 2. Close the pull request again to discard the story: it goes back to `drafts/` as you wrote it, and its branch is deleted. 3. If closing was a mistake: mark the pull request ready for review and merge it, which accepts the story as it is.

   Each option is an existing path of the machine.

**`_discard`**, for a story at any other stage:
1. Check out the main branch, `git mv` the story from `ongoing/` to `drafts/`, commit and push.
2. Delete the branch. The pull request stays closed.

### `ask`: post a question

1. Find the story's branch. Without a branch or a pull request, return handled, "question without a pull request on …", and do nothing.
2. If `blocked` is already `asked`, return `NOTHING`.
3. Check out the branch. If `attempts` has reached `max_attempts`, the question is a new log entry: "Stage *s* stalled *n* times. The last time: *last entry* Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to stop instead." Otherwise the question is the last log entry, verbatim, prefix and all: the agent's question, possibly followed by the form's findings or the round-cap question.
4. Post the question, set `blocked: asked` and `comments_seen` to the comment count after the post, commit and push.

### `pr`: read the human's comments

The handler is `answers`:
1. Find the branch; without one, return handled, "comments without a branch on …". If the pull request has no more comments than `comments_seen`, return `NOTHING`.
2. Check out the branch and copy the new human comments (`_copy_comments`): every comment after the first `comments_seen` that does not carry the factory's marker becomes an entry `human (pull request comment, <YYYY-MM-DD>): <body>`, and `comments_seen` becomes the total count.
3. If the story was `blocked: asked` and at least one human comment was copied, clear `blocked`; if `attempts` was at the cap, set it to 0. A comment at a gate is only recorded.
4. Commit and push.

### `reject`: an illegal stage change

1. On the branch the checkout is on, set `stage` back to the old value and append `illegal stage change <a> → <b>, moved back`.
2. If the work item has a pull request, post: "The stage was changed from *a* to *b*, which `stages.yml` does not allow; it is back at *a*."
3. Commit with a subject that contains `moved back`, which exempts it from the next evaluation's `reject`, and push.

### `expired`: an agent run died

1. Remove the run record. Find the story's branch; raise if there is none.
2. Check out the branch, add 1 to `attempts`, and append `run expired: the run that held it ended without finishing (lease over or machine restarted)`.
3. If there is a pull request, post: "Stage *s* stalled: its run ended without finishing (attempt *n* of *max*). Retrying."
4. Commit and push. The stage runs again on a later tick, or the attempts cap asks.

### `run`: a stage is due

1. Read the work item as the watcher did (`stage.current`): from its branch, else from `origin/main`; a due acceptance is synthesized at stage `feature`.
2. If the stage's agent is no longer the one the event named, the work item has moved on since the evaluation: return `NOTHING`.
3. If the work item has a pull request, read its state. A closed one is handled as `closed`, a merged one as `merged`.
4. Otherwise run the stage protocol ([chapter 8](../08-stage-run/README.md)).

`duplicate` and `error pr-lookup` return handled, with one sentence for the tick's log: "two stories with id …" and "gh could not answer for …; is gh logged in?".

### The tick's memo

`src/factory/tick.py` decides whether an event needs handling, calls the handler, and remembers the result in `.git/factory-tick.json`: `{"line": …, "head": …, "failures": …}`, where `head` is the checkout's `HEAD` when the tick evaluated, before the handler ran.

`needs_handling(event, memo, head, work items)`:

| Event | Needs handling when |
| :- | :- |
| `idle`, `busy` | never |
| `pr <path> OPEN <n>` | *n* exceeds the work item's `comments_seen`; the memo is not consulted |
| any other | it differs from the remembered event, or `HEAD` differs from the remembered `head`; or both match and 0 < `failures` < 3 |

Because `head` is taken before the handler runs, a handler that commits moves `HEAD`, and the memo never stops it from running again; the next evaluation's event has changed anyway. The memo stops exactly the repeats of results that changed nothing (`NOTHING`, `duplicate`, `error pr-lookup`, an `ask` without a pull request), and it counts failures.

For a `pr` event, `only_own_comments` then fetches the comment bodies and skips the event when every unseen comment is the factory's own, by the marker or the old `factory:` prefix. That is the case right after the factory posts the cost table at the gate: handling it would only raise `comments_seen`, and push to the branch just when the human is invited to merge. If `gh` fails here, the event is handled.

`handle_line` then:
1. logs `dispatch: <event>`, and calls the handler; any exception becomes a failure, `Handled(False, "<type>: <message>")`;
2. appends a cost record if an agent ran ([chapter 14](../14-runtime/README.md));
3. on success, stores the event and `head` with `failures: 0`, logs `done: <summary>`, posts the cost table if the work item has just reached a gate, and exits with code 3, which tells the scheduler to tick again at once;
4. on failure, stores the failure count, +1 if event and `head` are unchanged, else 1, and logs `failed (n/3): <summary>`. At `MAX_FAILURES = 3`, `give_up` posts on the work item's pull request:

   > The factory failed 3 times on `<event>` and has stopped retrying it. Last failure: *summary*. A human needs to look at the machine; a new commit on the branch makes the tick try again.

   and the tick exits with code 1. A tick with nothing to handle exits with 0.

The entrypoint deletes the memo at every start ([chapter 14](../14-runtime/README.md)), so a restart retries an event the factory had given up on.

### Shared helpers

`src/factory/ops.py` holds what the handlers share:

| Helper | Does |
| :- | :- |
| `edit(path, *entries, **fields)` | sets state fields and appends log entries in the working tree, in one write |
| `post(pr, body)` | comments, then returns the pull request's comment count, own post included |
| `commit_and_push(branch, subject)` | `git add -A`, commit, `git push -u origin <branch>` |
| `to_main`, `to_branch` | check out and fast-forward; raise if the fast-forward fails |
| `stall(path, branch, reason)` | `attempts` + 1, the stall entry, the stall note on the pull request, commit and push |
| `story_branch`, `meta`, `max_attempts`, `max_rounds`, `subject` | lookups with v1's defaults (2 and 2) |

`src/factory/repo.py` holds the Git steps. A step that may fail for a reason outside the factory (a branch that cannot fast-forward, a conflict, a remote that refuses) returns `False`; a step that fails only when the factory itself is wrong raises. Only the stage protocol turns a `False` into a stall; the handlers above turn it into a raise, and so into a counted failure.

`src/factory/github.py` wraps the `gh` command line. `GitHub` has `view`, `comment`, `reopen`, `to_draft`, `create_draft`, `find`, `edit_body` and `ready`; any non-zero exit raises `GitHubError`, except `reopen`, which returns `False`, and `find`, which returns `None`. `comment` appends the marker `<!-- factory -->` after a blank line. `is_own(body)` recognizes the factory's comments by the marker, or by the prefix `factory:` that comments had before the marker existed.

`tests/test_dispatch.py` runs every handler against a throwaway repository with a bare `origin`, a fake GitHub that records posts, drafts and state changes, and a fake agent that returns a chosen outcome and edits chosen files: 38 tests. `tests/test_tick.py` holds 23 more for the memo, the lock and the failures. Design decision: 2026-10-05 (the dispatcher is code).

> [!WARNING]
> **v1 limit:** `comments_seen` is a count, not a set. Every handler that posts sets it to the total after its own post, so a human comment made since the last read is counted as seen and never copied. While the stages work, a stall note or an expired agent run's note can swallow a comment that way. Deleting a comment lowers the count, so the next copy skips one.

> [!WARNING]
> **v1 limit:** posts can repeat. `ask`, `expired`, `reject`, `_sent_back` and `ops.stall` post before they write the state. A kill between the post and the file write loses the state and the next tick posts again; and if `ops.post`'s second call, the comment count, fails after a successful comment, the handler fails and each retry posts again, up to three times plus the give-up message. (A kill after the write is safe on a story's branch, because the next tick commits the leftovers; a killed `reject` on main leaves main dirty, and the tick stops with "working tree is dirty on main".)

> [!WARNING]
> **v1 limit:** `pr` events bypass the memo. A persistent failure of `answers`, such as a branch that cannot fast-forward, is retried on every tick, and from the third failure on, every tick posts the give-up message again. Each post raises the comment count while the human's unread comment keeps the event alive, so the loop does not end by itself.

> [!WARNING]
> **v1 limit:** the give-up message's promise is false. The memo compares the checkout's `HEAD`, and a commit pushed to the work item's branch moves only `origin/…`, never the local branch the checkout is on. What makes the tick try again is a changed event, a new commit on the main branch while the checkout sits there, or a restart. And `give_up` needs a pull request: a failure on a work item that has none yet, such as a failing first stage, reaches only the tick's log.

> [!WARNING]
> **v1 limit:** a close at the gate can be lost silently. `_sent_back` reopens the pull request and marks it a draft before it checks out the branch. If the checkout then fails, the next evaluation finds an open pull request at `accept` with no new comments, `needs_handling` says no, and nothing tells the human that their close was undone.

> [!WARNING]
> **v1 limit:** `gh` is reached three ways: the watcher's `gh_pr_state`, the `GitHub` wrapper, and the tick's `pr_comment_bodies`, each with its own error handling. A change of hosting service touches all three.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - one handler per event kind; each bookkeeping handler ends in at most one commit and one push;
>   - the handlers' meanings: merge archives; close refuses an acceptance, sends back at the gate, discards elsewhere; a close at the gate without a reason asks with three options that are all existing paths; an answer unblocks; at the attempts cap any answer retries;
>   - the pull request's state is read before every agent run;
>   - a handler's exception is a counted failure, retried on the same event and state, then reported to the human;
>   - the memo is keyed by the event and the repository state before the handler; it suppresses repeats of handlers that changed nothing, and bounds retries.
> - **Incidental to v1:** `gh`; the subject strings; the exit code 3; three as the failure cap.
> - **Watch for:**
>   - track the human's comments by identity (comment ids), not by count;
>   - write the state before any effect on the hosting service, or make those effects idempotent with a key, so a retry or a kill cannot double-post, and a failed step after a reopen cannot lose the human's close;
>   - bound every event by the failure cap, comment events included;
>   - key the retry to the work item's own branch, so a fix pushed there is noticed;
>   - report every failure where the human looks, with or without a pull request;
>   - one client for the hosting service, faked once in tests;
>   - an event kind without a handler should raise, not return "nothing to do".
