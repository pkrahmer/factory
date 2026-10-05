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
  - Request changes in a review, with comments on the lines that should change, to send it back to the coder. The coder addresses exactly those and replies to each.
  - A plain comment, on a line or in the conversation, is a question. The reviewer answers it and changes nothing.
  - Or close it with a comment saying what should change, which also sends it back to the coder.
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
gh pr review <n> --repo <owner>/<repo> --request-changes --body "…"  # send back; line comments go through the web or gh api
gh pr merge <n> --repo <owner>/<repo> --merge        # accept; the dispatcher archives the story
gh pr close <n> --repo <owner>/<repo>                # at accept: send back (say why first); elsewhere: discard
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

After every archived story, check its commits. Only intake and the coder leave a claim commit behind (R6): a story has eight commits plus the coder's work commits, so nine with one `feat` commit, and more only where the dispatcher merged `main` in or a stage asked, stalled or went back. Run `gh api repos/<owner>/<repo>/pulls/<n>/commits --jq '.[].commit.message' | grep 'claim for'`. It must list `claim for intake` and one `claim for doing` per coder run, nothing else. And every stage change from `ready → tests` to `demo → accept` must be there, in order.

To walk the paths a clean run never takes, write stories with one deliberate defect each, marked `<!-- carries path N -->`:

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
13. A restart (`docker compose restart`) while the reviewer holds its claim. The claim exists only in the container's checkout, and the tick must still find it and expire it at once.
14. A review requesting changes, with two comments on lines: one the coder fixes, one it keeps with a reason. Both get the coder's reply, the reviewer checks the replies, and you resolve the threads by hand. The pipeline never resolves one.
15. A plain comment on a line at the gate, asking why. The reviewer answers it in its thread, and the story stays at `accept`.
16. A comment on a line while the tester works. The coder gets it as *Notes from the human*, and the log has it before the coder's claim.
