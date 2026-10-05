---
name: stage-feature
description: Stage instructions for `feature`, the acceptance of a whole feature. Preloaded into the acceptor agent; not invoked directly.
---

Your ticket is `factory/features/<feature>/ACCEPTANCE.md`; the feature is the folder. The factory has created the branch `acceptance/<feature>`, written the report's head (its frontmatter with the archived stories, and the title) and opened a draft pull request. Every story of the feature is under `done/`, nothing is in `ongoing/` or `drafts/`. Your task names the archived stories, the next free story number and what the stories cost.

1. Do the eight checks of the role skill. Run the feature demo and `make mutants` for real; paste what they printed. `make check` must be green as you found it; if it is not, that is the first finding.
2. Write `ACCEPTANCE.md` below its head: `## Verdict` (one of the three, with the reasons in two or three sentences), then `## 1 Scope` to `## 8 Cost` as the role skill lists them, then `## Proposed stories` naming each draft you wrote with one line on why. Leave the frontmatter and the title as they are. Write the drafts into `drafts/`.
3. End with `accept` and the entry `<verdict>; <n> drafts proposed; make mutants <killed>/<total>`, followed by the eight findings in short, one line each. The factory commits, writes the pull request body from your Verdict, your entry and the proposed stories, and marks it ready for the human.

If you cannot finish (a tool missing, the budget nearly spent), write what you have into `ACCEPTANCE.md` and end with `stuck`, saying where you stopped (R2). The stage runs again.

When the human merges, the factory sets `stage: done` and `outcome: accepted` on `main` and deletes the branch; the drafts are then the human's. When the human closes, the factory copies your report to `main` with `outcome: refused` and the human's comment under the verdict, without the drafts; your findings survive, and the acceptance is due again when another story is archived. You never write `outcome` yourself.
