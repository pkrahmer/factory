# Retargeting the book to the latest repository

The book describes v1 as of commit `537fc20` (the preface says so, and the print pins every link there). The final version is meant to describe the repository as it stands when it is published. This file lists everything that has to change then. It is not part of the book (`_print/book.py` does not pick it up).

**Keep it current.** Whenever a file the book names moves, a document it quotes changes, or a chapter pins something to `537fc20`, add a line here, in the same commit.

## 1. The pin itself

| Where | What |
| :- | :- |
| `_print/book.py` | `DESCRIBES = "537fc20"` and `REPO_URL` (…`/blob/537fc20`): the commit the footnote links and the edition page name |
| `README.md` (the preface) | *What "v1" means*: "The book describes it as of commit `537fc20`", and the sentence on files that have moved since |
| `WRITING-PLAN.md` | the status lines and the sources that name `537fc20` |

## 2. Links pinned to `537fc20` in the text

These link to a file at its old path at `537fc20`, because it has moved since. Find them with `grep -rn "blob/537fc20" docs/reference --include=README.md`.

| Chapter | Links to | Becomes |
| :- | :- | :- |
| 3, P1 (*In v1*) | `docs/deterministic-core.md` | `docs/archive/deterministic-core.md` |
| 3, P10 (*In v1*) | `docs/fewer-commits.md` | `docs/archive/fewer-commits.md` |
| 3, P10 (*In v1*) | `docs/review-comments.md` | `docs/backlog/review-comments.md` |
| 8, the first limit | `docs/deterministic-core.md` | `docs/archive/deterministic-core.md` |

## 3. Files that moved after `537fc20`

Every chapter that names one of these in prose or in a code span needs the new path. The table lists where each is named now; check again with `grep -rn "<old path>" docs/reference --include=*.md`.

| Old path | New path | Moved | Named in |
| :- | :- | :- | :- |
| `docs/deterministic-core.md` | `docs/archive/deterministic-core.md` | 2026-10-07 | ch. 3, 8; `WRITING-PLAN.md` |
| `docs/fewer-commits.md` | `docs/archive/fewer-commits.md` | 2026-10-07 | ch. 3 |
| `docs/backlog.md` | `docs/backlog/README.md` | 2026-10-07 | `WRITING-PLAN.md` (ch. 17 will) |
| `docs/review-comments.md` | `docs/backlog/review-comments.md` | 2026-10-07 | ch. 3, 10; `WRITING-PLAN.md` |
| `docs/mutants-in-story-loop.md` | `docs/backlog/mutants-in-story-loop.md` | 2026-10-07 | ch. 11; `WRITING-PLAN.md` |

`docs/decisions.md` names the old paths too; it is append-only, and the archive's and the backlog's `README.md` say where the files went.

## 4. Documents whose content changed after `537fc20`

The book states these as facts about v1 at `537fc20`. At the new commit they are no longer true:

| Chapter | Statement | Changed |
| :- | :- | :- |
| 10, the note on the reverted plan | "The plan's document still reads as if nothing had been built" | 2026-10-07: `docs/backlog/review-comments.md` opens with its state (built and reverted, to be replanned) |
| 17 (planned) and `WRITING-PLAN.md`, *Known facts*: stale documents | `docs/review-comments.md` reads as unbuilt | the same |
| 17 (planned) | the backlog's contents | 2026-10-07: the feature-acceptance entry removed (built); "Running the Demo blocks in code" added (part E of the archived plan); the bigger plans listed as files |
| B (planned) | the file map | `docs/archive/` and `docs/backlog/` exist; the repository's `README.md` names them |

## 5. What drifts with any code change

These are tied to the code at `537fc20` and must be verified against the code at the new commit, chapter by chapter, as a lecturer review for accuracy only:

- *File and line references:* 16 of them, all in chapter 5, *Names in the code* (`grep -rnE "[a-z_]+\.py:[0-9]+" docs/reference --include=README.md`).
- *Function, constant and key names* cited throughout Part II (`stage._decide`, `MAX_FAILURES`, `story.FIELDS`, …).
- *Quoted strings:* the fixed texts in chapters 7, 8 and 10 (`STORY_CLOSING`, `ACCEPTANCE_CLOSING`, `CAP_QUESTION`, `SENT_BACK_QUESTION`, `FINISH`, the task lines, the posts, the log prefixes), quoted character for character.
- *Tables of v1's configuration:* the stage table (ch. 5), the lanes (ch. 8), the agents (ch. 9), the permissions (ch. 9).
- *Every `v1 limit` box:* a limit fixed since goes, or becomes history in chapter 16; chapter 17's table follows.
- *Stale-document limits:* the `max_attempts` comment (ch. 5), the template's Demo text (ch. 4), `stage-review`'s claim about `make check` (ch. 9), R10's `docs/branching.md` (ch. 9).
- *Counts:* tests, design decisions, files (ch. 16, appendices B and C).
- *Run data:* the four runs are history and stay; a new run after `537fc20` adds a row to chapter 16, not a rewrite.
