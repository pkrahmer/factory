# watch.py contract (version 5)

`factory-watch` (`src/factory/watch.py`) is the deterministic router. Everything else in the pipeline is written against this contract, so changing the contract means changing `version` in `stages.yml`.

## Model

- Features are folders under `root` (`factory/features` by default): `<F0001-slug>/` with a `FEATURE.md` and up to three subfolders, `drafts/`, `ongoing/`, `done/`. A story is a file `<F0001-S0003-slug>.md` in exactly one of them; its id is the stem without the slug, the feature's id is the first part. The watcher reads only `*/ongoing/*.md`. Promotion (`drafts/` → `ongoing/`) is the human's `git mv`; archiving (`ongoing/` → `done/`) is the dispatcher's, in the commit that sets `stage: done`. Neither is a stage change: a file that moved has no stage before.
- The stage is the frontmatter field `stage`. Missing frontmatter means `ready`: a story freshly promoted from `drafts/` needs none. The frontmatter holds seven fields, `stage`, `pr`, `blocked`, `comments_seen`, `claimed_at`, `round`, `attempts`; the watcher reads `stage`, `pr`, `blocked`, `claimed_at`, `attempts`.
- Every story past `ready` lives on the branch `ticket/<file stem>`. The watcher reads a story from the tip of that branch when the branch exists (local first, then `origin/`), otherwise from `origin/main` when that ref exists (the checkout may sit on a ticket branch while a new story lands on main; the tick fetches before it evaluates), otherwise from the working tree. The claim is a local commit: while a stage runs, the branch on `origin` lags the local branch by that stage's claim, and reading local first is what shows it. A branch that is already an ancestor of main counts as absent: it was merged, and the copy on `main` is the newer one, however long its ref lingers.
- A pull request number in `pr` ties the story to its GitHub pull request; `gh pr view` answers for it.
- Everything written on a pull request counts as one number: its comments, the comments on lines of the diff, and the text of every submitted review. `comments_seen` is how many of them the pipeline has read; the pipeline's own posts start with `factory:`. The reviews submitted since the story last reached the gate give a verdict. That point is the commit time of the last `… → accept` on the branch's first-parent line; reviews from before it belong to an earlier round. A change request stands until an approval; otherwise the newest review counts.
- A stage with `gate` in `stages.yml` has no agent: the human leaves it by merging or closing the pull request, or by requesting changes in a review.
- A feature's acceptance is a ticket of its own: `<feature>/ACCEPTANCE.md`, id the feature folder, branch `acceptance/<folder>`, frontmatter the seven fields plus `stories` (the archived story ids it covers). It is due when the feature has stories under `done/`, none under `ongoing/` or `drafts/`, and no report whose `stories` equals the archived set; then the watcher lists it with stage `feature` even though the file does not exist yet, and `run acceptor <path> main` follows. While `acceptance/<folder>` exists the report is read from that branch; a report at `done` that covers the archived set silences the acceptance until another story is archived; its `outcome` (`accepted` when the human merged, `refused` when the human closed) is the feature's status. `--board` shows it per feature as `-` (incomplete), `due`, `running`, `accepted` or `refused`.

## Invocation

```
factory-watch --once      # evaluate, print one line, exit 0
factory-watch --follow    # block; print a line each time the evaluation changes
factory-watch --board     # print the board, exit 0
```

`--once` is what the scheduled tick (`factory-tick`) uses: it evaluates once and decides whether the line needs the dispatcher. `--follow` polls every 2 seconds for a human watching a terminal: a change is detected when `HEAD`, `git status --porcelain <root>` or any `ticket/*` ref differs from the last poll; pull request state is re-read every 15 polls. `--board` prints one row per feature (drafts, ongoing, done counts from the working tree) and one row per ongoing story.

## Inputs

- `factory/stages.yml`
- Frontmatter of every `<root>/*/ongoing/*.md`, from the branch tip, `origin/main` or the working tree as above
- `git for-each-ref` over `refs/heads/ticket/`, `refs/remotes/origin/ticket/`, `refs/heads/acceptance/` and `refs/remotes/origin/acceptance/`
- Every file under `<root>/<feature>/` (to tell drafts, ongoing and done apart for the acceptance rule)
- For stage checks: the files in `git diff --name-only HEAD~1 HEAD -- <root>`, with their `stage` at `HEAD~1` and `HEAD`
- For stories with a `pr` that wait for the human (in a gate stage, or with a question posted on the pull request, `blocked: asked`): `gh pr view <pr> --json state,comments`, `gh api repos/{owner}/{repo}/pulls/<pr>/comments` and `gh api repos/{owner}/{repo}/pulls/<pr>/reviews`, and the commit time of the last `… → accept` on the story's branch

## Output

Exactly one line per evaluation, first match wins:

| Line | Condition |
| :- | :- |
| `reject <path> <from> <to>` | The last commit changed a story's stage to one not listed under `<from>.next`. Exempt: a merge commit (it brings stage changes that were legal where they happened), and a commit whose subject contains `moved back`, which is how the dispatcher corrects a rejected change |
| `duplicate <id> <path> <path>` | Two ongoing files carry the same id |
| `error pr-lookup <path>` | A story waiting for the human has a `pr` but `gh` could not answer |
| `merged <path> <branch>` | The story's pull request is merged |
| `closed <path> <branch>` | The story's pull request was closed without merging |
| `pr <path> OPEN <n> <review>` | The story waits for the human (gate stage or `blocked: asked`) and its pull request is open with `n` writings; `<review>` is the verdict of the reviews since the hand-over: `NONE`, `COMMENTED`, `CHANGES_REQUESTED` or `APPROVED`. The tick starts the dispatcher when `n` exceeds `comments_seen`, and once for `CHANGES_REQUESTED` on a story at the gate |
| `ask <path>` | Any story with `blocked: question`, or in a gate stage without a `pr`, or with `attempts` at or above `max_attempts` |
| `busy <path>` | A story is claimed (`claimed_at` set) and the claim is younger than `lease_minutes` |
| `expired <path>` | A story is claimed and its lease is older than `lease_minutes` |
| `run <agent> <path> <where>` | Lowest id among unclaimed tickets in a stage with an agent; `<where>` is `main` for `ready` and `feature` (the agent creates the branch) and the ticket's branch otherwise |
| `idle` | Nothing above matched |

`busy` enforces WIP 1: while a lease is alive, no `run` is emitted for any other story. Id order is `F0001-S0001 < F0001-S0002 < F0001-todo-service < F0002-S0001`: feature by feature, story by story, then the feature's acceptance (its id is the folder name, which sorts after `F0001-S…`).

## What it must not do

- Read story bodies, call a model, change tracked files, check out branches, or commit. It only reads and prints. Its one piece of state is the last line `--follow` printed, kept in `.git/factory-last-line`, so a restarted watcher stays silent until something changes.
- Prioritise by anything other than id order.
- Fetch from the remote. Merges are learned from `gh`, and the tick fetches.
- Look into `drafts/` or `done/`, except to count them for the board.

## Implementation

Standard library plus PyYAML and the `gh` CLI for pull request state. `evaluate()` is a pure function of (config, tickets, last change, now, pr lookup), so routing is tested without git or GitHub; `tests/test_watch.py` covers it and the git-backed readers.
