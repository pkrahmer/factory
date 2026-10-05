---
name: stage-review
description: Stage instructions for `review`. Preloaded into the reviewer agent; not invoked directly.
---

1. Claim the ticket (R6): commit with subject `ticket <id>: claim for review`, do not push.
2. Review `git diff main...HEAD -- . ':!factory'` as the role skill describes; the ticket is the only other input. Run `make check` yourself; do not rely on the log.
3. Write the findings and verdict as a log entry.
4. `verdict: pass`: set `stage: docs`.
   `verdict: rework`: add 1 to `round`. If `round` is now above `max_rounds` for this stage, keep the stage, set `blocked: question` with a one-paragraph summary of what keeps failing and stop (R12). Otherwise set `stage: doing`.
5. Clear the claim, then `git add -A && git commit --amend -m "ticket <id>: review → <stage>" && git push`. The amend folds the claim commit into this one and replaces its message.

You do not edit code, and you do not write any: no scratch copies, no seeded defects, no experiments. Judging the tests means reading them against the criteria and running `make check`. If the fix is a one-character change, it is still the coder's.

## Answer mode

A task message that starts with `Answer mode.` is not a review. The story waits at `accept`, the human asked about it on the pull request, and you answer: you know the diff and have judged it, without the author's urge to defend it. No claim, no stage change, no verdict, no `round`.

1. Read the story, `git diff main...HEAD -- . ':!factory'` and the comments the task lists. Nothing else.
2. Answer each listed comment where it was asked: factual, two to five sentences, from the diff, the story and its log, starting with `factory: ` so the pipeline knows its own post.
   - A comment on the diff: `gh api repos/{owner}/{repo}/pulls/<pr>/comments/<id>/replies -f body="factory: …"`.
   - A pull request comment or a review's text: `gh pr comment <pr> --body "factory: …"`, opening with the first words of the question in quotes, so the human sees what it answers.
   Change nothing and promise nothing. If the honest answer is that something should change, say so, and say that closing the pull request with a comment sends it to the coder.
3. Append one log entry `reviewer (answers): <n> comments answered`, with one indented line per answer: where, and its first sentence. Commit the story file alone with subject `ticket <id>: answers on the pull request`, push, stop.
