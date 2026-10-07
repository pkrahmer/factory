# 11. Feature acceptance

Every stage sees one story. Nobody sees the feature: whether the stories together keep its promise, what they noticed and left lying, and how the documentation reads as a whole. [Chapter 2](../02-concepts/README.md) introduced the feature acceptance as the work item that does; this chapter specifies it.

## The concept

A feature acceptance is a work item with one agent stage and one gate. It becomes due when a feature is complete, with at least one archived story and nothing in production or in draft, and due again whenever the set of archived stories changes, because a verdict covers a set of stories.

The acceptance judges; it builds nothing. Its result is a report with findings and a recommendation, the **verdict**, and a set of proposed stories as drafts, which only the human promotes (P3). The human's merge or close decides the result, and the result, not the verdict, is the feature's status. A refusal keeps the report and the human's reason, which becomes the brief for the stories the human writes next.

Some judgments belong here rather than in every story: those that need the whole feature (an end-to-end demonstration, the scope against the stories), those that read across stories (the documentation as one text, the notes the stages left behind), and mutation testing, whose survivors can only be judged against the feature's promises.

Where the acceptance sits decides what it can do. v1 merges each story into the main branch when the human accepts it, so the feature's code is already there when its acceptance runs: the acceptance cannot reject code, only hold back what comes next, such as a release. The alternative v1 rejected is a branch per feature, with the stories merging into it and the acceptance as the pull request to the main branch: a real gate on code, suited to features built in parallel or a main branch others depend on, at the price of story pull requests against another base, a watcher reading feature branches, and conflicts between features. Design decision: 2026-10-05 (trunk-based stays).

## In v1

### Due, and the acceptor's task

The watcher derives the acceptance from the feature folder ([chapter 6](../06-watcher/README.md), *Reading the work items*), and the stage protocol runs it like a first stage ([chapter 8](../08-stage-run/README.md)). The acceptor's task ends with three facts, from `_acceptor_facts`:

| Line | Computed from |
| :- | :- |
| `Archived stories: F0002-S0001, F0002-S0002, F0002-S0003` | the stories under `done/` |
| `Next free story number: F0002-S0004` | the highest `S` number of any Markdown file in the feature folder, `drafts/` included, plus one |
| `Cost of the stories: 19 runs, 7.1 min, $3.33` | the last log entry of each archived story that matches `stage.COST`, summed ([chapter 4](../04-work-items/README.md)) |

The acceptor's decisions are `accept`, which moves the acceptance to its gate, `question` and `stuck`.

### The eight items

The `role-acceptor` skill orders the work as eight things to check, the book's *items*. Each gets a section of the report, with a finding or "none":

| Section | Item |
| :- | :- |
| `## 1 Scope` | `FEATURE.md`'s Goal, Scope and Out of scope against the archived stories: a scope item without a story, a story outside the scope, a goal the stories do not reach together |
| `## 2 Feature demo` | a walk-through of the feature's purpose end to end, written as one script against the real entry points, run, with command and output pasted; not the stories' demonstrations again |
| `## 3 Mutation score` | `make mutants`, if the project has it; survivors read and grouped by module and rule into missing criteria |
| `## 4 What the stories noticed` | the coders' "noticed but not touched", the documenters' stale-but-unrelated, the reviewers' remarks, collected from the archived stories |
| `## 5 Documentation as a whole` | `README.md` and `docs/` read from the top as a newcomer: contradictions between stories, an example that no longer runs, a missing section |
| `## 6 Decisions taken for the human` | answers and defaults recorded in the logs and in `FEATURE.md`, in one list for the human to accept or revisit |
| `## 7 Slow checks` | whatever the project offers beyond `make check` and `make mutants`, usually nothing |
| `## 8 Cost` | the cost line from the task; whether a story stands out, and why |

The verdict is one of three:
- `accepted`: no finding of weight; drafts at most for survivors and noticed items;
- `accepted with drafts`: findings worth stories, none of them a broken promise;
- `not accepted`: a scope gap, a red feature demo, or documentation that contradicts behavior and misleads a user.

### The report

`ACCEPTANCE.md` has the six state fields plus `stories` and `outcome`, in a fixed order (`story.TRAILING`). The report's `outcome` field records the result, not the agent's decision, which v1's JSON also calls `outcome`.

| Part | Written by |
| :- | :- |
| frontmatter: the six fields, `stories` (the archived ids it covers), and `outcome` once recorded | the factory |
| `# Acceptance of <feature title>` | the factory |
| `## Verdict`: the verdict in bold and two or three sentences of reasons | the acceptor; on a refusal, the factory adds the human's reason as the first paragraph |
| `## 1 Scope` … `## 8 Cost` | the acceptor |
| `## Proposed stories`: one line per draft and why | the acceptor |
| `## Log (append only)` | the factory |

The skill prescribes the log entry's first line, `<verdict>; <n> drafts proposed; make mutants <killed>/<total>`, followed by one line per item; no code verifies it.

Each proposed draft follows `factory/TICKET.md` in full, with a concrete Interface where the change is code, criteria with their failing sides and the two closing criteria, and a Demo with `Expect:` lines. Its first line after the title is `<!-- proposed by feature acceptance of <date>; refine before promoting -->`. One draft covers one coherent change, not one mutant or one remark. Drafts are numbered from the next free number; if the human has unpushed drafts, the numbers can collide, and the human renumbers.

On the board (`watch.board`), a feature's acceptance shows `-` while the feature is incomplete; `due` when it is due or its acceptor is at work; `running` once it waits at its gate, or is merged but not yet recorded; then the recorded `outcome`, which stands until another story is archived. Design decision: 2026-10-05 (feature acceptance).

### In the demonstration runs

- *Operations* (`F0002`), run 4: "accepted with drafts". The project had no `make mutants` target yet, so the acceptor seeded mutants by hand.
- *Todo service* (`F0001`) was accepted three times in run 4 and the two hours after it: first after its four stories, then twice more as the stories its own drafts had become were archived. Each acceptance proposed the next drafts, some of them tests only.
- Run 3 refused two of its acceptances. *Search* (`F0003`) was refused because one draft belonged to another feature, and the human wanted a behavior change instead of a test pinning today's behavior. *Todo service* was refused on purpose, to test the refusal path: the acceptor's verdict, `not accepted` over a crash on an unpaired surrogate in a title, agreed with the human's close, but the human's reason differed. The human would write that story themselves, with the exact message they wanted, rather than take the draft.

> [!WARNING]
> **v1 limit:** test-only drafts cascade. Each acceptance's mutation survivors become draft stories; each story, once archived, makes the acceptance due again; each new acceptance can propose the next test-only drafts. Nothing ends the series but the human declining to promote. A plan to run mutation testing inside each story instead is parked (`docs/backlog/mutants-in-story-loop.md`).

> [!WARNING]
> **v1 limit:** an acceptance's own cost line sums every cost record of `<feature>/ACCEPTANCE.md`, so a feature's third acceptance reports the cost of all three ($4.80 for F0001 above, where the third alone cost $1.60).

> [!WARNING]
> **v1 limit:** any file in `drafts/` keeps a feature from being judged, so a parked idea holds its acceptance back indefinitely, and nothing lets the human ask for an acceptance early. Changes to the main branch made outside the line never make one due.

> [!WARNING]
> **v1 limit:** the report and the drafts are not validated. Form validation skips the report and the proposed drafts, and the pull request's description takes `## Verdict` and `## Proposed stories` by heading, so a missing heading leaves that part empty.

> [!WARNING]
> **v1 limit:** the acceptor's lane is wider than its feature and its task. Its patterns, `factory/features/*/ACCEPTANCE.md` and `factory/features/*/drafts/*.md`, let it write another feature's report or drafts, and overwrite any existing draft, which is the human's unpromoted story. Only the agent file's sentence says "new files".

> [!WARNING]
> **v1 limit:** the result holds nothing back. v1 has no release step, so `accepted` and `refused` are shown on the board and nowhere else.

> [!IMPORTANT]
> **Planner:** what this chapter fixes.
> - **Essential** (each a test):
>   - an acceptance is due when a feature has at least one archived story and nothing in production or in draft, and no report at `done` covers exactly its archived stories;
>   - a refused acceptance is not due again until the set of archived stories changes;
>   - a merged acceptance's drafts neither make it due again nor change its status;
>   - merging a report whose verdict is `not accepted` books `accepted`: the human's action is the result;
>   - a refusal keeps the report and the reason on the main branch and drops the drafts;
>   - the acceptor writes only its report and new drafts of its own feature.
> - **Incidental to v1:** the file name `ACCEPTANCE.md`; the section numbering; mutmut; the three verdict strings (a recommendation scale of some kind is essential).
> - **Watch for:**
>   - decide where the acceptance sits: on a trunk, as a status and a future release condition (v1), or as the pull request of a feature branch, a real gate on code;
>   - a stopping rule for follow-up work, so acceptances do not propose test-only stories without end;
>   - cost as data per agent run and per acceptance, not parsed from log text, and not summed across acceptances;
>   - validate the report's sections and the proposed drafts' form;
>   - let the human ask for an acceptance, and decide whether a parked draft should block one;
>   - give the result a consumer, such as a release.
