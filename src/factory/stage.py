"""One stage run: everything around the agent is code, the agent does the stage's work.

Before the agent: the story's branch is brought up to date (or, for intake and the acceptor,
created with the story's frontmatter and a draft pull request), the run file is written, and
the task names what the agent would otherwise have to work out. The agent ends with a structured
outcome: one of the stages `next` allows, `question`, or `stuck`, and the text of its log entry.

After the agent, the dispatcher keeps what is the agent's and decides the rest:
- writes outside the agent's lane are undone (the guard hook sees only Edit and Write);
- the frontmatter and the log are the dispatcher's: an agent's edits there are dropped;
- the outcome is checked against `next`; a forward move is held when the stage's `checks`
  are red (`stages.yml`), and a rework counts a round, asking the human past `max_rounds`;
- the story's form is checked again; a stage that broke it is a stall;
- the entry is appended as the next log entry, everything is committed and pushed, and at the
  human's gate the pull request body is written from the story and the pull request marked ready.
Anything else, whatever the agent said, is a stall.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from factory import agent, guard, ops, repo, story, watch
from factory.ops import MAIN, Context, Handled

FINISH = "Finish now: give your outcome (`stuck` if the work is not done) and your log entry."
STORY_CLOSING = (
    "Merge to accept, with a merge commit (not squash or rebase). To send it back, close it with "
    "a comment that says what should change; a close without one is answered with a question. "
    "Nobody answers comments while the story waits here: they go into the story's log and become "
    "the reason if you then close."
)
ACCEPTANCE_CLOSING = (
    "Merge, with a merge commit (not squash or rebase), to accept the report and take the "
    "proposed drafts into the feature's drafts/, where you refine them before promoting any. "
    "Close, with a comment saying why, to refuse: the report stays on main as refused with your "
    "comment, the proposed drafts are discarded, and the feature counts as not accepted until "
    "another story is archived and a new acceptance runs. Nobody answers comments while the "
    "acceptance waits here; they go into the report's log."
)
CAP_QUESTION = (
    "What should happen? Answer with a comment; close the pull request to discard the story."
)
EXTRA_OUTCOMES = ("question", "stuck")
FIELDS = {"stage": "", "pr": None, "blocked": None, "comments_seen": 0, "round": 0, "attempts": 0}
COST = re.compile(r"cost: (\d+) (?:\w+ )?runs?, ([\d.]+) min.*\$([\d.]+)")
TAIL = 15  # lines of a red check's output in the log


def schema(allowed: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "outcome": {"type": "string", "enum": allowed},
            "entry": {
                "type": "string",
                "description": "your log entry, without its number or your name: everything "
                "your stage skill says the entry contains",
            },
        },
        "required": ["outcome", "entry"],
        "additionalProperties": False,
    }


def current(ctx: Context, path: str) -> tuple[watch.Ticket, str]:
    """The story as the line saw it: from its branch, else from `origin/main`; and the branch."""
    branch = watch.Ticket(Path(path), {}).branch
    if repo.exists(ctx.root, branch):
        text = repo.show(ctx.root, branch, path)
    else:  # the line was evaluated against origin/main
        text = repo.show_ref(ctx.root, f"origin/{MAIN}", path)
    ticket = ops.ticket_of(path, text)
    if ticket.is_acceptance and (text is None or ticket.stage == "done"):
        # Due: no report yet, or one that covers fewer stories than are archived now. The
        # dispatcher writes the new report's head; the old report stays in main's history.
        ticket = watch.Ticket(Path(path), {"stage": watch.FEATURE_STAGE})
    return ticket, branch


# --- before the agent --------------------------------------------------------------------------


def _title(text: str) -> str:
    return next((line[2:].strip() for line in text.split("\n") if line.startswith("# ")), "")


def _done_ids(ctx: Context, feature: Path) -> list[str]:
    return watch.done_stories([p.relative_to(ctx.root) for p in (ctx.root / feature).rglob("*")])


def _open(ctx: Context, ticket: watch.Ticket) -> None:
    """Intake and the acceptor start on main: the dispatcher creates the branch with the story's
    frontmatter (or the report's head) and pushes it, so the pull request can be opened."""
    path, branch = ticket.path.as_posix(), ticket.branch
    ops.to_main(ctx)
    watch.git(ctx.root, "checkout", "-q", "-b", branch)
    if ticket.is_acceptance:
        feature = ticket.path.parent
        title = _title((ctx.root / feature / "FEATURE.md").read_text(encoding="utf-8"))
        head = {**FIELDS, "stage": ticket.stage, "stories": _done_ids(ctx, feature)}
        ops.write(ctx, path, story.render(head, f"# Acceptance of {title}\n"))
        what = "acceptance starts"
    else:
        meta, body = story.split(ops.read(ctx, path))
        ops.write(ctx, path, story.render({**FIELDS, "stage": ticket.stage, **meta}, body))
        what = "intake starts"
    ops.commit_and_push(ctx, branch, ops.subject(path, what))


def _ensure_pull_request(ctx: Context, ticket: watch.Ticket) -> int:
    """The story's pull request: the recorded one, one GitHub has for the branch, or a new draft."""
    path = ticket.path.as_posix()
    recorded = int(ops.meta(ctx, path).get("pr") or 0)
    if recorded:
        return recorded
    number = ctx.github.find(ticket.branch)
    if number is None:
        _, body = story.split(ops.read(ctx, path))
        if ticket.is_acceptance:
            title, text = f"{ticket.feature}: acceptance", "Feature acceptance in progress."
        else:
            title = f"{ticket.ticket_id}: {_title(body)}"
            text = (
                f"## Assignment\n\n{story.section(body, 'Assignment')}\n\n"
                f"## Acceptance criteria\n\n{story.section(body, 'Acceptance criteria')}"
            )
        number = ctx.github.create_draft(ticket.branch, title, text)
    ops.edit(ctx, path, pr=number)
    return number


def _prepare(ctx: Context, ticket: watch.Ticket, where: str) -> tuple[str, str | None]:
    """Check out where the agent works. (The task's `Branch:` line, a stall reason or None.)"""
    path, branch = ticket.path.as_posix(), ticket.branch
    if where == MAIN and not repo.exists(ctx.root, branch):
        _open(ctx, ticket)
        return branch, None
    if not repo.checkout(ctx.root, branch):
        return branch, f"{branch} cannot fast-forward to origin/{branch}"
    if not repo.merge_main(ctx.root, ops.subject(path, "merge main")):
        return branch, "merging main conflicts; merge aborted"
    if where == MAIN and ticket.stage == "ready":
        return f"{branch} (exists; intake asked before)", None
    return branch, None


def _acceptor_facts(ctx: Context, ticket: watch.Ticket) -> list[str]:
    feature = ticket.path.parent
    done = _done_ids(ctx, feature)
    numbers = [
        int(m.group(1))
        for p in (ctx.root / feature).rglob("*.md")
        if (m := re.match(rf"^{ticket.feature[:5]}-S(\d{{4}})", p.stem))
    ]
    runs, minutes, dollars = 0, 0.0, 0.0
    for path in sorted((ctx.root / feature / "done").glob("*.md")):
        logged = [t for _n, t in story.entries(story.split(path.read_text(encoding="utf-8"))[1])]
        found = next((m for t in reversed(logged) if (m := COST.search(t))), None)
        if found:
            runs += int(found.group(1))
            minutes += float(found.group(2))
            dollars += float(found.group(3))
    return [
        f"Archived stories: {', '.join(done)}",
        f"Next free story number: {ticket.feature[:5]}-S{max(numbers, default=0) + 1:04d}",
        f"Cost of the stories: {runs} runs, {minutes:.1f} min, ${dollars:.2f}",
    ]


def _task(ctx: Context, ticket: watch.Ticket, branch_line: str, findings: list[str]) -> str:
    path = ticket.path.as_posix()
    meta = ops.meta(ctx, path)
    allowed = _allowed(ctx, ticket.stage)
    lines = [
        f"Ticket: {path}",
        f"Id: {ticket.ticket_id}",
        f"Stage: {ticket.stage}",
        f"Allowed outcomes: {', '.join(allowed)}",
        f"Branch: {branch_line}",
        f"Pull request: {meta.get('pr')}",
        f"Round: {int(meta.get('round') or 0)}",
    ]
    logged = story.entries(story.split(ops.read(ctx, path))[1])
    if ticket.stage == "tests" and logged and logged[-1][1].startswith("coder:"):
        lines.append(
            f"Mode: a test change the human approved; the coder's entry {logged[-1][0]} names it."
        )
    if ticket.stage == "ready":
        listed = " ".join(f"{n}. {f}." for n, f in enumerate(findings, start=1))
        lines.append(f"Format check found: {listed}" if findings else "Format check: passed")
    if ticket.is_acceptance:
        lines += _acceptor_facts(ctx, ticket)
    lines.append(
        "End with your outcome and your log entry; the factory commits, pushes and moves the story."
    )
    return "\n".join(lines)


def _allowed(ctx: Context, stage: str) -> list[str]:
    return [*(ctx.config["stages"].get(stage, {}).get("next") or []), *EXTRA_OUTCOMES]


def _form(ctx: Context, ticket: watch.Ticket) -> list[str]:
    """The story's format findings (an acceptance report has a form of its own: none)."""
    return [] if ticket.is_acceptance else story.check_file(ctx.root, ticket.path)


# --- the run -----------------------------------------------------------------------------------


def run(ctx: Context, name: str, ticket: watch.Ticket, where: str) -> Handled:
    path, branch = ticket.path.as_posix(), ticket.branch
    branch_line, blocked = _prepare(ctx, ticket, where)
    if blocked is not None:
        ops.stall(ctx, path, branch, blocked)
        return Handled(True, f"stage {ticket.stage} of {path} stalled: {blocked}")
    _ensure_pull_request(ctx, ticket)
    findings = _form(ctx, ticket)
    before = ops.read(ctx, path)
    started_at = repo.head(ctx.root)
    task = _task(ctx, ticket, branch_line, findings)
    watch.write_running(ctx.root, watch.Running(path, datetime.now(UTC)))
    try:
        result = ctx.start(name, task, schema(_allowed(ctx, ticket.stage)))
    finally:
        watch.clear_running(ctx.root)
    if repo.current_branch(ctx.root) != branch:
        raise RuntimeError(f"the {name} agent left {branch}")
    undone = _undo_out_of_lane(ctx, name, path, started_at)
    _keep_the_dispatchers_parts(ctx, path, before)
    handled = _apply(ctx, name, ticket, result, (findings, undone))
    return Handled(handled.ok, handled.summary, result)


def _undo_out_of_lane(ctx: Context, name: str, path: str, started_at: str) -> list[str]:
    """Restore every path the agent changed outside its lane, and every other story."""
    tracked = watch.git(ctx.root, "diff", "--name-only", "--no-renames", started_at).split("\n")
    untracked = watch.git(ctx.root, "ls-files", "--others", "--exclude-standard").split("\n")
    root = ctx.root.resolve()
    features = watch.features_dir(ctx.config).as_posix()
    undone = []
    for changed in sorted({p for p in tracked + untracked if p and p != path}):
        another_story = re.fullmatch(rf"{re.escape(features)}/[^/]+/ongoing/[^/]+\.md", changed)
        if not another_story and guard.refusal(root, name, str(root / changed)) is None:
            continue
        if repo.ok(ctx.root, "cat-file", "-e", f"{started_at}:{changed}"):
            watch.git(ctx.root, "checkout", "-q", started_at, "--", changed)
        else:
            repo.ok(ctx.root, "rm", "-q", "-f", "--cached", "--", changed)
            (ctx.root / changed).unlink(missing_ok=True)
        undone.append(changed)
    return undone


def _keep_the_dispatchers_parts(ctx: Context, path: str, before: str) -> None:
    """The agent's sections stay; the frontmatter and the log are what they were before it."""
    target = ctx.root / path
    worked = target.read_text(encoding="utf-8") if target.is_file() else before
    meta, old_body = story.split(before)
    _, body = story.split(worked)
    ops.write(ctx, path, story.render(meta, story.with_log(body, old_body)))


def _outcome(ctx: Context, stage: str, result: agent.AgentRun) -> tuple[str, str, str | None]:
    """(outcome, entry, why it cannot be kept or None)."""
    denied = f"; denied: {result.denials[0]}" if result.denials else ""
    given = result.structured or {}
    outcome, entry = str(given.get("outcome") or ""), str(given.get("entry") or "").strip()
    allowed = _allowed(ctx, stage)
    if not result.ok:
        return outcome, entry, (result.reason or "the agent ended with an error") + denied
    if not outcome:
        return outcome, entry, "the agent gave no outcome" + denied
    if outcome not in allowed:
        return outcome, entry, f"outcome {outcome} is not one of {', '.join(allowed)}" + denied
    if outcome == "stuck":
        return outcome, entry, (entry or "the agent is stuck") + denied
    return outcome, entry, None


def _apply(
    ctx: Context,
    name: str,
    ticket: watch.Ticket,
    result: agent.AgentRun,
    checked: tuple[list[str], list[str]],
) -> Handled:
    findings, undone = checked
    outcome, entry, unkept = _outcome(ctx, ticket.stage, result)
    if unkept is not None:
        return _stalled(ctx, ticket, unkept)
    text = f"{name}: {_unprefixed(entry, name, ticket.stage)}"
    if undone:
        text += f"\n\nThe factory undid changes outside the {name}'s lane: {', '.join(undone)}"
    broke = [f for f in _form(ctx, ticket) if f not in findings]
    if broke:
        return _stalled(ctx, ticket, "the story's form broke: " + "; ".join(broke), text)
    return _decide(ctx, ticket, outcome, text, findings)


def _unprefixed(entry: str, name: str, stage: str) -> str:
    """Agents tend to start their entry with their own name or their stage's; the dispatcher
    writes that prefix itself."""
    for prefix in (f"{name}:", f"{stage}:"):
        if entry.lower().startswith(prefix):
            return entry[len(prefix) :].strip()
    return entry


def _stalled(ctx: Context, ticket: watch.Ticket, reason: str, entry: str = "") -> Handled:
    path = ticket.path.as_posix()
    if entry:
        ops.edit(ctx, path, entry)
    ops.stall(ctx, path, ticket.branch, reason)
    return Handled(True, f"stage {ticket.stage} of {path} stalled: {reason}")


def _decide(
    ctx: Context, ticket: watch.Ticket, outcome: str, text: str, findings: list[str]
) -> Handled:
    """A kept outcome: ask, send back, or move on once the stage's checks are green."""
    config = ctx.config["stages"].get(ticket.stage, {})
    forward = (config.get("next") or [None])[0]
    if outcome == forward and findings:
        found = "; ".join(findings)
        text += (
            f"\n\nThe format check found what has to change before the story can start: {found}."
        )
        outcome = "question"
    if outcome == "question":
        return _ask(ctx, ticket, text, f"{ticket.stage} asks")
    if outcome != forward and "max_rounds" in config:
        return _rework(ctx, ticket, outcome, text)
    if outcome == forward:
        red, notes = _checks(ctx, config)
        if notes:
            text += "\n\n" + "\n".join(notes)
        if red is not None:
            return _stalled(ctx, ticket, red, text)
    return _move(ctx, ticket, outcome, text)


def _ask(ctx: Context, ticket: watch.Ticket, text: str, what: str) -> Handled:
    path = ticket.path.as_posix()
    ops.edit(ctx, path, text, blocked="question")
    ops.commit_and_push(ctx, ticket.branch, ops.subject(path, what))
    return Handled(True, f"{path} has a question at {ticket.stage}")


def _rework(ctx: Context, ticket: watch.Ticket, outcome: str, text: str) -> Handled:
    """A stage sends the story back: a round, and past `max_rounds` the human decides."""
    path, stage = ticket.path.as_posix(), ticket.stage
    rounds = int(ops.meta(ctx, path).get("round") or 0) + 1
    cap = ops.max_rounds(ctx, stage)
    if rounds > cap:
        sent = f"This story has now been sent back {rounds} times, more than {cap}."
        ops.edit(ctx, path, round=rounds)
        return _ask(ctx, ticket, f"{text}\n\n{sent} {CAP_QUESTION}", f"{stage} asks (round cap)")
    ops.edit(ctx, path, round=rounds)
    return _move(ctx, ticket, outcome, text)


def _checks(ctx: Context, config: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Run the stage's `checks` (must be green) and `records` (any result, noted).
    (Why the move is held, or None; the notes for the entry.)"""
    notes: list[str] = []
    for target in config.get("checks") or []:
        green, tail = ctx.gate(str(target))
        if not green:
            return f"`make {target}` is red after the stage:\n{tail}", notes
        notes.append(f"`make {target}`: {_last_line(tail)}")
    for target in config.get("records") or []:
        _, tail = ctx.gate(str(target))
        notes.append(f"`make {target}`: {_last_line(tail)}")
    return None, notes


def _last_line(text: str) -> str:
    """The output's last line that is not make's own report of a failed recipe."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    own = [line for line in lines if not line.startswith(("make: ***", "make["))]
    return (own or lines or [""])[-1]


def _move(ctx: Context, ticket: watch.Ticket, outcome: str, text: str) -> Handled:
    path, stage = ticket.path.as_posix(), ticket.stage
    ops.edit(ctx, path, text, stage=outcome, blocked=None)
    ops.commit_and_push(ctx, ticket.branch, ops.subject(path, f"{stage} → {outcome}"))
    if ctx.config["stages"].get(outcome, {}).get("gate"):
        _hand_over(ctx, ticket, text)
    return Handled(True, f"{path}: {stage} → {outcome}")


# --- at the human's gate -----------------------------------------------------------------------


def _hand_over(ctx: Context, ticket: watch.Ticket, entry: str) -> None:
    """Write the pull request body from the story and mark it ready for the human."""
    path = ticket.path.as_posix()
    pr = int(ops.meta(ctx, path).get("pr") or 0)
    _, body = story.split(ops.read(ctx, path))
    text = _acceptance_body(body, entry) if ticket.is_acceptance else _story_body(ctx, ticket, body)
    ctx.github.edit_body(pr, text)
    ctx.github.ready(pr)


def _last_by(body: str, who: str) -> str:
    logged = [t for _n, t in story.entries(body) if t.startswith(f"{who}:")]
    return logged[-1] if logged else "none"


def _story_body(ctx: Context, ticket: watch.Ticket, body: str) -> str:
    commits = watch.git(ctx.root, "log", "--oneline", f"origin/{MAIN}..HEAD").strip()
    feature = ctx.root / ticket.path.parent.parent
    live = list((feature / "ongoing").glob("*.md"))
    drafts = list((feature / "drafts").glob("*.md"))
    last = (
        f"This is the last story of {feature.name}; merging completes the feature.\n\n"
        if len(live) == 1 and not drafts
        else ""
    )
    return (
        f"## Assignment\n\n{story.section(body, 'Assignment')}\n\n"
        f"## Acceptance criteria\n\n{story.section(body, 'Acceptance criteria')}\n\n"
        f"## Tests\n\n{_last_by(body, 'tester')}\n\n"
        f"## Review\n\n{_last_by(body, 'reviewer')}\n\n"
        f"## Documentation\n\n{_last_by(body, 'documenter')}\n\n"
        f"## Demo\n\n{_last_by(body, 'demo')}\n\n"
        f"## Commits\n\n```\n{commits}\n```\n\n"
        f"{last}{STORY_CLOSING}"
    )


def _acceptance_body(body: str, entry: str) -> str:
    return (
        f"## Verdict\n\n{story.section(body, 'Verdict')}\n\n"
        f"## Findings in short\n\n{entry}\n\n"
        f"## Proposed stories\n\n{story.section(body, 'Proposed stories')}\n\n"
        f"{ACCEPTANCE_CLOSING}"
    )
