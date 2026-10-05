---
name: stage-tests
description: Stage instructions for `tests`. Preloaded into the tester agent; not invoked directly.
---

0. If the ticket comes from `doing` (the log ends with a question about a test, the human's answer, and the coder's hand-back), your job is only that change: claim as in step 1, edit exactly the named test as the answer says, run `make test` once, log what you changed and why in one entry, set `stage: doing`, clear the claim, then `git add -A && git commit --amend -m "ticket <id>: tests → doing (test changed as approved)" && git push`. Skip the steps below.
1. Claim the ticket (R6): commit with subject `ticket <id>: claim for tests`, do not push.
2. Read the ticket and the files `CLAUDE.md` names under *Tests* and *Architecture*. Nothing else: not other tickets, not `FEATURE.md`, not `factory/`, not `.claude/`. Write the tests for every acceptance criterion as the role skill describes, where `CLAUDE.md` says tests live.
3. Run `make test 2>&1 | tail -5` once. The expected result is red in one of two shapes: failures, or collection errors because the modules under test do not exist yet. Record the last line verbatim and the names of the modules the test runner could not import. Do not run the tests again, not on a subset and not with other flags, to get counts for the log; the coder's run will produce them.
4. Run `make lint`; it must be green. Skip the type check in this stage: it cannot pass while the modules under test do not exist, and the coder's `make check` covers the tests afterwards.
5. Append a log entry: which criteria map to which test functions, and the files you created. If you had to interpret a criterion, that is a question (R8): stop there instead of moving on.
6. Set `stage: doing`, clear the claim, and commit tests and ticket together into the claim commit: `git add -A && git commit --amend -m "ticket <id>: tests → doing" && git push`. The amend folds the claim commit into this one and replaces its message. The branch now has red tests on purpose; that is the coder's specification.
