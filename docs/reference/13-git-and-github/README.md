# 13. Git and GitHub

Part II named every commit subject, every post and every lookup a handler makes. This chapter takes the repository's side: which branches exist, who commits where, how the factory's checkout stays in step with the remote, and what the hosting service must be set to. [Chapter 10](../10-human-at-the-gate/README.md) has the pull request as the human sees it.

## The concept

The factory uses **trunk-based development**: one long-lived main branch, and a short branch per work item ([chapter 2](../02-concepts/README.md)). Three properties keep the factory's view of the repository true:
- *The remote is the truth;* the factory's checkout is a cache of it. Every tick starts by fetching, and every handler that changes a branch pushes before it ends. A checkout that has parted from its remote is a stop the human must hear of, not a state to build on.
- *History is never rewritten.* The factory only fast-forwards, merges and commits; a branch that cannot fast-forward is a stall or a failure, never a force.
- *The human's merge is read as acceptance, and never as anything else.* Whatever detects stage changes in the history must not misfire on a merge, whichever method the hosting service used.

The hosting service must offer what [chapter 3](../03-principles/README.md) lists in its Planner box.

## In v1

[`docs/branching.md`](../../branching.md) is v1's specification and [`docs/github-settings.md`](../../github-settings.md) its settings.

### Branches

| Branch | Holds | Created | Ends |
| :- | :- | :- | :- |
| `main` | everything accepted; the human's work items; the factory's bookkeeping | — | never |
| `ticket/<file stem>` | one story, from its first stage to the human's decision | by `stage._open`, from the main branch, when the story's first stage is due ([chapter 8](../08-stage-run/README.md)) | deleted after a merge or a discard; kept after a send-back |
| `acceptance/<feature folder>` | one feature's acceptance report and its proposed drafts | the same, when the acceptance is due | deleted after a merge or a refusal |

The table in `docs/branching.md` says intake and the acceptor create the branches; its own step list, and the code, say the factory does. `repo.delete` removes a branch locally (unless it is checked out), prunes, and deletes it on the remote with `git push origin --delete`; a branch already gone is fine.

The names `main` and `origin` are fixed in the code (`ops.MAIN`, `watch.MAIN_REF`, `tick.sync_main`), and `gh pr create` is called without `--base`, so every pull request targets the repository's default branch, which must be `main`.

### Who commits where

| Branch | Who | Commits |
| :- | :- | :- |
| `main` | *the human* | features, drafts, the stage table, the forms, the guide, the build files; the `git mv` that promotes a story |
| `main` | *the human, on GitHub* | the merge commit of a pull request |
| `main` | *the factory* | one per event: the archive after a merge, the refusal record, the discard ([chapter 7](../07-dispatcher/README.md)); and `reject`'s correction when the checkout is on the main branch |
| a work item's branch | *the factory* | the first commit; `merge main` before a later stage, when the main branch has moved; one commit per stage result; the bookkeeping of questions, answers, send-backs, corrections, stalls and expired agent runs |
| a work item's branch | *the coder* | its work commits, `ticket <id>: feat(<layer>): …` |
| a work item's branch | *the tick* | `work left uncommitted by an interrupted run`: whatever a killed process, or a handler that raised between an edit and its commit, left in the work tree ([chapter 14](../14-runtime/README.md)) |
| a work item's branch | *the human, by hand* | any push between stages, GitHub's *Update branch* included; the next stage pulls it |

A clean story leaves seven commits of the factory's on its branch (the first and six stage results), plus the coder's; on the main branch, the promotion, the merge commit and the archive. The table in `docs/branching.md` also lists "an answer as a log entry when no pull request exists yet" among the human's commits on the main branch; no code reads one, because every work item has a pull request before its first agent run.

Commits carry a noreply address only (design decision 2026-10-05: a repository the factory builds may be public, and an address in a commit stays in its history). Pull requests, comments and pushes go through the human's token.

### Staying in step

| Step | Where | What |
| :- | :- | :- |
| *Fetch* | `tick.fetch`, every tick | `git fetch -q --prune origin`; its exit status is ignored |
| *The main branch* | `tick.sync_main`, every tick | only when the checkout is on `main`: `git merge --ff-only origin/main`; a failure is logged and the tick goes on |
| *A work item's branch* | `repo.checkout`, before a stage or a handler | check out (tracking `origin/<branch>` if only the remote has it), then `git pull --ff-only`; `False` if it cannot fast-forward |
| *The main branch into a work item* | `repo.merge_main`, before every stage on an existing branch | `git fetch origin main`, `git merge --no-edit origin/main`; on a conflict `git merge --abort` and a stall ([chapter 8](../08-stage-run/README.md)) |
| *Push* | `repo.push`, after every handler's commit | `git push -q -u origin <branch>`; a rejection raises |
| *Push of leftovers* | `tick.recover_dirty_tree` | `git push -q`; a rejection is ignored |

### Merges

v1 learns of a merge from the pull request's state, not from the history. The history matters only to the rule against illegal stage changes, which exempts real merge commits ([chapter 6](../06-watcher/README.md)). A squash merge puts the whole branch into one ordinary commit on the main branch, in which the story's `stage` jumps from `ready` (the main branch's copy has no `stage`, and `last_change` reads that as `ready`) to `accept`. And it leaves the branch's tip outside the main branch's history, so the watcher still reads the story from its branch, at `accept`. Two cases follow, depending on where the checkout is:
- *On the work item's branch,* as it usually is after the hand-over: the branch's last commit is legal, the pull request's state arrives as `merged`, and the story is archived. The squash goes unnoticed.
- *On `main`:* `sync_main` fast-forwards to the squash commit, and the same tick's evaluation reads it as `reject … ready accept` (observed on 2026-10-05). The factory moves the story back on the main branch and posts a correction on the merged pull request; by the code, the very next tick reads the story from its branch, finds the pull request merged, and archives it. The archived log keeps the entry "illegal stage change ready → accept, moved back".

Either way, `merged` then deletes the branch, so its commits survive only in GitHub's reference to the pull request. A rebase merge is untested.

### Settings on GitHub

`docs/github-settings.md` sets, for every repository the factory builds:

| Setting | Value | Why |
| :- | :- | :- |
| *Merge methods* | merge commits only; auto-merge off | the only merge the watcher was tested with; the human's merge is the acceptance |
| *Ruleset `main`* | restrict deletions, block force pushes; nothing else | "require a pull request" would block the human's promotions and the factory's bookkeeping on the main branch; "require linear history" forbids merge commits; no CI exists for status checks; agents do not sign |
| *Ruleset `tickets`* (`ticket/**`, `acceptance/**`) | block force pushes; deletions allowed | the factory deletes these branches |
| *Visibility* | private | |
| *Code security* | secret scanning and push protection, where the plan offers them | for a personal account, only public repositories, so a private project has neither |

The token in the container, `GH_TOKEN`, is a fine-grained personal access token of the human's, limited to the repositories in `REPOS`, with Contents and Pull requests read and write and Metadata read; Issues read and write if `gh pr comment` is refused, because pull request comments go through the issues API. It should expire. A classic token with `repo` scope works too, and reaches every repository of the account.

> [!WARNING]
> **v1 limit:** the factory has no identity of its own. It pushes, opens pull requests and comments with the human's token, so GitHub treats it as the human, with the consequences [chapter 10](../10-human-at-the-gate/README.md) states. Its commits carry an address that belongs to nobody it controls: GitHub resolves `factory@users.noreply.github.com` by the login before the `@`, and attributes the demonstration project's commits to an unrelated organization named `factory`. A machine account or an app installation with its own noreply address would fix both.

> [!WARNING]
> **v1 limit:** the main branch accepts any push the token can make. Because the human and the factory commit there directly, the ruleset cannot require a pull request, and a bypass would cover the token's owner, which is the human and everything that holds the token. "Nothing lands without the human" holds on GitHub only because nothing else pushes to `main`; [chapter 15](../15-safety/README.md) shows what else holds the token.

> [!WARNING]
> **v1 limit:** a rejected push stops the work item, mostly in silence. It raises in `repo.push`: a counted failure, not the stall `docs/branching.md` describes. The commit stays in the local branch, which the watcher reads before `origin/` ([chapter 6](../06-watcher/README.md)):
> - *if the commit was `demo → accept`,* the hand-over never ran, the pull request stays a draft, and nothing more happens;
> - *if it moved the story to a stage with an agent,* each later `run` stalls at the fast-forward (`stage._prepare`), posts, and fails to push its stall; after two stall posts the attempts cap is reached, and `dispatch.ask` fails three times at the same fast-forward before the give-up post;
> - *on the main branch* (a promotion pushed while `merged` archived), the `merged` event returns, `ops.to_main` raises "main cannot fast-forward" three times, and since `merged` outranks all new work, the repository stops; a restart only repeats the cycle.
>
> A failed fetch is ignored, and the tick evaluates the refs it had. When the token expires, the failures and the give-up post go through the same token, and reach only the factory's log file.

> [!WARNING]
> **v1 limit:** nothing checks the settings. The merge methods, the rulesets, the default branch and the container token's scope and expiry are documented, not verified. `scripts/demo-check.sh` reads only the repository's visibility, as a note, and the scope of the human's own `gh` login.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - a short branch per work item, created by the factory from the main branch before the first agent run, deleted after a merge, a discard or a refusal;
>   - the main branch receives only the human's work and the factory's bookkeeping about finished work items, each as one commit;
>   - fetch every tick, fast-forward only, never rewrite history;
>   - a merge is learned from the hosting service's state; the illegal-change rule never fires on the human's merge.
> - **Incidental to v1:** GitHub, `gh`, the branch prefixes, the ruleset names, the commit subjects, `main` and `origin` as names.
> - **Watch for:**
>   - a factory identity of its own (machine account or app) for commits, pushes and posts, and a protection rule on the main branch that admits exactly that identity and the human's merge;
>   - verify the hosting service's settings in the preflight: merge methods, branch rules, the default branch, the token's scope and expiry;
>   - after a rejected push, the next tick reports the factory's unpushed commit as a stop the human sees, then resets the local branch to its remote; test it with a push to the branch during a stage, and with a promotion during an archive;
>   - read the pull request's state before applying the illegal-change rule, so no merge method is misread; read the base branch from the repository instead of assuming `main`.
