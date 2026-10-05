---
name: stage-tests
description: Stage instructions for `tests`. Preloaded into the tester agent; not invoked directly.
---

0. If the task says `Mode: a test change the human approved`, your job is only that change: edit exactly the named test as the human's answer says, run `make test` once, and end with `doing` and an entry saying what you changed and why. Skip the steps below.
1. Read the ticket and the files `CLAUDE.md` names under *Tests* and *Architecture*. Nothing else: not other tickets, not `FEATURE.md`, not `factory/`, not `.claude/`. Write the tests for every acceptance criterion as the role skill describes, where `CLAUDE.md` says tests live.
2. Run `make test 2>&1 | tail -5` once, to see the tests fail for the right reason: failures, or collection errors because the modules under test do not exist yet. Do not run the tests again, not on a subset and not with other flags, to get counts; the factory runs `make test` after you and logs its last line.
3. Run `make lint`; it must be green, and the factory checks it again. Skip the type check in this stage: it cannot pass while the modules under test do not exist, and the coder's `make check` covers the tests afterwards.
4. If you had to interpret a criterion, that is a question (R8): end with `question` instead of moving on.
5. End with `doing` and an entry: which criterion maps to which test function, one line each (`criterion 3: tests/…::test_name`), the files you created, and the modules the test runner could not import. The branch now has red tests on purpose; that is the coder's specification.
