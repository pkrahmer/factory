"""What the line handlers share: the context they work in, and the steps they take on a story.

A story is edited only in the working tree of the branch it lives on and committed by the
handler that edited it; `edit` keeps the frontmatter in its fixed order and appends log entries
as the next number. The frontmatter is the dispatcher's alone: agents never write it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from factory import agent, github, repo, story, watch

MAIN = "main"


class PullRequests(Protocol):
    def view(self, pr: int) -> github.PullRequest: ...
    def comment(self, pr: int, body: str) -> None: ...
    def reopen(self, pr: int) -> bool: ...
    def to_draft(self, pr: int) -> None: ...
    def create_draft(self, head: str, title: str, body: str) -> int: ...
    def find(self, head: str) -> int | None: ...
    def edit_body(self, pr: int, body: str) -> None: ...
    def ready(self, pr: int) -> None: ...


Start = Callable[[str, str, dict[str, Any]], agent.AgentRun]  # (agent, task, outcome schema)
Gate = Callable[[str], tuple[bool, str]]  # make target -> (green, the output's tail)


@dataclass(frozen=True)
class Context:
    root: Path
    config: watch.Config
    github: PullRequests
    start: Start
    today: str  # YYYY-MM-DD, for the human's comments and a refusal
    gate: Gate


@dataclass(frozen=True)
class Handled:
    ok: bool
    summary: str
    run: agent.AgentRun | None = None


NOTHING = Handled(True, "nothing to do")


def ticket_of(path: str, text: str | None) -> watch.Ticket:
    return watch.Ticket(Path(path), watch.parse_frontmatter(text or ""))


def subject(path: str, what: str) -> str:
    ticket = watch.Ticket(Path(path), {})
    prefix = (
        f"acceptance {ticket.feature}" if ticket.is_acceptance else f"ticket {ticket.ticket_id}"
    )
    return f"{prefix}: {what}"


def read(ctx: Context, path: str) -> str:
    return (ctx.root / path).read_text(encoding="utf-8")


def write(ctx: Context, path: str, text: str) -> None:
    target = ctx.root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")


def edit(ctx: Context, path: str, *entries: str, **fields: Any) -> None:
    """Set frontmatter fields and append log entries to the story in the working tree."""
    meta, body = story.split(read(ctx, path))
    meta.pop("claimed_at", None)  # contract version 4 kept the claim here; the run file has it
    meta.update(fields)
    for entry in entries:
        body = story.append(body, entry)
    write(ctx, path, story.render(meta, body))


def meta(ctx: Context, path: str) -> dict[str, Any]:
    return watch.parse_frontmatter(read(ctx, path))


def max_attempts(ctx: Context) -> int:
    return int(ctx.config.get("max_attempts", 2))


def max_rounds(ctx: Context, stage: str) -> int:
    return int(ctx.config["stages"].get(stage, {}).get("max_rounds", 2))


def post(ctx: Context, pr: int, body: str) -> int:
    """Post on the pull request; the number of comments it has afterwards, own post included."""
    ctx.github.comment(pr, body)
    return len(ctx.github.view(pr).comments)


def commit_and_push(ctx: Context, branch: str, what: str) -> None:
    repo.commit_all(ctx.root, what)
    repo.push(ctx.root, branch)


def to_main(ctx: Context) -> None:
    if not repo.checkout(ctx.root, MAIN):
        raise RuntimeError("main cannot fast-forward to origin/main")


def to_branch(ctx: Context, branch: str) -> None:
    if not repo.checkout(ctx.root, branch):
        raise RuntimeError(f"{branch} cannot fast-forward to origin/{branch}")


def story_branch(ctx: Context, path: str) -> str | None:
    branch = watch.Ticket(Path(path), {}).branch
    return branch if repo.exists(ctx.root, branch) else None


def stall(ctx: Context, path: str, branch: str, reason: str) -> None:
    """The stage ended without an outcome it could keep: count it, say why, commit what is there.
    The watcher decides what comes next; at `max_attempts` it asks the human."""
    current = meta(ctx, path)
    stage = str(current.get("stage") or "ready")
    attempts = int(current.get("attempts") or 0) + 1
    edit(ctx, path, f"stage {stage} stalled: {reason}; partial work committed", attempts=attempts)
    pr = int(current.get("pr") or 0)
    if pr:
        said = (
            f"Stage {stage} stalled (attempt {attempts} of {max_attempts(ctx)}): {reason}. "
            "Retrying on the next tick."
        )
        edit(ctx, path, comments_seen=post(ctx, pr, said))
    commit_and_push(ctx, branch, subject(path, f"{stage} stalled"))
