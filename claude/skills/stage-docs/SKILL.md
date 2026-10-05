---
name: stage-docs
description: Stage instructions for `docs`. Preloaded into the documenter agent; not invoked directly.
---

1. Read the story, the diff and the documentation as the role skill describes, all in your first turn (one command, or parallel reads). Nothing else: not other tickets, not `FEATURE.md`, not `factory/`, not `.claude/`. If the task's round is greater than 0, the latest findings name what to redo; do exactly that.
2. Write the documentation the docs criterion asks for, and fix what the cross-read found stale. If the criterion says `none`, write nothing new; the cross-read is still your job. Run every example you wrote or changed.
3. Run `make check` in the same command as your last edit; it must stay green (a documentation file can be part of a check, and an example in a doctest is code the check runs). The factory runs it again after you.
4. Your entry: which files you changed and why in one line each, which documents you cross-read and found current, and anything stale you saw but did not touch because it is unrelated to this story.
5. No findings: end with `demo`.
6. Findings (the code contradicts the Interface or the criteria, a public interface without the docstring `CLAUDE.md` asks for): add them to your entry as a numbered list (location, what is wrong, what would fix it) and end with `doing`. Documentation you already wrote stays; the coder's fix comes back through review and then to you.

You do not edit code, tests or comments in code. The human reads the documentation in the pull request; write for them.
