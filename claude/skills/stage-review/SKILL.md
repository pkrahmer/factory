---
name: stage-review
description: Stage instructions for `review`. Preloaded into the reviewer agent; not invoked directly.
---

1. Review `git diff main...HEAD -- . ':!factory'` as the role skill describes; the ticket is the only other input. Read both in your first command: the ticket, the diff's `--stat`, and the diff without the generated files `CLAUDE.md` names and lock files (add `':!<path>'` for each; the stat still lists them). Do not read the Makefile, `pyproject.toml` or tool configuration unless the diff changes them; `CLAUDE.md` says what the checks enforce. Do not run `make check`: the factory ran it after the coder, the coder's entry carries the result, and the factory runs it again after you.
2. Your entry is the findings as a numbered list (location, what is wrong, what would fix it, one line each), or "no findings".
3. No findings: end with `docs`. Findings: end with `doing`. The factory counts the round and asks the human when the cap is passed.

You do not edit code, and you do not write any: no scratch copies, no seeded defects, no experiments. Judging the tests means reading them against the criteria and the factory's `make check`. If the fix is a one-character change, it is still the coder's.
