# GitHub settings

Everything to set on GitHub, in one place: for each repository the factory builds, for the factory's own repository, for the tokens, and for the account. The branching these settings protect is in `docs/branching.md`.

## Repositories the factory builds

**Settings → General → Pull Requests**

| Setting | Value | Why |
| :- | :- | :- |
| Allow merge commits | on | the only merge the watcher understands |
| Allow squash merging | **off** | a squash reads as an illegal stage change (`docs/branching.md`) |
| Allow rebase merging | **off** | untested with the watcher |
| Allow auto-merge | off | the human's merge is the acceptance |
| Always suggest updating pull request branches | either | "Update branch" merges `main` in, which the next stage pulls without harm |
| Automatically delete head branches | either | the dispatcher deletes them anyway |

**Settings → Rules → Rulesets → New branch ruleset**

- **Ruleset "main":**
  - Target: the default branch. Enforcement: active. Bypass list: empty.
  - Rules on: **Restrict deletions** and **Block force pushes**.
  - Rules off:
    - **Require a pull request before merging.** The dispatcher and the human commit to `main` directly. The container's token is the owner's, so a bypass for the dispatcher would cover everyone and the rule would protect nothing.
    - **Require linear history.** It forbids merge commits.
    - **Require status checks to pass.** There is no CI yet; GitHub Actions on ready pull requests is in the backlog.
    - **Require signed commits.** The agents do not sign.
- **Ruleset "tickets":**
  - Target: `ticket/**` and `acceptance/**`.
  - Rule on: **Block force pushes**.
  - Deletion stays allowed: the dispatcher deletes these branches.

**Settings → General**

- **Visibility:** private.
- **Features:** Issues, Wiki, Projects and Discussions can be off. The pipeline talks only through pull requests.

**Settings → Code security**

- **Secret scanning and push protection:** on, where the plan offers them. For personal accounts that means public repositories.

## The factory's own repository

- **Pull Requests:** merge commits on; squash allowed if wanted (no watcher reads this repository); auto-merge off.
- **Ruleset "main":** Restrict deletions and Block force pushes. Nothing else: the maintainers and their Claude sessions commit to `main` directly or through pull requests.
- **Code security:**
  - secret scanning and push protection on;
  - Dependabot alerts on;
  - private vulnerability reporting on, once the repository is public.
- **Features:**
  - Issues on, for feedback once the repository is public.
  - Wiki and Projects off.
  - Discussions as wanted.
- **Visibility:** public, once the settings above are in place.

## Tokens

- **The container's `GH_TOKEN`:** a fine-grained personal access token, limited to the repositories in `REPOS`.
  - Permissions: Contents read and write, Pull requests read and write, Metadata read.
  - If `gh pr comment` is refused, add Issues read and write (pull request comments go through the issues API).
  - Give it an expiry date. A classic token with `repo` scope works too, but reaches every repository of the account.
- **`gh` on the human's machine:** logged in with `repo` scope. `scripts/demo-check.sh` checks for it, because the session that plays the human merges, closes and comments with it.

## The account

**github.com/settings/emails**

- **Keep my email addresses private:** on. Merges and edits on github.com then carry `<id>+<login>@users.noreply.github.com`.
- **Block command line pushes that expose my email:** on. It refuses any push that contains a commit authored with a private address of the account. Turn it on only once nothing commits under the personal address any more. The block covers only the addresses registered on the account.

On every machine that commits, set the same noreply address as the git author: `git config --global user.email "<id>+<login>@users.noreply.github.com"`. The container's identity defaults to `factory@users.noreply.github.com` (`compose.yml`).
