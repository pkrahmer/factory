# Demo: the factory builds a to-do service

You give one prompt to Claude Code and watch the factory build a working FastAPI to-do service in an empty GitHub repository: eight stories in three features, each through tests, code, review, documentation and demo, each accepted by a merged pull request. The Claude Code session plays the human. It sets the repository up, puts the stories in one at a time, answers the pipeline's questions on the pull requests, and merges. It writes no product code; the factory's agents do that, in the container.

A clean run takes about an hour and a half and roughly 15 USD of API usage (see *What a run looks like*).

## What is in this folder

- `project/`: the empty project the factory builds into. Its `CLAUDE.md` (architecture, tests, docs), `Makefile` (`check`, `lint`, `test`), `pyproject.toml` with its lock file, and a README for the service's readers.
- `features/`: the three features with their stories, ready to promote.
  - `F0001-todo-service`: domain model, service layer, HTTP API, SQLite storage.
  - `F0002-operations`: health endpoint, version command, statistics.
  - `F0003-search`: title search.

  Each `FEATURE.md` already lists the product decisions behind its stories.

## Before you start

You need:

- Docker with Compose, `git`, `uv`, and Claude Code on your machine.
- The GitHub CLI `gh`, logged in with `repo` scope (`gh auth login`, or `gh auth refresh -s repo`). The session merges, closes and comments with it.
- A GitHub token for the container: fine-grained, limited to the target repository, with Contents and Pull requests read and write (see `docs/github-settings.md`).
- A Claude login for the container. The agents run there as Claude Code.

Then, from your checkout of the factory:

1. Create an empty repository for the demo and clone it beside the factory:

   ```bash
   gh repo create <owner>/<repo> --private
   git clone https://github.com/<owner>/<repo> ../<repo>
   ```

2. In its settings, allow merge commits only (`docs/github-settings.md`). A squash merge confuses the watcher (`docs/branching.md`).
3. Configure the container: `cp .env.example .env`, then set `REPOS=<owner>/<repo>` and `GH_TOKEN`.
4. Build the image and log Claude in once: `docker compose build`, then `docker compose run --rm -it --entrypoint claude factory`, complete the login, `/exit`.
5. Check: `bash scripts/demo-check.sh <owner>/<repo>`. Every line must say `ok`; a `note` is for your information.
6. Start the factory: `docker compose up -d`.

## The prompt

Start Claude Code in your factory checkout and give it this, with your repository's name:

> Read `demo/README.md` and run the demo against `<owner>/<repo>`; its checkout is `../<repo>`. You are the human in the loop: set the repository up, put the stories in, promote one at a time, answer the pipeline on the pull requests, merge or close. Never write product code. Stop and report when the demo says to.

Then watch: `docker compose logs -f` for the tick, the pull requests on GitHub for the work, and the board with `docker compose exec factory sh -c 'cd /work/<repo> && factory-watch --board'`.

## For the session: how to run the demo

You are the human in the loop, not a stage. Work in the target's checkout (`../<repo>`), commit with the machine's git identity, push after every step.

### Set up

1. Copy everything in `demo/project/` into the target's root, `.gitignore` included.
2. Copy `template/stages.yml`, `template/TICKET.md` and `template/FEATURE.md` into the target's `factory/` folder.
3. Run `make check` in the target. It must be green before the first story.
4. Commit `Set up the repository for the factory` and push.

### Put the stories in, one at a time

1. Copy a feature from `demo/features/` into `factory/features/`, its `FEATURE.md` and its `drafts/`. Commit `F0001: draft S0001 to S0004` and push.
2. Promote the lowest story: `mkdir -p factory/features/<feature>/ongoing && git mv factory/features/<feature>/drafts/<story>.md factory/features/<feature>/ongoing/`. Commit `F0001: start S0001` and push.
3. Wait until the story's pull request is merged and the dispatcher has archived the story (it shows up in `done/` on `main`). Pull, then promote the next one.
4. When a feature's last story is archived, the factory runs that feature's acceptance (`docs/diagrams/05-feature-acceptance.svg`). Read the report on its pull request.
   - Merge it if the verdict is fair. Its proposed drafts land in `drafts/`. They are yours to refine; this demo does not promote them.
   - Otherwise close it with a comment saying why.
5. Then copy in the next feature. A story takes about ten minutes when nothing asks.

### Answer and decide

- **The pipeline asks** on a pull request: answer with a comment, as a sensible single-user to-do service would. The dispatcher copies the answer into the story, and the stage runs again. Add every product decision you take to the feature's `FEATURE.md` under *Decisions taken for the human*.
- **A pull request is ready** (stage `accept`): read it.
  - Merge with a merge commit (`gh pr merge <n> --merge`) when the story does what it says.
  - A comment, on a line or in the conversation, is a question. The reviewer answers it on the pull request and changes nothing.
  - Close it with a comment saying what should change to send it back to the coder. Your comments on lines since the hand-over count as part of the reason, and the coder replies to each. "Request changes" is not available: the factory opens the pull requests under your own account.
- **Never** edit the target's `src/`, `tests/`, `README.md` or `docs/`: they belong to the stages. Never touch `.claude/` in the target, never put the token into a commit, never rewrite pushed history, never run a stage's commands by hand to help a stuck story.

### Stop and report

Stop when one of these happens:

- the pipeline has spent more than 40 USD on the target: the cost lines in the archived stories plus the open story's cost table on its pull request;
- you have been running for four hours;
- a stage stalls in a way that looks like a defect of the factory, not of a story: the same stall twice, a stage that cannot finish, the watcher repeating a line;
- a pull request would merge something you believe is wrong although every stage passed it.

Stopping means: leave the pull request as it is, and write a summary as your last message. Cover what was built, what the pipeline asked and what you answered, every product decision, what went wrong with the tick log lines that show it, and what is open.

### Watch and act

```bash
docker compose logs -f --since 5m                    # the tick: "dispatch:" and "done:" lines
gh pr list --repo <owner>/<repo>                     # what is open, and whether it is ready
gh pr view <n> --repo <owner>/<repo> --comments      # a question, the cost table
gh pr comment <n> --repo <owner>/<repo> --body "…"   # an answer; the dispatcher copies it into the story
gh pr merge <n> --repo <owner>/<repo> --merge        # accept; the dispatcher archives the story
gh pr close <n> --repo <owner>/<repo> --comment "…"  # at accept: send back with the reason; elsewhere: discard
```

A comment on a line of the diff goes through the API (`gh pr comment` writes only to the conversation):

```bash
head=$(gh pr view <n> --repo <owner>/<repo> --json headRefOid --jq .headRefOid)
gh api repos/<owner>/<repo>/pulls/<n>/comments -f body="…" -f commit_id="$head" -f path=<file> -F line=<line> -f side=RIGHT
```

Several at once, as one review whose text says what they are about:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews --input - <<'EOF'
{"event": "COMMENT", "body": "…",
 "comments": [{"path": "<file>", "line": <line>, "side": "RIGHT", "body": "…"},
              {"path": "<file>", "line": <line>, "side": "RIGHT", "body": "…"}]}
EOF
```

The container keeps its own checkout in the `work` volume; do not edit there.

## What a run looks like

From the factory's own runs on these stories:

| Run | Stories | Dispatcher time | Wall clock | Cost | Notes |
| :- | -: | -: | -: | -: | :- |
| clean run | 8, all merged | 50.5 min in 48 runs, 6 per story | 87 min | 14.09 USD | every stage passed first time; no question, no rework |
| first run | 8 merged, 10 pull requests | 62.1 min in 69 runs | 2 h, with factory fixes between stories | 17.97 USD | two deliberate questions from intake, one review rework, two discards on purpose |
| feature acceptances | 3 reports | 17.7 min in 3 runs | 26 min | 4.66 USD | one acceptor run per feature |

A story costs about 1.50 to 2.20 USD and five to eight minutes of dispatcher time. The cost table on each pull request shows the running total.

## Another run on the same target

A run's history and pull requests stay; the next run starts from a commit that removes everything:

```bash
git -C ../<repo> tag run-<n> && git -C ../<repo> push origin run-<n>                  # where the run ended
git -C ../<repo> rm -r -q . && git -C ../<repo> commit -m "Clean the repository for run <n+1>" && git -C ../<repo> push
docker compose down && docker volume rm factory_work     # the checkout and its cost records; the login stays
bash scripts/demo-check.sh <owner>/<repo>                # "repo … empty" and "work volume fresh" must be ok
```

## Hardening mode, for the factory's maintainers

The same demo, with one rule changed: **every defect is a factory defect until proven otherwise.** When a stage stalls, asks something it should have known, misreads a criterion or skips a rule, the session does not stop. It finds the cause in the skills, the rules, the engine or the template and fixes it there. Then it runs `make check` in the factory, commits, pushes, rebuilds (`docker compose build && docker compose up -d`) and lets the story continue. A lasting decision goes into `docs/decisions.md`.

It stops and asks the maintainer when a fix would change the model rather than a detail: a new stage, a new rule, a change to what the human does, or a change to `docs/WATCH_CONTRACT.md`.

After every archived story, check its commits (R6). Only intake and the coder leave a claim commit behind. A story has eight commits plus the coder's work commits, so nine with one `feat` commit. It has more only where the dispatcher merged `main` in or copied notes, or a stage asked, stalled or went back.
- `gh api repos/<owner>/<repo>/pulls/<n>/commits --paginate --jq '.[].commit.message' | grep 'claim for'` lists `claim for intake` and one `claim for doing` per coder run, nothing else. That holds for stories that asked a question as well.
- Every stage change from `ready → tests` to `demo → accept` is there, in order.
- A feature acceptance's pull request has `acceptance <feature>: claim` and `feature → accept`.

To walk the paths a clean run never takes: paths 1 to 7 need stories with one deliberate defect each, marked `<!-- carries path N -->`. Paths 8 to 16 are things you do, on stories that otherwise run clean. After each path, check what it lists; a check that fails is a factory defect.

1. Intake asks: a behaviour without a criterion; a Demo without `Expect:`.
2. Intake asks about a failing side: a limit with no rejecting criterion.
3. The tester finds a criterion that contradicts the Interface. The answer needs a test change, so `doing → tests → doing` runs.
4. A review rework: an Interface that invites an architecture violation.
5. A documenter finding: an Interface and a Demo that cannot both be right.
6. A demo finding: an `Expect:` the correct implementation cannot meet.
7. The round cap at review or demo.
8. The attempts cap: a stage made to stall twice; the retry question; `attempts: 0` after the answer.
9. `reject`: an illegal stage change committed by hand on a ticket branch.
10. Two stories in `ongoing/` at once; WIP 1 holds.
11. A close at `accept` with a comment asking for a change.
12. Feature acceptance: one report refused, one merged with drafts that are then refined and promoted.
13. **A restart while a claim is local.** Run `docker compose restart` as soon as the tick log shows `dispatch: run reviewer …`. The reviewer's claim exists only in the container's checkout.
    Check:
    - The next tick says `expired`, not `busy`.
    - The story's log has "claim expired …" and `attempts: 1`.
    - The reviewer runs again and the story goes on.
14. **Sending a story back with comments on lines.** At `accept`, write two comments on lines as one review (*Watch and act*), and close the pull request with a comment right after, before the next tick. One comment asks for a change the story allows; the other asks for one its criteria rule out.
    Check:
    - The dispatcher reopens the pull request as a draft and copies both comments into the log as `human (review comment <id>, <path>:<line>)`, each with its line quoted.
    - The coder fixes the first and keeps the second. It replies in each thread with `factory: fixed in <sha>: …` or `factory: kept: <reason>`, and its log entry names the reply ids.
    - The reviewer's entry confirms the replies.
    - No reply comes back into the log as yours.
    - The threads stay open until you resolve them.
15. **A question at the gate.** At `accept`, write a comment on a line asking why something is done the way it is, and one question in the conversation.
    Check:
    - Within one or two ticks, the reviewer answers the line comment in its thread, and the conversation question with a comment that quotes it. Both answers start with `factory:`.
    - The log has `reviewer (answers): 2 comments answered`.
    - The story stays at `accept`, the pull request stays ready, and no stage change was committed.
    - The tick does not dispatch again for the reviewer's own answers.
16. **Notes while the stages work.** While the tester runs, write two comments on lines of the diff: one settles a detail the story leaves open, the other contradicts the story.
    Check:
    - Before the coder starts, the log has both as `human (review comment <id> before doing, …)`, in a commit `notes from the human`.
    - The coder follows the first, and its log entry says so.
    - The second makes the coder ask (R8) instead of following it.
