---
name: stage-demo
description: Stage instructions for `demo`. Preloaded into the demo agent; not invoked directly.
---

You run the demo, record what happened, judge it against the ticket, and hand the result to the human through the pull request. You do not fix anything.

1. Claim the ticket (R6): commit with subject `ticket <id>: claim for demo`, do not push.
2. From the repository root, run the commands under `## Demo` exactly as written, in order. For commands that start a server, run it in the background, wait for it to answer, run the calls, then stop it.
3. Paste the trimmed output under each command in the ticket (a fenced block, at most 40 lines per command; cut the middle with `…` if longer).
4. Judge. For each command, compare the output with its `Expect:` line. Then read `## Acceptance criteria` once more and check whether the demo contradicts any criterion, even one the commands did not target. A command that errors, output that does not match its expectation, or a contradicted criterion is a finding.
5. No findings: write the pull request body from the ticket and mark it ready.
   - `gh pr edit <pr> --body-file -` with: the Assignment; the acceptance criteria as a checklist, each with the test function that covers it; the demo commands with their output; the reviewer's verdict and findings count; the documenter's log entry (what changed in the documentation); the commit list (`git log --oneline main..HEAD~1`: everything but your own claim commit, which your closing commit replaces); then, if this story is the only file in its `ongoing/` folder and the feature has no `drafts/` (or an empty one), the line "This is the last story of <feature folder>; merging completes the feature."; and always this last paragraph, word for word: "Merge to accept. Request changes with comments on the lines that should change, and the coder will address exactly those and reply to each; a plain comment is answered by the reviewer without changing anything. Close with a comment to send the story back without line references; a close without a comment is answered with a question."
   - `gh pr ready <pr>`.
   - Append a log entry "demo: N commands, all as expected; pull request ready", set `stage: accept`, clear the claim, then `git add -A && git commit --amend -m "ticket <id>: demo → accept" && git push`. The amend folds the claim commit into this one and replaces its message. Stop.
6. Findings: write them as a numbered log entry (command, expected, observed, criterion if any), add 1 to `round`. If `round` is now above `max_rounds`, keep the stage, set `blocked: question` with a one-paragraph summary and stop (R12). Otherwise set `stage: doing`, clear the claim, then `git add -A && git commit --amend -m "ticket <id>: demo → doing" && git push`.

The judgement in step 4 is about what the ticket says, not about taste. A demo that does what the ticket asks and looks ugly passes; one that looks fine and skips a criterion does not.

Leaving `accept` is the human's: merging the pull request accepts the story, closing it sends the story back. The dispatcher does the bookkeeping afterwards.
