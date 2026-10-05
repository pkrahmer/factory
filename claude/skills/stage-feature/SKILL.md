---
name: stage-feature
description: Stage instructions for `feature`, the acceptance of a whole feature. Preloaded into the acceptor agent; not invoked directly.
---

Your ticket is `factory/features/<feature>/ACCEPTANCE.md`, which may not exist yet; the feature is the folder. You are on `main`, every story of the feature is under `done/`, nothing is in `ongoing/` or `drafts/`. Like intake, you create the branch and the pull request; like demo, you leave the pull request ready for the human.

1. `git checkout -b acceptance/<feature>`. Everything you commit goes to this branch.
2. Claim: write `ACCEPTANCE.md` with the frontmatter `stage: feature`, `pr: null`, `blocked: null`, `comments_seen: 0`, `claimed_at: <now>`, `round: 0`, `attempts: 0`, `stories: [<every id under done/, sorted>]` — the `stories` list is what tells the watcher this report covers these stories and no others — and a title line `# Acceptance of <feature title>`. Commit `acceptance <feature>: claim`, push with `git push -u origin acceptance/<feature>`. Like intake's, this claim is pushed because the pull request needs the branch on GitHub, so it stays in the history and your closing commit in step 8 is a normal one (R6).
3. `gh pr create --draft --head acceptance/<feature> --title "<feature>: acceptance" --body "Feature acceptance in progress."`; put the number into `pr`.
4. Do the eight checks of the role skill. Run the feature demo and `make mutants` for real; paste what they printed. `make check` must be green on `main` as you found it; if it is not, that is the first finding.
5. Write `ACCEPTANCE.md`: after the frontmatter and title, `## Verdict` (one of the three, with the reasons in two or three sentences), then `## 1 Scope` to `## 8 Cost` as the role skill lists them, then `## Proposed stories` naming each draft you wrote with one line on why. Write the drafts into `drafts/`.
6. Append a log entry at the end of `ACCEPTANCE.md` under `## Log (append only)`: `1. acceptor: <verdict>; <n> drafts proposed; make mutants <killed>/<total>` — one line.
7. Pull request body: the Verdict section, the eight findings in short, the list of proposed drafts, and this last paragraph, word for word: "Merge, with a merge commit (not squash or rebase), to accept the report and take the proposed drafts into the feature's drafts/, where you refine them before promoting any. Close, with a comment saying why, to refuse: the report stays on main as refused with your comment, the proposed drafts are discarded, and the feature counts as not accepted until another story is archived and a new acceptance runs. Nobody answers comments while the acceptance waits here; they go into the report's log." Then `gh pr ready <pr>`.
8. Set `stage: accept`, clear the claim, commit everything with subject `acceptance <feature>: feature → accept`, push. Stop.

If you cannot finish (turn limit, a tool missing), write what you have into `ACCEPTANCE.md`, append a log entry saying where you stopped, keep `stage: feature`, clear the claim, commit, push (R2). The watcher retries the stage.

When the human merges, the dispatcher sets `stage: done` and `outcome: accepted` on `main` and deletes the branch; the drafts are then the human's. When the human closes, the dispatcher copies your report to `main` with `outcome: refused` and the human's comment under the verdict, without the drafts; your findings survive, and the acceptance is due again when another story is archived. You never write `outcome` yourself.
