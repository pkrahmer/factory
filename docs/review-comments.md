# Review comments on the diff

The plan for making the human's inline review comments count. Built in one pull request after `docs/fewer-commits.md`; the next end-to-end run verifies it (paths 14 to 16 of the hardening mode in `demo/README.md`). Where the build had to differ from the plan, *As built* at the end says how and why.

## What is wrong today

The watcher's pull request lookup is `gh pr view <n> --json state,comments`. `comments` are the pull request's *issue* comments: the conversation under the description. A comment the human writes on a line of the diff is a *review* comment and comes from another endpoint; a review the human submits ("Comment", "Request changes", "Approve") from a third. Neither is read. The demo's closing paragraph says so honestly ("Nobody answers comments while the story waits here"), and the human's only tools at the gate are merge and close-with-free-text. The free text then names a file and a line in prose that GitHub would have carried for free.

## What GitHub offers

- `GET repos/{o}/{r}/pulls/{n}/comments` — review comments: `id`, `path`, `line` (or `original_line` when the diff moved), `body`, `diff_hunk`, `in_reply_to_id`, `user`, `created_at`.
- `GET repos/{o}/{r}/pulls/{n}/reviews` — reviews: `id`, `state` (`COMMENTED`, `CHANGES_REQUESTED`, `APPROVED`, `DISMISSED`), `body`, `submitted_at`.
- `POST …/pulls/{n}/comments/{id}/replies` — a reply in the same thread.
- Resolving a thread (`resolveReviewThread`) is GraphQL only. It works through `gh api graphql` in the container and on the PC; it does not work in the cloud sandbox where the factory is written, so it is verified by the PC session, and the design does not depend on it (see *Who resolves*).

## The three paths

**1. "Request changes" is the rework path.** The human submits a review with state `CHANGES_REQUESTED`, usually with inline comments. The dispatcher treats it like a close with a comment at `accept`, without the close: the pull request stays open and goes back to draft (`gh pr ready --undo`), the story goes to `doing` with `round + 1`, and the findings are the inline comments, copied into the log one entry each as `human (review comment, <path>:<line>): <body>` with the quoted diff line, plus the review body if any. The coder addresses exactly those (the rework rule it already follows for the reviewer's findings), and **replies inline to every comment** — "fixed in <sha>: <one line>" or "kept: <reason>" — before handing to review. The reviewer checks that every human comment has a reply and that each "fixed" is true. Then docs, demo, ready, as always. The round cap applies; at the cap the usual question goes on the pull request.

**2. "Comment" is a question, and the reviewer answers.** A review with state `COMMENTED`, or inline comments without a review, at `accept`: the dispatcher starts the reviewer agent in **answer mode** — a task message that names the comments and says: read the diff, the story and the question; reply inline, factual, two to five sentences; change nothing. One run, roughly ten turns. The reviewer is the right voice: it knows the diff as well as the coder and has already judged it, without the author's urge to defend. If the answer does not satisfy the human, they request changes (path 1) or close. The story stays at `accept`; the pull request stays ready.

**3. Comments while the stages work.** The watcher polls a pull request only while the human is expected to act, and that stays (the tick costs nothing when idle). But the dispatcher already asks GitHub for the pull request's state before every stage start (closed-in-flight detection). It now also fetches review comments newer than the ones the story has seen and hands them to the agent in the task message under `Notes from the human:` with path, line and text, and copies them into the log as `human (review comment while <stage>, <path>:<line>): <body>`. The agent reads them as what they are: the human steering mid-flight. A note that contradicts the story is a question (R8), not an order; the agent asks.

`APPROVED` means nothing to the pipeline: accepting is merging. The demo's closing paragraph is rewritten to say what each action does now.

## Who resolves

The coder replies; the human resolves. "Resolve conversation" is the reviewer's word for "I have read your answer and I am satisfied", and that reviewer is the human. The pipeline never resolves a thread. This keeps the one GraphQL-only call out of the agents' hands and keeps the "n of m conversations resolved" counter on the pull request meaningful to the one person who reads it.

## Changes, file by file

All in this repository.

1. `src/factory/watch.py`, `gh_pr_state`: read `state` from `gh pr view`, review comments from `pulls/{n}/comments`, reviews from `pulls/{n}/reviews`. The count in the `pr` line becomes the sum of issue comments and review comments, so `comments_seen` keeps one meaning (everything the human wrote that the pipeline has read). The newest review's state rides on the line: `pr <path> OPEN <n> <REVIEW>` where `<REVIEW>` is `NONE`, `COMMENTED`, `CHANGES_REQUESTED` or `APPROVED`, decided from the reviews newer than the story's last hand-over to the human (the demo's `demo → accept` commit time; reviews from before a rework are history). `PrState` grows a third field; every caller in `tests/test_watch.py` adjusts.
2. `src/factory/tick.py`, `needs_model`: a `pr` line needs the dispatcher when the count exceeds `comments_seen` **or** `<REVIEW>` is `CHANGES_REQUESTED` and the story is still at `accept` (a review with no comments has no count to exceed).
3. `claude/skills/factory/SKILL.md`:
   - `pr … OPEN <n> <REVIEW>` at `accept`: copy new issue and review comments into the log (review comments with path and line and the quoted diff line); then by `<REVIEW>`: `CHANGES_REQUESTED` → the rework bookkeeping (draft again, `round + 1`, `stage: doing`, no close, no reopen), `COMMENTED` or inline comments without a review → start the reviewer in answer mode with the new comments, `NONE`/`APPROVED` → nothing more.
   - `run <agent> …`: before starting an agent, fetch review comments newer than `comments_seen` (the dispatcher knows the ids it has copied: it copies in order and the log carries the ids), copy them into the log, and add `Notes from the human:` to the task message.
   - `closed` at `accept` is unchanged: a close still works, and a close without a comment still gets the three-option question — the review path is the better way, not the only one.
4. `claude/skills/stage-doing/SKILL.md`: on a rework round whose findings are the human's review comments, reply inline to each (`gh api repos/{o}/{r}/pulls/{n}/comments/{id}/replies -f body=…`) with `fixed in <sha>: …` or `kept: …`; a `kept` needs a reason the story supports, else it is a question. The reply ids go into the log entry.
5. `claude/skills/role-reviewer/SKILL.md`, checklist 5 (ticket hygiene): on such a round, every human review comment has a reply, and every `fixed` reply is true in the diff. A missing or false reply is a finding.
6. `claude/skills/stage-review/SKILL.md`: the answer mode — a task message beginning `Answer mode:` means: no claim, no stage change, no verdict; read the diff and the story, reply inline to each listed comment, append one log entry `reviewer (answers): <n> comments answered`, commit the ticket, push, stop.
7. `claude/skills/stage-demo/SKILL.md`: the closing paragraph of the pull request body becomes, word for word: "Merge to accept. Request changes with comments on the lines that should change, and the coder will address exactly those and reply to each; a plain comment is answered by the reviewer without changing anything. Close with a comment to send the story back without line references; a close without a comment is answered with a question."
8. `claude/skills/factory-rules/SKILL.md`, R8: the human's review comments are answers and instructions like pull request comments; a note that contradicts the story is a question, not an order.
9. `claude/settings.json`: the allow list has `Bash(gh pr *)` but not `gh api`, which the reads and the replies need. Add `Bash(gh api repos/*)`; `gh api graphql` stays out, so no agent can resolve a thread.
10. `docs/WATCH_CONTRACT.md`: the `pr` line's new shape, the two endpoints among the inputs, the meaning of `comments_seen`.
11. `docs/decisions.md`: one entry — review comments are read; request-changes is the rework path, comment is a question the reviewer answers, approve means nothing, the pipeline never resolves a thread.
12. `demo/README.md`, hardening mode: three paths for the next run — a request-changes review with two inline comments (one fixed, one kept with a reason), a plain inline question at the gate answered by the reviewer, and an inline comment while the tester works that the coder then sees as a note.

## What stays as it is

- Merge is the only acceptance; `APPROVED` is ignored.
- Close keeps working as before, for the human who prefers it or has nothing line-specific to say.
- The watcher polls GitHub only while the human is expected to act; mid-flight comments are picked up by the dispatcher at the next stage start, which is at most one stage later.

## Verification

- `make check` in the factory: the new `PrState` shape, the `needs_model` rule for `CHANGES_REQUESTED`, the line format.
- The next end-to-end run: the three paths above, each once, with the log entries, the inline replies and the pull request's "conversations" counter checked by the human (resolve by hand, see that the pipeline never did it).

## As built

Where the build differs from the plan above, and why:

1. **Review texts count too.** `comments_seen` counts the conversation, the comments on the diff, *and* the text of every submitted review. A "Comment" review with text but no line comment would otherwise never raise the count and would go unanswered.
2. **The pipeline's own posts start with `factory:`.** That covers the coder's replies (`factory: fixed in <sha>: …`, `factory: kept: …`) and the reviewer's answers, like the tick's cost table. The dispatcher never copies them, and the tick ignores them when they are all that is unseen. Without a mark, the dispatcher would copy the agents' replies back into the log as the human's.
3. **A change request stands until an approval.** The review verdict is not simply the newest review's state. A plain comment after "Request changes" does not lift the request (as on GitHub), while a comment after an approval does count as a question again. Dismissed and pending reviews count for nothing.
4. **Only the story's own hand-over counts.** The hand-over is the last `… → accept` on the branch's first-parent line, so another story's hand-over, merged in with `main`, does not count.
5. **A change request is dispatched once**, even without a comment, and only for a story at `accept`. It is remembered like any other line (line plus `HEAD`), so a failing dispatcher cannot loop. The cost table cannot hide it either. On an acceptance, a review means nothing.
6. **A change request without any comment or text** is asked about, like a close without a comment, so the coder never guesses.
7. **At the gate, a conversation comment is a question too.** The demo's closing paragraph promises that "a plain comment is answered by the reviewer". The reviewer answers a conversation comment or a review's text with `gh pr comment`, quoting the question's first words.
8. **Mid-flight, every new writing becomes a note**, not only comments on the diff. `comments_seen` is one number, so what it counts must all be copied.
9. **The log carries ids**: `human (review comment <id>, <path>:<line>)` and `human (review <id>, <state>)`. The dispatcher tells new from copied by them, and the coder replies to them.
10. **The contract's version is now 5**, as `docs/WATCH_CONTRACT.md` asks for a change of the `pr` line (`template/stages.yml` too). A repository's own `factory/stages.yml` is the human's to change; nothing reads the field.
