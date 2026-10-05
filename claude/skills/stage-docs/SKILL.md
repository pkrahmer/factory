---
name: stage-docs
description: Stage instructions for `docs`. Preloaded into the documenter agent; not invoked directly.
---

1. Claim the ticket (R6), commit.
2. Read the story, the diff and the documentation as the role skill describes. Nothing else: not other tickets, not `FEATURE.md`, not `factory/`, not `.claude/`. If `round` is greater than 0, the log's last findings name what to redo; do exactly that.
3. Write the documentation the docs criterion asks for, and fix what the cross-read found stale. If the criterion says `none`, write nothing new; the cross-read is still your job. Run every example you wrote or changed.
4. Run `make check`; it must stay green (a documentation file can be part of a check, and an example in a doctest is code the check runs).
5. Append a log entry: which files you changed and why in one line each, which documents you cross-read and found current, and anything stale you saw but did not touch because it is unrelated to this story.
6. No findings: set `stage: demo`, clear the claim, commit documentation and ticket together with subject `ticket <id>: docs → demo`, push.
7. Findings (the code contradicts the Interface or the criteria, a public interface without the docstring `CLAUDE.md` asks for): write them as a numbered log entry (location, what is wrong, what would fix it), add 1 to `round`. If `round` is now above `max_rounds` for this stage, keep the stage, set `blocked: question` with a one-paragraph summary and stop (R12). Otherwise set `stage: doing`, clear the claim, commit with subject `ticket <id>: docs → doing`, push. Documentation you already wrote stays committed; the coder's fix comes back through review and then to you.

You do not edit code, tests or comments in code. The human reads the documentation in the pull request; write for them.
