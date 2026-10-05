---
name: stage-doing
description: Stage instructions for `doing`. Preloaded into the coder agent; not invoked directly.
---

1. Claim the ticket (R6), commit.
2. Read the ticket and the files its last log entries name (the tester's test files; on a rework round, the findings). Nothing else: not other tickets, not `FEATURE.md`, not `factory/`, not `.claude/`. If `round` is greater than 0, address exactly the listed findings, nothing more.
3. Implement as the role skill describes until `make check` is green. A test that cannot pass against the ticket (contradicts the interface, is non-deterministic) is a question (R8, R9): describe the test and the options, set `blocked: question`, clear the claim, commit, push, stop. When you arrive with the human's answer in the log and it calls for a test change, do not touch the test: append a log entry naming the test and the change in one sentence, set `stage: tests`, clear the claim, commit with subject `ticket <id>: doing → tests (test change approved)`, push, stop. The tester makes the change and sends the ticket back.
4. Commit as you go with messages `ticket <id>: feat(<layer>): <what>`. One commit per coherent change is fine.
5. Refactor, once. With `make check` green, read your own diff (`git diff main...HEAD -- . ':!factory' ':!tests'`) the way a reviewer would: rename what is unclear, simplify what is convoluted, remove duplication and dead code. Add nothing. Behaviour stays the same, tests stay untouched, `make check` is green again afterwards. Commit separately as `ticket <id>: refactor(<layer>): <what>` so the reviewer sees feature and clean-up apart. If nothing needs changing, say so in the log entry below. A restructuring beyond this ticket is a new ticket, not a refactor (R13).
6. Append a log entry: what you built (paths), the main design decision and the alternative you rejected, anything you noticed but did not touch.
7. Rewrite `## Assignment` only if a log entry changed the meaning of the task; then update its "as of" heading.
8. Set `stage: review`, clear the claim, commit with subject `ticket <id>: doing → review`, push.
