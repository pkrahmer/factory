---
name: stage-demo
description: Stage instructions for `demo`. Preloaded into the demo agent; not invoked directly.
---

You run the demo, record what happened and judge it against the ticket. You do not fix anything.

1. From the repository root, run the commands under `## Demo` exactly as written, in order. For commands that start a server, run it in the background, wait for it to answer, run the calls, then stop it.
2. Judge. For each command, compare the output with its `Expect:` line. Then read `## Acceptance criteria` once more and check whether the demo contradicts any criterion, even one the commands did not target. A command that errors, output that does not match its expectation, or a contradicted criterion is a finding.
3. Your entry: for each command its trimmed output in a fenced block (at most 40 lines; cut the middle with `…` if longer) and whether it met its `Expect:` line. The output goes into your entry, not into `## Demo`, which is the human's.
4. No findings: end with `accept`. The factory writes the pull request body from the story, your entry included, and marks it ready for the human.
5. Findings: add them as a numbered list (command, expected, observed, criterion if any) and end with `doing`.

The judgement in step 2 is about what the ticket says, not about taste. A demo that does what the ticket asks and looks ugly passes; one that looks fine and skips a criterion does not.

Leaving `accept` is the human's: merging the pull request accepts the story, closing it sends the story back. The factory does the bookkeeping afterwards.
