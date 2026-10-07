# 9. Agents, roles and skills

[Chapter 2](../02-concepts/README.md) defined a role by five parts and its instructions by four layers; [chapter 8](../08-stage-run/README.md) showed how v1 assembles them into one agent run. This chapter specifies the content: what each role judges, what each stage must leave in the log, and which rule is enforced by what.

## The concept

A role exists for one kind of judgment, and owns nothing else:

| Role | Judges |
| :- | :- |
| intake | whether a story is buildable as written |
| tester | how each criterion becomes a test |
| coder | how to make the tests pass inside the architecture |
| reviewer | whether the diff does what the story says, inside the architecture, safely |
| documenter | what a reader who was not there needs to know now |
| demo | whether observed output matches the expected output and the criteria |
| acceptor | whether the stories together keep the feature's promise |

Per stage, a planner must carry over three things: the steps (including what to read first and what not to read), the log entry's required contents, and the meaning of each decision. The entry matters beyond the stage: the next stage reads it, and so may code.

A rule an agent is told and code does not enforce is a known gap, and should be listed as one; P10 says why. And an agent's cost is mostly reading: each turn re-reads the whole conversation so far, so a turn or a read saved at the start of an agent run saves its share on every later turn. Instructions are therefore tuned by measurement, turns and tokens per agent run before and after a change (P16, P17).

## In v1

### The seven agents

Each agent is a Markdown file in `claude/agents/` with YAML frontmatter. The runner reads five keys ([chapter 8](../08-stage-run/README.md)):

| Agent | Stage | `model` | `effort` | `budget_usd` | `tools` | `skills` |
| :- | :- | :- | :- | -: | :- | :- |
| intake | `ready` | sonnet | low | 1 | Read, Grep, Glob, Edit, Bash | rules, `stage-intake` |
| tester | `tests` | opus | medium | 2 | as intake, plus Write | rules, `role-tester`, `stage-tests` |
| coder | `doing` | opus | medium | 4 | as intake, plus Write | rules, `role-coder`, `stage-doing` |
| reviewer | `review` | opus | high | 3 | Read, Grep, Glob, Edit, Bash | rules, `role-reviewer`, `stage-review` |
| documenter | `docs` | sonnet | medium | 1.5 | as intake, plus Write | rules, `role-documenter`, `stage-docs` |
| demo | `demo` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash | rules, `stage-demo` |
| acceptor | `feature` | opus | high | 8 | as intake, plus Write | rules, `role-acceptor`, `stage-feature` |

*rules* is the skill `factory-rules`. Leaving out Write is no boundary: Edit still changes files, and Bash can write anything. Intake runs on Sonnet because Haiku, its first model, needed more than 20 turns on a story and guessed timestamps; no design decision records why the documenter does. Each file's body is one or two sentences, the agent's own boundary: "Never edit tests; a wrong test is a question" for the coder, "Fix nothing" for the demo, "Do not improve the ticket; accept it or ask" for intake. Design decisions: 2026-10-04 (intake on Sonnet, not Haiku; the permission mode), 2026-10-05 (budgets in dollars).

### The rules, R1 to R15

`claude/skills/factory-rules/SKILL.md` gives every agent the same fifteen rules. The table maps each to the principles of [chapter 3](../03-principles/README.md) and to its enforcement; the list below it is the complete list of what R1 to R15 ask and nothing enforces. Role rules that nothing enforces are in the limits at the end of this chapter and of [chapter 11](../11-feature-acceptance/README.md).

| Rule | In short | Principles | Enforced by |
| :- | :- | :- | :- |
| R1 | Git is the only truth; nothing carries over between agent runs | P2, P6 | a fresh process with a new Claude Code session and auto memory off (`AGENT_ENV`) |
| R2 | Every stage ends with a decision and an entry: what was done, why, what was rejected, what is open; for `stuck`, where it stopped | P1, P10 | `--json-schema`; anything else is a stall |
| R3 | One work item; never the feature's `FEATURE.md` | P3, P5 | the undo restores every other story; the guard refuses any `FEATURE.md` |
| R4 | The work item is the memory; no work item or criterion named in code | P6 | nothing |
| R5 | State and log are the factory's; new criteria before the two closing ones; no clock time; never move the file | P2, P10 | the restore after the agent run; form validation (the closing criteria); the undo (a move is a deletion and an out-of-lane write) |
| R6 | Take the facts from the task | P10, P11 | the task (`stage._task`) |
| R7 | The stage changes by the decision only; the factory runs the checks | P10, P11 | `stage._decide`, `_checks`; `reject` for hand edits ([chapter 6](../06-watcher/README.md)) |
| R8 | Ask with `question`, with the options and a preference; never guess on the guide's list of things not to do without asking | P9 | `question` is always allowed; the `ask` handler posts it ([chapter 7](../07-dispatcher/README.md)) |
| R9 | Tests are the tester's; a wrong test is a question; an approved change goes back to `tests` | P7, P8 | the coder's lane has no `tests/`; the guard and the undo; the `Mode:` line in the tester's task |
| R10 | One branch; never push, check out, switch, merge, pull or call `gh`; only the coder commits | P2, P3 | the deny list; the branch test after the agent run |
| R11 | `make check` means that command; a missing tool is `stuck` | P11 | the factory runs the checks; the preflight checks the machine ([chapter 14](../14-runtime/README.md)) |
| R12 | Rework rounds share one counter, capped | P12 | `stage._rework`, `dispatch._sent_back` |
| R13 | Nothing starts without the human; only the acceptor proposes drafts; no scope beyond the assignment | P3 | only the acceptor's lane reaches `drafts/`; the undo removes any new story in `ongoing/` |
| R14 | Commit subjects start with `ticket <id>:` | P2 | the factory's own subjects |
| R15 | The pipeline's files (`stages.yml`, the templates, every `FEATURE.md`, `drafts/`, `done/`, `.claude/`) are the human's; write only your lane | P3, P10, P15 | the guard's never-lists, the lanes, the undo ([chapter 8](../08-stage-run/README.md)); the guard's refusal cites "(R15)" |

What no code enforces:
- *R1:* ignored files and background processes, such as a demo's server, outlive the agent run;
- *R2:* the entry's contents;
- *R4:* all of it; the reviewer looks for names in code;
- *R5:* clock times;
- *R6:* looking them up anyway;
- *R8:* guessing;
- *R9:* that a `tests` decision follows a human's approval;
- *R10:* `git commit` is allowed to every agent; the undo reverts content, the commit stays in the history;
- *R13:* scope;
- *R14:* the coder's subjects.

### The roles and their stages

Each agent's prompt carries one stage skill, named after its stage (`stage-review`), except intake's, `stage-intake` for `ready`; all but intake and the demo also carry a role skill (`role-coder`). Every stage may end with `question` or `stuck`; the table lists the other decisions.

| Agent | Must not | Entry must contain | Decisions |
| :- | :- | :- | :- |
| intake | repeat what form validation tests; improve the story | `accepted`, then one line per aspect judged: the Interface, the criteria, the Demo, the architecture, the scope; or the numbered questions, the form's findings among them | `tests` (made a question by code if the form has findings) |
| tester | interpret a criterion; test what the criteria leave open; run the tests more than once | criterion → test function, one line each; files created; modules the runner could not import | `doing` |
| coder | edit a test; fix unrelated code; name work items in code or comments | what was built (paths); the main choice and the rejected alternative; what was noticed but not touched | `review`; `tests` for an approved test change |
| reviewer | write any code, even scratch; run `make check`; pass with remarks | numbered findings (location, what is wrong, what would fix it), or "no findings" | `docs`, `doing` |
| documenter | edit code, tests, in-code comments or generated documentation | each file changed and why; documents cross-read and found current; stale text noticed but unrelated | `demo`; `doing` when code contradicts the story or a docstring is missing |
| demo | fix anything; judge taste; write into `## Demo` | each command's trimmed output (at most 40 lines) and whether it met its `Expect:`; findings numbered | `accept`, `doing` |
| acceptor | change anything but the report and new drafts; decide product questions | `<verdict>; <n> drafts proposed; make mutants <killed>/<total>`, then one line per item judged | `accept` |

Rules of individual stages that a planner needs:

- *Intake after an answer* writes exactly what the answer changes into the story (a new criterion before the two closing ones, a reworded Interface line or Demo expectation, the Assignment and its heading if the meaning changed) and names the log entry it came from. That is the human's edit carried in, not an improvement.
- *The tester* tests a stated limit on both sides of each boundary, as one parametrized test; the cases the criteria leave open are a question. With `Mode:` in its task, it makes exactly the named change, runs `make test` once, and ends with `doing`.
- *The coder* refactors once, after green, as a separate commit, and chains its last `make check` with that commit; it commits as it goes with `ticket <id>: feat(<layer>): …`.
- *The reviewer* stops at the first failing group of five, in order: criteria and their tests (failing sides, both sides of each limit), architecture, security, quality, the story's hygiene. A marker that silences a security check is a finding unless the guide allows it and the diff gives the reason.
- *On a rework round*, the coder and the documenter address exactly the latest findings, nothing more.
- *A docs criterion of `none`* means nothing new is written; the cross-read still happens.
- *Reads.* The tester, coder and documenter read everything they need in the first turn, in one command where they can; never other work items, `FEATURE.md`, `factory/` or `.claude/`; never the Makefile, `pyproject.toml` or tool configuration, which the checks enforce; and the project's documentation where the guide points them, not as a tour. Design decision: 2026-10-05 (fewer turns).

The acceptor's eight items, verdicts and drafts are in [chapter 11](../11-feature-acceptance/README.md).

### The project guide

`template/CLAUDE.md` is the project's layer: *Language* (everything in English), *Architecture* (layers, dependency direction, typing and validation), *Tests* (framework, location, what may be faked), *Docs* (the documentation layout, generated files, required docstrings), *Checks* (what `make check`, `make lint` and `make test` run), and *Not without asking*, the list that ends a stage with `question`: among others a new dependency, a change to `factory/`, a change to a test one did not write, a marker that silences a security check. The skills cite *Architecture*, *Tests*, *Docs* and *Not without asking* by name; intake and the coder refer to "the architecture `CLAUDE.md` describes".

### Permissions

`claude/settings.json` applies to every agent run, whatever the role:

| | Patterns |
| :- | :- |
| *Allow, tools* | `Read`, `Edit`, `Write`, `Glob`, `Grep` |
| *Allow, project* | `Bash(uv run *)`, `Bash(uv sync*)`, `Bash(uv export*)`, `Bash(make *)`, `Bash(factory-*)` |
| *Allow, Git* | `Bash(git status*)`, `git diff*`, `git log*`, `git show*`, `git add *`, `git commit *`, `git rev-parse*` |
| *Allow, shell* | `ls *`, `cat *`, `date *`, `sed *`, `grep *`, `sleep *`, `curl *`, `pkill *`, `echo*`, `printf*`, `head*`, `tail*`, `wc*`, `which*`, `find*`, `sort*`, `uniq*`, `tr *`, `cut *`, `diff*`, `mkdir*`, `touch*`, `cd *`, `taskkill*`; exactly `pwd`, `true`, `set -o pipefail` |
| *Deny* | `git push*`, `git checkout*`, `git switch*`, `git merge*`, `git pull*`, `git rebase*`, `git reset*`, `git branch -D*`, `gh *`, `rm -rf *` |
| *Environment* | `CLAUDE_CODE_FORK_SUBAGENT=0`; no design decision records why |

The shell vocabulary was read from the agents' transcripts, after a coder died on a pipe into `head` that the list did not cover. [Chapter 15](../15-safety/README.md) examines where these lists leak.

### Installation

The image copies the repository to `/opt/factory` and installs `claude/agents/`, `claude/skills/` and `claude/settings.json` into `~/.claude/`. That folder is a volume, which also keeps the login, so the entrypoint copies the three again on every start: new and changed files replace the old, but an agent or skill deleted from the image stays in the volume. The project guide is not installed: Claude Code reads `CLAUDE.md` from the checkout it runs in, so every agent run gets the project's own.

> [!WARNING]
> **v1 limit:** the instruction layers are tied to one agent runtime and one toolchain. The project guide must be named `CLAUDE.md`, because Claude Code loads that file. The rules and skills name `make check`, `make lint`, `make test` and `make mutants`; the acceptor's skill runs `uv run mutmut show`; and the documenter's and reviewer's skills name `docs/openapi.json` as an example of generated documentation. R10 points agents to `docs/branching.md`, which exists only in the factory's own repository, not in a project's checkout.

> [!WARNING]
> **v1 limit:** instructions and code are kept in step by hand, and have drifted (the stage skills also name their decisions, [chapter 5](../05-stage-machine/README.md)). `stage-review` tells the reviewer that the factory runs `make check` again after it, but `review` has no `checks`; the next `make check` runs after the documenter. And the template's guide says "the pipeline knows only these three targets" while the acceptor runs `make mutants`.

> [!WARNING]
> **v1 limit:** role boundaries rest on lanes alone. Every role gets the same shell vocabulary, so the reviewer may `git commit` and `curl`. The documenter's lane `docs/*` includes `docs/openapi.json`, the coder's generated file, so the rule that the documenter does not edit generated documentation is enforced by nothing.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential:**
>   - one judgment per role, with the boundaries in the table under *The roles and their stages*: the tester tests nothing the criteria leave open, the coder never edits a test, the reviewer writes no code, the demo fixes nothing, the acceptor proposes and never starts;
>   - per stage: the steps, the first-turn reads and the forbidden reads, the entry's required contents, and the meaning of each decision;
>   - every rule mapped to its enforcement, with the gaps listed (the R table);
>   - the project guide as the project's own layer, read by every agent run;
>   - an instruction change is accepted on turns and tokens per agent run, measured before and after.
> - **Incidental to v1:** Claude Code's agent files, skills and settings format; the model names; the budgets; the R numbering.
> - **Watch for:**
>   - generate each stage's decision text from the stage table instead of writing it into the skill;
>   - make the required entry contents checkable (sections or fields), not only requested;
>   - a command allow list per role, and lanes that do not overlap;
>   - keep tool names (`make`, `uv`, the guide's file name) out of the factory's instructions, or make them project configuration;
>   - every file an instruction names must exist where the agent runs;
>   - whether intake can run on a cheaper model than Sonnet: v1 tried Haiku and got a weaker intake; record the measurement either way.
