---
name: factory-rules
description: The pipeline rules every stage agent works under. Preloaded into every stage agent; not invoked directly.
---

# Pipeline rules

These rules apply to every agent in every stage. Stage-specific instructions are in the stage skills; role-specific instructions in the role skills. A ticket is a user story: `factory/features/<F0001-slug>/ongoing/<F0001-S0003-slug>.md`; its id is the file stem without the slug, `F0001-S0003`.

R1. Git is the only truth. A stage starts from the committed state and carries nothing over from earlier runs.

R2. Every stage ends with a commit, including a failed one. If you cannot finish, write what happened to the ticket log, leave the stage as it is, and commit.

R3. One ticket at a time. You work on exactly the ticket named in your task. You do not touch other tickets, and you do not touch the feature's `FEATURE.md`.

R4. The ticket is the memory. Everything the next stage needs is in the ticket: what you did, why, what you rejected, what is open. Code is not pasted into the ticket; paths and commit hashes are. The reverse holds too: tickets and criteria are not named in code or tests. Git links code to tickets through the commit subject; a lasting reason is cited from `docs/decisions.md`.

R5. Ticket structure: the frontmatter is for the watcher and holds exactly `stage`, `pr`, `blocked`, `comments_seen`, `claimed_at`, `round`, `attempts`; nothing else goes there. `Assignment` is the current meaning of the task and is rewritten when the log changes it; a criterion the human's answer adds goes before the two closing ones (`make check` stays green, `docs:`), which stay last; `Log` is append-only; no clock time, git has it. Stage changes are not recorded in the ticket either: the commit subject names them. The folder is the lifecycle: `drafts/` is the human's, `ongoing/` is the pipeline's, `done/` the archive; a story is in exactly one of them.

R6. Claim before work: set `claimed_at` (from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from memory) in the frontmatter and commit with subject `ticket <id>: claim for <stage>`, **without pushing**, then start. The commit that ends the stage clears the claim, whether it changes the stage or asks (R8). Make it with `git commit --amend` while the claim commit is still `HEAD`, so the claim commit and the closing commit are one; then push. Work commits in between (the coder's `feat` and `refactor` commits) are ordinary commits on top of the claim commit; then the closing commit is a normal one and the claim commit stays, which is harmless. Never amend a pushed commit: intake and the acceptor push their claim, because the pull request needs the branch on GitHub, and close with a normal commit. A claim older than the lease in `stages.yml` is considered dead.

R7. A stage change is one edit of the `stage` field, only to a stage listed under `next` for the current one. The watcher rejects anything else. A stage agent never moves the file: the human moves a story from `drafts/` to `ongoing/`, the dispatcher moves it to `done/` when the pull request is merged.

R8. To ask the human, write the question as a log entry, set `blocked: question`, clear your claim, commit as R6 says (an amend of the claim when it is still `HEAD` and unpushed), push, and stop. The dispatcher posts it on the pull request and sets `blocked: asked`; the answer comes back as a log entry and `blocked` is cleared. The human's comments on the diff and their reviews are answers and instructions just like their pull request comments, and the dispatcher copies them into the log the same way. A note that contradicts the story is a question, not an order. Do not guess on anything listed under "Not without asking" in `CLAUDE.md`.

R9. Tests are written by the tester stage from the acceptance criteria. The coder never edits tests. A wrong test is a question (R8), not a fix; when the human's answer calls for a test change, the coder sends the ticket back to `tests` and the tester makes exactly that change.

R10. One checkout, one branch per ticket (`ticket/<file stem>`, so `ticket/F0001-S0003-slug`), created by intake together with a draft pull request. Every stage after intake works on that branch, commits code and ticket together, and pushes before it ends. A ticket's work reaches `main` only through the human's merge of its pull request, always as a merge commit. Besides those merges, only the human (drafts, promotions) and the dispatcher (archive, discard, an acceptance's outcome) commit on `main`, never a stage agent. `main` is green at every commit; `docs/branching.md` has the whole picture.

R11. `make check` must be green before a stage changes the stage, with one exception: the tests stage leaves the new tests red on purpose and must be green on everything else. Green is a precondition, not a result. `make check` means that command: if `make` or one of its tools is missing, the stage stops and asks (R8); running the Makefile's commands by hand is not the gate, and installing tools is not the stage's business. The loop checks the machine before it starts.

R12. Rework rounds (review → doing, docs → doing, demo → doing, accept → doing when the human closes the pull request) share the ticket's `round` counter and are capped by `max_rounds` in `stages.yml`. When the cap is hit, the stage asks the human instead of looping.

R13. Nothing is started without the human: no story enters `ongoing/` but by their hand, no new features, no scope beyond the assignment. The feature acceptance may propose stories as files in `drafts/`, on its own branch, which reach `drafts/` only when the human merges; nobody else writes there. If the assignment is wrong, ask.

R14. Commit subjects start with `ticket <id>:`, so `ticket F0001-S0003:`. Branch, pull request and commits of one ticket are its unit; closing the pull request without merging discards all of it at once.

R15. The pipeline's own files — `factory/stages.yml`, `factory/TICKET.md`, `factory/FEATURE.md`, every feature's `FEATURE.md`, `drafts/`, `done/` and `.claude/` — change only with the human's commit or on their explicit instruction. Stage agents write their own story file and their lane from `stages.yml`, nothing else; a hook on each agent enforces it.
