---
name: stage-review
description: Stage instructions for `review`. Preloaded into the reviewer agent; not invoked directly.
---

1. Claim the ticket (R6), commit.
2. Review `git diff main...HEAD -- . ':!factory'` as the role skill describes; the ticket is the only other input. Run `make check` yourself; do not rely on the log.
3. Write the findings and verdict as a log entry.
4. `verdict: pass`: set `stage: docs`.
   `verdict: rework`: add 1 to `round`. If `round` is now above `max_rounds` for this stage, keep the stage, set `blocked: question` with a one-paragraph summary of what keeps failing and stop (R12). Otherwise set `stage: doing`.
5. Clear the claim, commit with subject `ticket <id>: review → <stage>`, push.

You do not edit code, and you do not write any: no scratch copies, no seeded defects, no experiments. Judging the tests means reading them against the criteria and running `make check`. If the fix is a one-character change, it is still the coder's.
