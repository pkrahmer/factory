# Retargeting the book to the latest repository

The book describes v1 at one commit, its *pin*: the preface names it, and the print (`_print/book.py`, `DESCRIBES`) pins every link to a repository file there. This file says how to move the pin; it is not part of the book (`_print/book.py` does not pick it up).

**Retargeted on 2026-10-07** from `537fc20` to `930c61a`, the merge of Part IV into `main`. Between the two, the code changed only in the default commit address (`.env.example`, `compose.yml`, `entrypoint.sh`); the documents moved into `docs/archive/` and `docs/backlog/`, and the decision log gained the entries for the reverted plans and the address. Every chapter now names the new paths, chapter 3's P17 holds, and chapter 17's L6 is marked *Fixed*.

## Retargeting again

1. Set `DESCRIBES` in `_print/book.py` and the commit in the preface's *What "v1" means* to the newest commit on `main`.
2. `git diff --stat <old pin> <new pin> -- . ':!docs/reference'` shows what moved; every file the book names that moved or changed gets its new path or statement (`grep -rn "<old path>" docs/reference --include=*.md`).
3. Check the list below against that diff, chapter by chapter; where code changed, a lecturer review for accuracy only.
4. Whenever a file the book names moves, or a document it quotes changes, between two retargets, add a line here, in the same commit.

## What drifts with any code change

These are tied to the code at the pin and must be verified against the code at the new commit, chapter by chapter, as a lecturer review for accuracy only:

- *File and line references:* 16 of them, all in chapter 5, *Names in the code* (`grep -rnE "[a-z_]+\.py:[0-9]+" docs/reference --include=README.md`).
- *Function, constant and key names* cited throughout Part II (`stage._decide`, `MAX_FAILURES`, `story.FIELDS`, …).
- *Quoted strings:* the fixed texts in chapters 7, 8 and 10 (`STORY_CLOSING`, `ACCEPTANCE_CLOSING`, `CAP_QUESTION`, `SENT_BACK_QUESTION`, `FINISH`, the task lines, the posts, the log prefixes), quoted character for character.
- *Tables of v1's configuration:* the stage table (ch. 5), the lanes (ch. 8), the agents (ch. 9), the permissions (ch. 9).
- *Every `v1 limit` box:* a limit fixed since goes, or becomes history in chapter 16; chapter 17's table follows, keeping its numbers L1… stable (a fixed limit's row says so rather than disappearing, since plans cite the numbers).
- *Stale-document limits:* the `max_attempts` comment (ch. 5), the template's Demo text (ch. 4), `stage-review`'s claim about `make check` (ch. 9), R10's `docs/branching.md` (ch. 9).
- *Counts:* tests (183 in ten files, ch. 16's table), design decisions, files (appendices B and C).
- *Run data:* the four runs are history and stay; a new run adds a row to chapter 16, not a rewrite. It also updates what depends on which paths have run live on the current generation: chapter 16's paths table and its limit, chapter 17's L73, and chapter 3's P14 (*In v1*: "on generation 5 the restart is tested by unit tests only").
- *Part III's tables of v1's machine and settings:* the control surface, the template against the demonstration project and the protected paths (ch. 12); the branches, the commit table, the sync steps and the GitHub settings (ch. 13); the image, the compose variables, the entrypoint's steps, the tick's steps, the preflight's items, the state files and the log lines (ch. 14); the reach table (ch. 15).
- *Statements about Claude Code's behavior* in chapter 15 (auto mode drops broad run rules, the classifier allows pushes to any branch, protected paths, `settings.local.json` without a trust step): taken from Claude Code's documentation on 2026-10-07, not from v1's code; check them against the documentation and the version the image then installs.
- *Facts about the running container* (ch. 13, 14, 15): file ownership, the credential helper in `~/.gitconfig`, Claude Code 2.1.289 in the container built on 2026-10-05 at 20:59 UTC, and GitHub attributing `factory@users.noreply.github.com` to the organization `factory`; observed on 2026-10-07, not in the repository.
