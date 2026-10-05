# Fewer commits per story

**Withdrawn on 2026-10-05.** The claim left Git (`docs/deterministic-core.md`, part D): the dispatcher keeps it in `.git/factory-run.json`, so there are no claim commits left to fold away, and the dispatcher opens the pull request, so intake needs no exception. A story's branch now has the dispatcher's first commit, one commit per stage and the coder's work commits. The plan below is kept as it was written.

The plan for taking the claim commits out of a story's history. Nothing here is done yet: it runs on this repository before the next end-to-end run, which verifies it. One pull request, one rebuild of the image.

## What a story's branch looks like today

Pull request #18 of the demo repository (title search, run 2), thirteen commits:

```
ticket F0003-S0001: claim for intake
ticket F0003-S0001: ready → tests
ticket F0003-S0001: claim for tests
ticket F0003-S0001: tests → doing
ticket F0003-S0001: claim for doing
ticket F0003-S0001: feat(service,api): filter todos by title search
ticket F0003-S0001: doing → review
ticket F0003-S0001: claim for review
ticket F0003-S0001: review → docs
ticket F0003-S0001: claim for docs
ticket F0003-S0001: docs → demo
ticket F0003-S0001: claim for demo
ticket F0003-S0001: demo → accept
```

Three kinds. The **stage changes** (six) are the transitions log: version 4 dropped the ticket's `## Transitions` section because the commit subject names the change and git has the time, and the watcher's `reject` check reads exactly one stage change out of `HEAD~1..HEAD`. They stay. The **work commits** (here one) are the point. The **claim commits** (six) carry nothing but `claimed_at`, which the stage's last commit clears again: in the final diff of the branch they do not exist. They go.

## Why the claim is committed at all, and what it does not need

The claim is the lease. The watcher reads it from the branch tip (`git show <branch>:<path>`), reports `busy` while it is younger than `lease_minutes`, and `expired` after; a container restart finds it in the work volume and the tick turns it into `expired` (restart recovery, run 1 fix 6). All of that needs the claim **committed on the branch**. None of it needs the claim **pushed**: the watcher, the tick and the agents share one checkout, and nobody else reads the branch while a stage runs — the human sees the pull request, not the commits.

So the claim becomes a local commit, and the stage's closing commit amends it. Amending an unpushed commit rewrites nothing anyone has.

## The rule

R6 becomes:

> Claim before work: set `claimed_at` (from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from memory) in the frontmatter and commit **without pushing**, then start. The stage's closing commit — the one that changes the stage and clears the claim — is made with `git commit --amend`, so the claim commit and the closing commit are one; then push. Work commits in between (the coder's `feat` and `refactor` commits) are ordinary commits on top of the claim commit, and the closing commit amends the claim only when no work commit sits between them; otherwise it is a normal commit and the claim commit stays, which is harmless. A claim older than the lease in `stages.yml` is considered dead.

In plain terms per stage:

| Stage | Commits after the change |
| :- | :- |
| intake | two: `claim for intake` and `ready → tests` (the exception, see below) |
| tests | one: `tests → doing` with the tests |
| doing | work commits plus `doing → review`; the claim commit stays underneath them (amending across work commits would rewrite the work) |
| review | one: `review → docs` or `review → doing` with the findings |
| docs | one: `docs → demo` with the documentation |
| demo | one: `demo → accept` with the outputs |
| feature (acceptor) | one: `feature → accept` with the report and the drafts |

Nine commits for the pull request above instead of thirteen.

## The intake exception

Intake must push before the pull request exists: `gh pr create` needs the branch on GitHub with at least one commit that differs from `main`, and today that commit is the claim. Amending it afterwards would make intake's final push a force push, which the deny list forbids (`git push --force*`) and which this plan does not want to open for one commit per story. So intake keeps its two commits: `claim for intake` (pushed, carries the branch and the pull request) and `ready → tests`. Every other stage ends with one closing commit that absorbed its claim.

For pull request #18 that means nine commits instead of thirteen: intake's two, one each for tests, review, docs, demo, the coder's claim (kept, because a work commit sits on top of it), the coder's work commit and `doing → review`.

## Changes, file by file

All in this repository:

1. `claude/skills/factory-rules/SKILL.md` — R6 as above.
2. `claude/skills/stage-tests/SKILL.md`, `stage-review`, `stage-docs`, `stage-demo`, `stage-feature`: step 1 "Claim the ticket (R6), commit" becomes "Claim the ticket (R6): commit, do not push"; the closing step becomes `git add -A && git commit --amend -m "ticket <id>: <from> → <to>" && git push`. The amend folds the claim commit into the closing commit and replaces its message. Each skill names the exact command, so no agent has to work it out.
3. `claude/skills/stage-doing/SKILL.md`: step 1 as above; the closing step stays a normal commit (work commits in between); the skill says why.
4. `claude/skills/stage-intake/SKILL.md`: unchanged in substance (push before the pull request); one sentence saying that intake is the exception and why.
5. `claude/skills/factory/SKILL.md`, the stall handling: "when it returns and `HEAD` has not moved" — with a local claim commit, `HEAD` has moved by one commit even when the agent did nothing after claiming. The dispatcher records `HEAD` after the agent's claim? It cannot; it records before. Change the test to: the stage stalled when the branch tip's frontmatter still carries `claimed_at` (the agent did not reach its closing commit), or the agent ended with an error. The watcher's `expired` path already covers the lease; this is the dispatcher's immediate judgement.
6. `src/factory/tick.py`, `recover_dirty_tree`: unchanged — leftovers go on top of whatever is committed, claim included, and are pushed; a stale claim then reaches GitHub, which is harmless.
7. `src/factory/watch.py`: unchanged. The watcher reads the local branch first (`refs/heads/ticket/…` before `refs/remotes/origin/…`), so the unpushed claim is what it sees. Confirm with a test: a claim committed locally and not pushed yields `busy`.
8. `docs/WATCH_CONTRACT.md`: one sentence under *Model*: the claim is a local commit; the branch on `origin` lags the local branch by the running stage's claim.
9. `docs/decisions.md`: one entry — claim commits are local and amended into the closing commit; stage-change commits stay as the transitions log; squash-merge and force-push stay forbidden, with the reasons below.
10. `demo/README.md`, hardening mode: the expected commit count per story (nine, more with the coder's work commits) and a check that no `claim for <stage>` subject other than intake's reaches GitHub.

## What stays as it is, and why

- **Stage-change commits.** They are the transitions log and the `reject` check's input. Folding `tests → doing` and `doing → review` into one commit would lose both.
- **Dispatcher commits** (`blocked: asked`, `comments_seen`, the human's answer in the log, the archive on `main`). Each is an event; they happen only when something happened.
- **No squash merges.** `merged_into_main` asks whether the branch is an ancestor of `main`; after a squash it is not, the branch counts as unmerged and the story keeps being read from it. `main` keeps merge commits.
- **No force pushes, no amend of pushed commits.** The deny list stays; nothing in this plan needs it.

## Verification

- `make check` in the factory (the new watcher test).
- Run 3 part two: after the first story is archived, `gh api repos/…/pulls/<n>/commits` lists no `claim for` subject except intake's, and the stage-change subjects are all present and in order. The restart test of run 1 (kill the container while the reviewer holds its claim) once more: the claim must still be found locally and expire.
