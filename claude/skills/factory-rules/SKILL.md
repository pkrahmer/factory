---
name: factory-rules
description: The pipeline rules every stage agent works under. Preloaded into every stage agent; not invoked directly.
---

# Pipeline rules

These rules apply to every agent in every stage. Stage-specific instructions are in the stage skills; role-specific instructions in the role skills. A ticket is a user story: `factory/features/<F0001-slug>/ongoing/<F0001-S0003-slug>.md`; its id is the file stem without the slug, `F0001-S0003`.

Everything around your work is the factory's: it checks out the branch, opens the pull request, writes the ticket's frontmatter and log, commits, pushes, changes the stage and talks to GitHub. You do the stage's work and end with an outcome.

R1. Git is the only truth. A stage starts from the committed state and carries nothing over from earlier runs.

R2. Every stage ends with an outcome and a log entry. The outcome is one of the stages your task lists under *Allowed outcomes*, `question` (R8), or `stuck` when you cannot finish; the entry is the text of your log entry, without a number: what you did, why, what you rejected, what is open, and for `stuck` where you stopped. The factory appends the entry, commits everything you left in the working tree, pushes and moves the ticket.

R3. One ticket at a time. You work on exactly the ticket named in your task. You do not touch other tickets, and you do not touch the feature's `FEATURE.md`.

R4. The ticket is the memory. Everything the next stage needs is in the ticket, through your entry: what you did, why, what you rejected, what is open. Code is not pasted into the ticket; paths and commit hashes are. The reverse holds too: tickets and criteria are not named in code or tests. Git links code to tickets through the commit subject; a lasting reason is cited from `docs/decisions.md`.

R5. Ticket structure: the frontmatter and `## Log (append only)` are the factory's; you never edit them, and an edit there is dropped. `Assignment` is the current meaning of the task and is rewritten when the log changes it; a criterion the human's answer adds goes before the two closing ones (`make check` stays green, `docs:`), which stay last. No clock time in the ticket: git has it. The folder is the lifecycle: `drafts/` is the human's, `ongoing/` is the pipeline's, `done/` the archive; you never move a ticket.

R6. Your task names the facts you need: the stage, the allowed outcomes, the branch, the pull request, the round, and whatever your stage skill says the factory tells you. Take them from the task; do not work them out from git or GitHub.

R7. The stage changes by your outcome and nothing else. The factory checks it against `next` in `stages.yml`. A forward outcome waits for the stage's checks, which the factory runs itself after you (`make check`; for the tests stage `make lint`): red holds the ticket at your stage and counts as a stall.

R8. To ask the human, end with `question` and the question as your entry: precise, with the options you see and the one you would choose. The factory posts it on the pull request; the answer comes back as a log entry and the stage runs again. Do not guess on anything listed under "Not without asking" in `CLAUDE.md`.

R9. Tests are written by the tester stage from the acceptance criteria. The coder never edits tests. A wrong test is a question (R8), not a fix; when the human's answer calls for a test change, the coder ends with `tests` and names the test and the change, and the tester makes exactly that change.

R10. One branch per ticket, checked out for you. You never push, check out, switch, merge, pull or call `gh`. The coder commits its work as it goes; every other agent leaves its changes in the working tree for the factory's commit. A ticket's work reaches `main` only through the human's merge of its pull request; `docs/branching.md` has the whole picture.

R11. `make check` must be green before you hand forward; run it yourself while you work. `make check` means that command: if `make` or one of its tools is missing, end with `stuck` and say which; running the Makefile's commands by hand is not the gate, and installing tools is not the stage's business. The loop checks the machine before it starts.

R12. Rework rounds (review → doing, docs → doing, demo → doing, and the human's close at `accept`) share the ticket's `round`, capped by `max_rounds` in `stages.yml`. Your task names the round; on a rework round the latest entries name the findings. When the cap is passed, the factory asks the human instead of looping.

R13. Nothing is started without the human: no story enters `ongoing/` but by their hand, no new features, no scope beyond the assignment. The feature acceptance may propose stories as files in `drafts/`, on its own branch, which reach `drafts/` only when the human merges; nobody else writes there. If the assignment is wrong, ask.

R14. Commit subjects start with `ticket <id>:`. The factory writes them, except for the coder's own work commits. Branch, pull request and commits of one ticket are its unit; closing the pull request without merging discards all of it at once.

R15. The pipeline's own files — `factory/stages.yml`, `factory/TICKET.md`, `factory/FEATURE.md`, every feature's `FEATURE.md`, `drafts/`, `done/` and `.claude/` — change only with the human's commit or on their explicit instruction. You write your own ticket (outside its frontmatter and log) and your lane from `stages.yml`, nothing else: a hook refuses an edit outside the lane, and the factory undoes any other write after the stage.
