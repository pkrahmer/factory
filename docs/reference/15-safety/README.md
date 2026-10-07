# 15. Safety

Every stage agent runs commands a model wrote, in a checkout the factory pushes from, on a machine that holds the factory's credentials. This chapter states what v1 does to contain an agent run and, at greater length, where that containment ends. The mechanisms themselves are specified elsewhere: the lane guard and the undo in [chapter 8](../08-stage-run/README.md), the allow and deny lists in [chapter 9](../09-agents-and-skills/README.md), the machine in [chapter 14](../14-runtime/README.md).

## The concept

Two threats shape the design. The likely one is a model that errs: it edits a test it should not, runs a command that destroys work, or reports green where nothing ran. The other is a model that is steered by text it reads: a comment, a dependency's documentation, a web page, a story written to mislead. Both act through the same means, so one set of defenses serves both, and the second sets the bar.

An agent run's reach should be bounded in four layers:
1. *What it can reach:* the files, credentials, processes and network an agent run's process can touch at all. Only a sandbox bounds this.
2. *What it may do:* the commands and tools the agent runtime lets it use.
3. *What survives it:* every change outside its lane is undone after the stage.
4. *What lands:* nothing reaches the main branch without the human's merge (P3), which reviews whatever the first three let through.

The aim is that the worst an agent run can do is spoil its own work item's branch, which the next stage, the reviewer or the human then sees. Every credential the factory needs belongs to the factory's code, not to the agent; and the layers that matter most are the ones that do not depend on the model's cooperation (P10): a sandbox before a permission list, a permission list before an instruction.

## In v1

v1 has the second and third layers and leans on the fourth. Its first layer is only the container ([chapter 14](../14-runtime/README.md)), which bounds the machine, not the agent run: the design decision of 2026-10-04 that moved the loop there gives the reason, that agents running model-written commands should not do so in the human's own account on the human's own computer. Inside the container, the agent's commands pass three filters:
- *the allow and deny lists* of `~/.claude/settings.json` ([chapter 9](../09-agents-and-skills/README.md));
- *Claude Code's auto mode* (`--permission-mode auto`): a second model, the classifier, judges whatever the lists do not decide; `--permission-prompts none` denies whatever would still ask;
- *the lane guard and the undo* ([chapter 8](../08-stage-run/README.md)), with the protected paths of [chapter 12](../12-project-contract/README.md).

What the classifier decides is Claude Code's, not v1's: its rules are in Claude Code's documentation, they change between versions, and v1 pins no version ([chapter 14](../14-runtime/README.md)). The statements below about the agent runtime's behavior come from that documentation, read on 2026-10-07; v1 has tested none of them.

### What an agent run can reach

An agent run's process inherits the factory's environment (`agent.subprocess_process` passes `os.environ`, plus `AGENT_ENV`) and runs as `factory`, the user that owns its home, `/work`, `/opt/factory` and the tools installed under its home, Claude Code and the factory package (`Dockerfile`):

| Resource | How an agent run reaches it | What stops it |
| :- | :- | :- |
| *`GH_TOKEN`* | the environment | `gh *` is denied; `curl` is allowed, and the classifier judges the rest |
| *Git's credentials* | the credential helper `gh auth git-credential`, set up by `gh auth setup-git`; it has no stored login and works through `GH_TOKEN` | the deny rule `git push*`, as written only |
| *The Claude login* | `~/.claude/.credentials.json`, readable by its owner | the classifier |
| *Agents, skills, settings* | `~/.claude/` | the guard refuses Edit and Write outside the checkout; Claude Code routes recognized writes to `.claude` to the classifier |
| *The factory's code* | `/opt/factory`, the installed package under `~/.local/share/uv/tools/factory`, Claude Code under `~/.local/` | the guard, for Edit and Write; the classifier |
| *The checkout's `.git/`* | hooks, configuration, the factory's state files | the guard, because no lane reaches it; Claude Code routes recognized writes there to the classifier; the undo never looks there |
| *Ignored files in the work tree* | any path in `.gitignore`, `.venv/` included | the guard, for Edit and Write outside the lane; the undo never sees them |
| *Other checkouts* | `/work/<other>`, with several entries in `REPOS` | the guard, for Edit and Write |
| *The network* | `curl`, any program | the classifier |

A program started by an allowed command writes unchecked, and the guard fails open: a tool call it cannot parse, or one without a `file_path`, passes (`guard.main`).

> [!WARNING]
> **v1 limit:** every agent holds the human's GitHub token. `GH_TOKEN` is in its environment (`agent.subprocess_process`), and the deny list blocks only `gh` and a few spellings of Git commands. Claude Code matches a Bash rule as written, so `git -C . push origin main` does not match `git push*` (the documentation uses that example), and the classifier allows, by default, "pushing to any branch of the repository you're working in, including the default branch". The GitHub API is reachable with `curl`. With the token an agent can do anything the human's token can on the factory's repositories: push to the main branch, which no ruleset protects against an ordinary push ([chapter 13](../13-git-and-github/README.md)); merge its own pull request, which is the acceptance; close, reopen, or comment as the human, which the factory then copies into the log as the human's answer. [Chapter 3](../03-principles/README.md)'s P10 table says that pushing and calling the hosting service "are denied to the agent"; that holds for the spellings the deny list names, not for the act.

> [!WARNING]
> **v1 limit:** the allow list does not describe what runs. In auto mode Claude Code drops "broad allow rules that grant arbitrary code execution", package-manager run commands among them, so `Bash(uv run *)` sends every `uv run` to the classifier instead of allowing it; the list's effective boundary is the classifier's judgment. Of the rules that stay, `make *` runs any recipe through `--eval`, and `pkill *` stops any process of the user, the tick's included. `rm` is not on the list at all; the deny rule `rm -rf *` names one spelling, and Claude Code denies removals of critical paths by itself. The list was built to keep agents from stalling ([chapter 9](../09-agents-and-skills/README.md)), not drawn as a boundary (`claude/settings.json`).

> [!WARNING]
> **v1 limit:** what an agent run writes outside the tracked work tree outlives it. The undo compares tracked files and untracked files Git does not ignore (`git ls-files --others --exclude-standard`) with the start commit (`stage._undo_out_of_lane`); nothing else is ever restored:
> - *`.git/`:* a hook in `.git/hooks/` runs inside the factory's own `git` commands at the next commit, and keys in `.git/config` such as `core.fsmonitor` run code in every `git status` the tick makes; the earlier cost records, which the bill at the gate sums, can be rewritten;
> - *ignored paths:* a `.pth` file planted in `.venv/` runs in every later `uv run`, the factory's own checks included; and the demonstration project's `.gitignore` lists `.claude/settings.local.json`, which Claude Code applies, untracked, without a trust step, to every later agent run in that checkout;
> - *other checkouts:* a write into another repository's checkout on a work item's branch is committed and pushed there by that repository's next tick (`tick.recover_dirty_tree`);
> - *`~/.claude/` and the image's files:* changed agents, skills and settings apply to every later agent run; the entrypoint copies `/opt/factory/claude/` over them at start (`entrypoint.sh`), but the agent's user owns that source too. `/opt/factory`, the installed `factory` package (which holds the guard and the undo themselves) and Claude Code last until the container is recreated; `restart: unless-stopped` (`compose.yml`) restarts the same container, whose changed `entrypoint.sh` then runs. The volumes outlive even a rebuild.
>
> Leftovers of a killed agent run skip even the undo ([chapter 8](../08-stage-run/README.md)).

> [!WARNING]
> **v1 limit:** text from outside reaches the agents unfiltered. The factory copies every comment on a pull request that lacks its marker into the log as `human (pull request comment, <date>)`, whoever wrote it: `github.GitHub.view` reads no author, and `dispatch._copy_comments`, `dispatch.answers` and `_reason_given` trust what it returns. `docs/github-settings.md` makes the project's repository private, so only collaborators can comment; on a repository others can comment on, a stranger's comment answers a question, retries a stage at the attempts cap, or becomes the reason for a send-back. An agent that holds the token can do the same in the human's name. Dependencies the project installs, their documentation in `.venv/`, and pages fetched with `curl` are read as freely. Nothing marks such text as data rather than instructions.

> [!WARNING]
> **v1 limit:** refused actions are not recorded. `agent.run` collects the agent runtime's permission denials, but `stage._outcome` reports only the first one, and only in a stall's reason; a successful agent run's refused attempts, a denied push among them, are recorded nowhere, not in the log and not in the cost record.

None of this was exercised in the demonstration runs, which had a simulated human, stories written in advance and no other commenters. No agent run is known to have used any of these paths; nothing v1 configures or tests kept it from them. Claude Code offers stronger options v1 does not use: its Bash sandbox, `--setting-sources` to leave out project settings, and `--bare`; whether the sandbox works in v1's image is untested.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - four layers, each independent of the model's cooperation: what an agent run can reach, what it may do, what survives it, what lands;
>   - the worst case of an agent run is its own work item's branch; the human's merge reviews the rest;
>   - every credential belongs to the factory's code; no agent run holds a token that can push, merge or post;
>   - text from outside the human's two places (P4) is data, and comments count as the human's only when the human wrote them.
> - **Incidental to v1:** Docker; Claude Code's permission modes, its classifier and its rule syntax; the guard as a `PreToolUse` hook.
> - **Watch for:**
>   - run each agent run's tools in a sandbox of its own: a copy of the checkout without `.git/`, no credentials (the agent runtime's model login held by a process outside the sandbox, or behind a proxy), no access to the factory's code or other checkouts, network only to the model provider and the package index;
>   - strip `GH_TOKEN` from the agent's environment: with v1's credential helper, that alone closes both the API and `git push`;
>   - an allow list per role, built as a boundary and tested against a pinned agent runtime, with wrappers and options (`make --eval`, `git -C`, `git -c`, `find -exec`, `uv run`) treated as what they run; a guard that fails closed;
>   - undo or forbid writes to ignored paths, and keep the agent runtime's project settings out of the agent's reach;
>   - read each comment's author, and count only the human's;
>   - record every permission denial, and test the containment: each row of the table above as a case that must fail.
