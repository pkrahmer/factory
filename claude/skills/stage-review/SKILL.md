---
name: stage-review
description: Stage instructions for `review`. Preloaded into the reviewer agent; not invoked directly.
---

1. Review `git diff main...HEAD -- . ':!factory'` as the role skill describes; the ticket is the only other input. The factory ran `make check` after the coder and logged its result in the coder's entry; run it yourself when you need more than that line.
2. Your entry is the findings as a numbered list (location, what is wrong, what would fix it, one line each), or "no findings".
3. No findings: end with `docs`. Findings: end with `doing`. The factory counts the round and asks the human when the cap is passed.

You do not edit code, and you do not write any: no scratch copies, no seeded defects, no experiments. Judging the tests means reading them against the criteria and the factory's `make check`. If the fix is a one-character change, it is still the coder's.
