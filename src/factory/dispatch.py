"""What happens for each watcher line, in code: until 2026-10-05 a model did this from a skill.

The tick calls `handle` with the line it got from the watcher. `run` lines start the stage agent
named in the line (through `Context.start`) after bringing its branch up to date; every other
line is bookkeeping on the story and its pull request: archive, discard, refuse, ask, copy an
answer, move an illegal change back, clear a dead run. Each handler ends in at most one commit
and one push, or in nothing at all, and says so in one sentence for the tick log.

The rules for each line are those of `docs/WATCH_CONTRACT.md` and, for what a stage does, of the
stage skills. A situation no handler foresees raises; the tick counts it as a failure, retries,
and reports on the pull request when it gives up.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from factory import agent, costs, github, repo, story, watch

MAIN = "main"
FINISH = "Finish now: commit what you have with a log entry (R2), push, and hand back."


class PullRequests(Protocol):
    def view(self, pr: int) -> github.PullRequest: ...
    def comment(self, pr: int, body: str) -> None: ...
    def reopen(self, pr: int) -> bool: ...
    def to_draft(self, pr: int) -> None: ...


@dataclass(frozen=True)
class Context:
    root: Path
    config: watch.Config
    github: PullRequests
    start: Callable[[str, str], agent.AgentRun]  # (agent name, task message) -> its run
    today: str  # YYYY-MM-DD, for the human's comments and a refusal


@dataclass(frozen=True)
class Handled:
    ok: bool
    summary: str
    run: agent.AgentRun | None = None


NOTHING = Handled(True, "nothing to do")


def handle(ctx: Context, line: str) -> Handled:
    kind, *args = line.split()
    handler = LINES.get(kind)
    return handler(ctx, *args) if handler else NOTHING


# --- the story on disk -------------------------------------------------------------------------


def _ticket(path: str, text: str | None) -> watch.Ticket:
    return watch.Ticket(Path(path), watch.parse_frontmatter(text or ""))


def _subject(path: str, what: str) -> str:
    ticket = watch.Ticket(Path(path), {})
    prefix = (
        f"acceptance {ticket.feature}" if ticket.is_acceptance else f"ticket {ticket.ticket_id}"
    )
    return f"{prefix}: {what}"


def _read(ctx: Context, path: str) -> str:
    return (ctx.root / path).read_text(encoding="utf-8")


def _write(ctx: Context, path: str, text: str) -> None:
    target = ctx.root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")


def _edit(ctx: Context, path: str, *entries: str, **fields: Any) -> None:
    """Set frontmatter fields and append log entries to the story in the working tree."""
    meta, body = story.split(_read(ctx, path))
    meta.pop("claimed_at", None)  # contract version 4 kept the claim here; the run file has it
    meta.update(fields)
    for entry in entries:
        body = story.append(body, entry)
    _write(ctx, path, story.render(meta, body))


def _meta(ctx: Context, path: str) -> dict[str, Any]:
    return watch.parse_frontmatter(_read(ctx, path))


def _max_attempts(ctx: Context) -> int:
    return int(ctx.config.get("max_attempts", 2))


def _max_rounds(ctx: Context, stage: str) -> int:
    return int(ctx.config["stages"].get(stage, {}).get("max_rounds", 2))


def _post(ctx: Context, pr: int, body: str) -> int:
    """Post on the pull request; the number of comments it has afterwards, own post included."""
    ctx.github.comment(pr, body)
    return len(ctx.github.view(pr).comments)


def _commit_and_push(ctx: Context, branch: str, subject: str) -> None:
    repo.commit_all(ctx.root, subject)
    repo.push(ctx.root, branch)


def _to_main(ctx: Context) -> None:
    if not repo.checkout(ctx.root, MAIN):
        raise RuntimeError("main cannot fast-forward to origin/main")


def _to_branch(ctx: Context, branch: str) -> None:
    if not repo.checkout(ctx.root, branch):
        raise RuntimeError(f"{branch} cannot fast-forward to origin/{branch}")


# --- merged and closed -------------------------------------------------------------------------


def merged(ctx: Context, path: str, branch: str) -> Handled:
    """The human merged: book it on main and delete the branch. A story moves to `done/`."""
    _to_main(ctx)
    cost = costs.one_line(ctx.root, path)  # keyed by the path the lines named: before the move
    entry = f"done (pull request merged); {cost}"
    ticket = watch.Ticket(Path(path), {})
    if ticket.is_acceptance:
        _edit(ctx, path, entry, stage="done", outcome="accepted")
    else:
        _edit(ctx, path, entry, stage="done", blocked=None)
        archived = Path(path).parent.parent / "done" / Path(path).name
        (ctx.root / archived).parent.mkdir(parents=True, exist_ok=True)
        watch.git(ctx.root, "mv", path, archived.as_posix())
    _commit_and_push(ctx, MAIN, _subject(path, "accept → done (pull request merged)"))
    repo.delete(ctx.root, branch)
    return Handled(True, f"booked the merge of {path} on main and deleted {branch}")


def closed(ctx: Context, path: str, branch: str) -> Handled:
    if watch.Ticket(Path(path), {}).is_acceptance:
        return _refused(ctx, path, branch)
    current = _ticket(path, repo.show(ctx.root, branch, path))
    if current.stage == "accept":
        return _sent_back(ctx, path, branch, current)
    return _discard(ctx, path, branch)


def _refused(ctx: Context, path: str, branch: str) -> Handled:
    """The human closed the acceptance: the report goes to main as refused, the drafts do not."""
    report = repo.show(ctx.root, branch, path)
    if report is None:
        raise RuntimeError(f"no report at {branch}:{path}")
    pr = int(_ticket(path, report).meta.get("pr") or 0)
    seen = int(_ticket(path, report).meta.get("comments_seen") or 0)
    said = github.human(ctx.github.view(pr).comments[seen:]) if pr else []
    reason = " ".join(c.body.strip() for c in said) or "no reason given"
    _to_main(ctx)
    cost = costs.one_line(ctx.root, path)
    meta, body = story.split(report)
    meta.update(stage="done", outcome="refused")
    meta.pop("claimed_at", None)
    body = story.insert_under(body, "Verdict", f"Refused by the human on {ctx.today}: {reason}")
    body = story.append(body, f"done (pull request closed by the human); {cost}")
    _write(ctx, path, story.render(meta, body))
    _commit_and_push(ctx, MAIN, _subject(path, "closed by the human"))
    repo.delete(ctx.root, branch)
    return Handled(True, f"recorded the refusal of {path} on main and deleted {branch}")


SENT_BACK_QUESTION = (
    "What should happen? 1. Comment what should change; the coder reworks the story with exactly "
    "that. 2. Close the pull request again to discard the story: it goes back to `drafts/` as you "
    "wrote it, and its branch is deleted. 3. If closing was a mistake: mark the pull request ready "
    "for review and merge it, which accepts the story as it is."
)


def _copy_comments(ctx: Context, path: str, pr: int) -> tuple[int, int]:
    """Append every unseen human comment to the log; (comments now, human comments copied)."""
    seen = int(_meta(ctx, path).get("comments_seen") or 0)
    comments = ctx.github.view(pr).comments
    said = github.human(comments[seen:])
    entries = [f"human (pull request comment, {c.date}): {c.body.strip()}" for c in said]
    _edit(ctx, path, *entries, comments_seen=len(comments))
    return len(comments), len(said)


def _reason_given(body: str) -> bool:
    """A human comment after the demo's hand-over is the reason for sending the story back."""
    logged = [text for _n, text in story.entries(body)]
    handover = max((i for i, text in enumerate(logged) if text.startswith("demo")), default=-1)
    return any(text.startswith("human (pull request comment") for text in logged[handover + 1 :])


def _sent_back(ctx: Context, path: str, branch: str, current: watch.Ticket) -> Handled:
    """Closed at `accept`: reopen as a draft, back to `doing`; without a reason, or past the
    round cap, ask what should happen instead of letting the coder guess."""
    pr = int(current.meta.get("pr") or 0)
    if not ctx.github.reopen(pr):
        return Handled(False, f"pull request {pr} could not be reopened; nothing changed")
    ctx.github.to_draft(pr)
    _to_branch(ctx, branch)
    _copy_comments(ctx, path, pr)
    rounds = int(_meta(ctx, path).get("round") or 0) + 1
    _edit(ctx, path, stage="doing", round=rounds)
    cap = _max_rounds(ctx, "demo")
    if _reason_given(story.split(_read(ctx, path))[1]) and rounds <= cap:
        _edit(ctx, path, blocked=None)
        _commit_and_push(ctx, branch, _subject(path, "accept → doing (pull request closed)"))
        return Handled(True, f"sent {path} back to the coder with the human's reason")
    first = (
        "The pull request was closed without a comment."
        if rounds <= cap
        else f"This story has now been sent back {rounds} times, more than {cap}."
    )
    question = f"{first} {SENT_BACK_QUESTION}"
    _edit(ctx, path, question)
    _edit(ctx, path, blocked="asked", comments_seen=_post(ctx, pr, question))
    _commit_and_push(ctx, branch, _subject(path, "accept → doing (pull request closed; asked why)"))
    return Handled(True, f"reopened pull request {pr} and asked what should happen")


def _discard(ctx: Context, path: str, branch: str) -> Handled:
    """Closed before `accept`: the story goes back to `drafts/` as the human wrote it."""
    _to_main(ctx)
    draft = Path(path).parent.parent / "drafts" / Path(path).name
    (ctx.root / draft).parent.mkdir(parents=True, exist_ok=True)
    watch.git(ctx.root, "mv", path, draft.as_posix())
    _commit_and_push(ctx, MAIN, _subject(path, "discarded (pull request closed)"))
    repo.delete(ctx.root, branch)
    return Handled(True, f"discarded {path} to drafts/ and deleted {branch}")


# --- asking and answers ------------------------------------------------------------------------


def _story_branch(ctx: Context, path: str) -> str | None:
    branch = watch.Ticket(Path(path), {}).branch
    return branch if repo.exists(ctx.root, branch) else None


def ask(ctx: Context, path: str) -> Handled:
    """Post the question on the pull request: the agent's last entry, or at the attempts cap
    the last stall and the offer to retry."""
    branch = _story_branch(ctx, path)
    text = repo.show(ctx.root, branch, path) if branch else None
    current = _ticket(path, text)
    pr = int(current.meta.get("pr") or 0)
    if branch is None or not pr:
        return Handled(True, f"question without a pull request on {path}")
    if current.meta.get("blocked") == "asked":
        return NOTHING
    _to_branch(ctx, branch)
    attempts = int(current.meta.get("attempts") or 0)
    last = story.last_entry(story.split(_read(ctx, path))[1])
    if attempts >= _max_attempts(ctx):
        question = (
            f"Stage {current.stage} stalled {attempts} times. The last time: {last} "
            "Comment anything to retry: the attempts go back to 0 and the stage runs again. "
            "Close the pull request to stop instead."
        )
        _edit(ctx, path, question)
    else:
        question = last
    _edit(ctx, path, blocked="asked", comments_seen=_post(ctx, pr, question))
    _commit_and_push(ctx, branch, _subject(path, "question asked on the pull request"))
    return Handled(True, f"asked the question of {path} on pull request {pr}")


def answers(ctx: Context, path: str) -> Handled:
    """Copy the human's new comments into the log. An answer unblocks the story; at the attempts
    cap any answer is a retry."""
    branch = _story_branch(ctx, path)
    if branch is None:
        return Handled(True, f"comments without a branch on {path}")
    current = _ticket(path, repo.show(ctx.root, branch, path))
    pr = int(current.meta.get("pr") or 0)
    seen = int(current.meta.get("comments_seen") or 0)
    if len(ctx.github.view(pr).comments) <= seen:
        return NOTHING
    _to_branch(ctx, branch)
    _, copied = _copy_comments(ctx, path, pr)
    if current.meta.get("blocked") == "asked" and copied:
        retry = (
            {"attempts": 0} if int(current.meta.get("attempts") or 0) >= _max_attempts(ctx) else {}
        )
        _edit(ctx, path, blocked=None, **retry)
    _commit_and_push(ctx, branch, _subject(path, "comments from the pull request"))
    return Handled(True, f"copied {copied} comments of pull request {pr} into {path}")


# --- corrections -------------------------------------------------------------------------------


def reject(ctx: Context, path: str, before: str, after: str) -> Handled:
    """Move an illegal stage change back, on the branch it was made on."""
    branch = repo.current_branch(ctx.root)
    _edit(ctx, path, f"illegal stage change {before} → {after}, moved back", stage=before)
    pr = int(_meta(ctx, path).get("pr") or 0)
    if pr:
        said = (
            f"The stage was changed from {before} to {after}, which `stages.yml` does not allow; "
            f"it is back at {before}."
        )
        _edit(ctx, path, comments_seen=_post(ctx, pr, said))
    _commit_and_push(ctx, branch, _subject(path, f"illegal change {before} → {after}, moved back"))
    return Handled(True, f"moved {path} back to {before}")


def expired(ctx: Context, path: str) -> Handled:
    """The run that held the story is gone (lease over, or the machine restarted)."""
    watch.clear_running(ctx.root)
    branch = _story_branch(ctx, path)
    if branch is None:
        raise RuntimeError(f"a run on {path} without a branch")
    _to_branch(ctx, branch)
    meta = _meta(ctx, path)
    attempts = int(meta.get("attempts") or 0) + 1
    _edit(
        ctx,
        path,
        "run expired: the run that held it ended without finishing (lease over or machine "
        "restarted)",
        attempts=attempts,
    )
    pr = int(meta.get("pr") or 0)
    if pr:
        said = (
            f"Stage {meta.get('stage')} stalled: its run ended without finishing "
            f"(attempt {attempts} of {_max_attempts(ctx)}). Retrying."
        )
        _edit(ctx, path, comments_seen=_post(ctx, pr, said))
    _commit_and_push(ctx, branch, _subject(path, "run expired"))
    return Handled(True, f"cleared the expired run on {path}")


# --- run ---------------------------------------------------------------------------------------


def _stall(ctx: Context, path: str, branch: str, reason: str) -> None:
    """The stage ended without a stage change or a question: count it, say why, commit what is
    there. The watcher decides what comes next; at `max_attempts` it asks the human."""
    meta = _meta(ctx, path)
    stage = str(meta.get("stage") or "ready")
    attempts = int(meta.get("attempts") or 0) + 1
    _edit(
        ctx,
        path,
        f"stage {stage} stalled: {reason}; partial work committed",
        attempts=attempts,
    )
    pr = int(meta.get("pr") or 0)
    if pr:
        said = (
            f"Stage {stage} stalled (attempt {attempts} of {_max_attempts(ctx)}): {reason}. "
            "Retrying on the next tick."
        )
        _edit(ctx, path, comments_seen=_post(ctx, pr, said))
    _commit_and_push(ctx, branch, _subject(path, f"{stage} stalled"))


def _prepare(ctx: Context, current: watch.Ticket, where: str) -> tuple[str, str | None]:
    """Check out where the agent starts. (The task's `Branch:` line, a stall reason or None.)"""
    path, branch = current.path.as_posix(), current.branch
    if where == MAIN and not repo.exists(ctx.root, branch):
        _to_main(ctx)
        return f"main; create {branch}", None
    if not repo.checkout(ctx.root, branch):
        return branch, f"{branch} cannot fast-forward to origin/{branch}"
    if not repo.merge_main(ctx.root, _subject(path, "merge main")):
        return branch, "merging main conflicts; merge aborted"
    if where == MAIN:
        why = "; intake asked before" if current.stage == "ready" else ""
        return f"{branch} (exists{why})", None
    return branch, None


def _task(ctx: Context, current: watch.Ticket, branch_line: str, findings: list[str]) -> str:
    stage = ctx.config["stages"].get(current.stage, {})
    pr = current.meta.get("pr")
    checked = ""
    if current.stage == "ready":
        listed = " ".join(f"{n}. {f}." for n, f in enumerate(findings, start=1))
        checked = f"Format check found: {listed}\n" if findings else "Format check: passed\n"
    return (
        f"Ticket: {current.path.as_posix()}\n"
        f"Id: {current.ticket_id}\n"
        f"Stage: {current.stage}\n"
        f"Allowed next stages: {', '.join(stage.get('next') or [])}\n"
        f"Branch: {branch_line}\n"
        f"Pull request: {pr or 'none yet'}\n"
        f"{checked}"
        "Follow your preloaded stage skill. End with a pushed commit that contains the ticket file."
    )


def _refuse_format(ctx: Context, path: str, findings: list[str]) -> str:
    """Intake moved on although the story's form is wrong: back to `ready`, and the findings are
    the question. Code checks the form; no model can accept a story past it."""
    entry = "format check: the story cannot start until its form is right: " + "; ".join(findings)
    _edit(ctx, path, entry + ".", stage="ready", blocked="question")
    subject = _subject(path, "ready → tests refused by the format check, moved back")
    _commit_and_push(ctx, watch.Ticket(Path(path), {}).branch, subject)
    return f"the format check refused {path}: {'; '.join(findings)}"


def _progressed(before: watch.Ticket, after: dict[str, Any]) -> bool:
    """A stage run ends in a stage change or a question; anything else is a stall."""
    return str(after.get("stage") or "ready") != before.stage or after.get("blocked") == "question"


def _reason(result: agent.AgentRun) -> str:
    parts = [result.reason or "the agent ended without a stage change or a question"]
    parts += [f"denied: {d}" for d in result.denials[:1]]
    return "; ".join(parts)


def _current(ctx: Context, path: str) -> tuple[watch.Ticket, str]:
    """The story as the line saw it: from its branch, else from `origin/main`; and the branch."""
    branch = watch.Ticket(Path(path), {}).branch
    if repo.exists(ctx.root, branch):
        text = repo.show(ctx.root, branch, path)
    else:  # the line was evaluated against origin/main
        text = repo.show_ref(ctx.root, f"origin/{MAIN}", path)
    current = _ticket(path, text)
    if text is None and current.is_acceptance:  # due, and the acceptor writes the report
        current = watch.Ticket(Path(path), {"stage": watch.FEATURE_STAGE})
    return current, branch


def _decided_on_github(ctx: Context, current: watch.Ticket) -> Handled | None:
    """The watcher reads a pull request only while the human is expected to act; a close or a
    merge while the stages work shows up here, before the next agent starts."""
    pr = int(current.meta.get("pr") or 0)
    state = ctx.github.view(pr).state if pr else "OPEN"
    path = current.path.as_posix()
    if state == "CLOSED":
        return closed(ctx, path, current.branch)
    if state == "MERGED":
        return merged(ctx, path, current.branch)
    return None


def run(ctx: Context, name: str, path: str, where: str) -> Handled:
    """Bring the story's branch up to date, start the agent, and count a run that made no
    progress as a stall."""
    current, branch = _current(ctx, path)
    if ctx.config["stages"].get(current.stage, {}).get("agent") != name:
        return NOTHING
    decided = _decided_on_github(ctx, current)
    if decided is not None:
        return decided
    branch_line, blocked = _prepare(ctx, current, where)
    if blocked is not None:
        _stall(ctx, path, branch, blocked)
        return Handled(True, f"stage {current.stage} of {path} stalled: {blocked}")
    findings = story.check_file(ctx.root, Path(path)) if current.stage == "ready" else []
    started_at = repo.head(ctx.root)
    watch.write_running(ctx.root, watch.Running(path, datetime.now(UTC)))
    try:
        result = ctx.start(name, _task(ctx, current, branch_line, findings))
    finally:
        watch.clear_running(ctx.root)
    return _after_run(ctx, current, findings, result, started_at)


def _after_run(
    ctx: Context,
    current: watch.Ticket,
    findings: list[str],
    result: agent.AgentRun,
    started_at: str,
) -> Handled:
    """Judge the run by what is on the branch now: a stage change or a question is progress;
    anything else, whatever the agent said, is a stall."""
    path, branch = current.path.as_posix(), current.branch
    if repo.current_branch(ctx.root) != branch:
        wrong = "; it committed on the wrong branch" if repo.head(ctx.root) != started_at else ""
        summary = f"the agent stalled before {branch} existed: {_reason(result)}{wrong}"
        return Handled(False, summary, result)
    after = _meta(ctx, path) if (ctx.root / path).is_file() else {}
    if not (result.ok and _progressed(current, after)):
        _stall(ctx, path, branch, _reason(result))
        return Handled(True, f"stage {current.stage} of {path} stalled: {_reason(result)}", result)
    if findings and after.get("stage") != current.stage:
        return Handled(True, _refuse_format(ctx, path, findings), result)
    return Handled(True, f"{path} moved on: {result.result[:200]}", result)


def _duplicate(_ctx: Context, story_id: str, first: str, second: str) -> Handled:
    return Handled(True, f"two stories with id {story_id}: {first} and {second}")


def _pr_lookup(_ctx: Context, *args: str) -> Handled:
    return Handled(True, f"gh could not answer for {args[-1]}; is gh logged in?")


LINES: dict[str, Callable[..., Handled]] = {
    "run": run,
    "merged": merged,
    "closed": closed,
    "ask": ask,
    "pr": lambda ctx, path, *_state: answers(ctx, path),
    "reject": reject,
    "expired": expired,
    "duplicate": _duplicate,
    "error": _pr_lookup,
}
