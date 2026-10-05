---
name: stage-demo
description: Stage instructions for `demo`. Preloaded into the demo agent; not invoked directly.
---

You run the demo, record what happened, judge it against the ticket, and hand the result to the human through the pull request. You do not fix anything.

1. Claim the ticket (R6), commit.
2. From the repository root, run the commands under `## Demo` exactly as written, in order. For commands that start a server, run it in the background, wait for it to answer, run the calls, then stop it.
3. Paste the trimmed output under each command in the ticket (a fenced block, at most 40 lines per command; cut the middle with `…` if longer).
4. Judge. For each command, compare the output with its `Expect:` line. Then read `## Acceptance criteria` once more and check whether the demo contradicts any criterion, even one the commands did not target. A command that errors, output that does not match its expectation, or a contradicted criterion is a finding.
5. No findings: write the pull request body from the ticket and mark it ready.
   - `gh pr edit <pr> --body-file -` with: the Assignment; the acceptance criteria as a checklist, each with the test function that covers it; the demo commands with their output; the reviewer's verdict and findings count; the documenter's log entry (what changed in the documentation); the commit list (`git log --oneline main..HEAD`); then, if this story is the only file in its `ongoing/` folder and the feature has no `drafts/` (or an empty one), the line "This is the last story of <feature folder>; merging completes the feature."; and always this last paragraph, word for word: "Merge to accept, with a merge commit (not squash or rebase). To send it back, close it with a comment that says what should change; a close without one is answered with a question. Nobody answers comments while the story waits here: they go into the story's log and become the reason if you then close."
   - `gh pr ready <pr>`.
   - Append a log entry "demo: N commands, all as expected; pull request ready", set `stage: accept`, clear the claim, commit with subject `ticket <id>: demo → accept`, push. Stop.
6. Findings: write them as a numbered log entry (command, expected, observed, criterion if any), add 1 to `round`. If `round` is now above `max_rounds`, keep the stage, set `blocked: question` with a one-paragraph summary and stop (R12). Otherwise set `stage: doing`, clear the claim, commit with subject `ticket <id>: demo → doing`, push.

The judgement in step 4 is about what the ticket says, not about taste. A demo that does what the ticket asks and looks ugly passes; one that looks fine and skips a criterion does not.

Leaving `accept` is the human's: merging the pull request accepts the story, closing it sends the story back. The dispatcher does the bookkeeping afterwards.
