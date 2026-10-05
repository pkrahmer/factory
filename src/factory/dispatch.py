"""What happens for each watcher line, in code: until 2026-10-05 a model did this from a skill.

The tick calls `handle` with the line it got from the watcher. A `run` line goes to
`factory.stage`, which starts the stage agent and applies its outcome; every other line is
bookkeeping on the story and its pull request: archive, discard, refuse, ask, copy an answer,
move an illegal change back, clear a dead run. Each handler ends in at most one commit and one
push, or in nothing at all, and says so in one sentence for the tick log.

The rules for each line are those of `docs/WATCH_CONTRACT.md`. A situation no handler foresees
raises; the tick counts it as a failure, retries, and reports on the pull request when it gives
up.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from factory import costs, github, ops, repo, stage, story, watch
from factory.ops import MAIN, NOTHING, Context, Handled

__all__ = ["Context", "Handled", "handle"]


def handle(ctx: Context, line: str) -> Handled:
    kind, *args = line.split()
    handler = LINES.get(kind)
    return handler(ctx, *args) if handler else NOTHING


# --- merged and closed -------------------------------------------------------------------------


def merged(ctx: Context, path: str, branch: str) -> Handled:
    """The human merged: book it on main and delete the branch. A story moves to `done/`."""
    ops.to_main(ctx)
    cost = costs.one_line(ctx.root, path)  # keyed by the path the lines named: before the move
    entry = f"done (pull request merged); {cost}"
    if watch.Ticket(Path(path), {}).is_acceptance:
        ops.edit(ctx, path, entry, stage="done", outcome="accepted")
    else:
        ops.edit(ctx, path, entry, stage="done", blocked=None)
        archived = Path(path).parent.parent / "done" / Path(path).name
        (ctx.root / archived).parent.mkdir(parents=True, exist_ok=True)
        watch.git(ctx.root, "mv", path, archived.as_posix())
    ops.commit_and_push(ctx, MAIN, ops.subject(path, "accept → done (pull request merged)"))
    repo.delete(ctx.root, branch)
    return Handled(True, f"booked the merge of {path} on main and deleted {branch}")


def closed(ctx: Context, path: str, branch: str) -> Handled:
    if watch.Ticket(Path(path), {}).is_acceptance:
        return _refused(ctx, path, branch)
    current = ops.ticket_of(path, repo.show(ctx.root, branch, path))
    if current.stage == "accept":
        return _sent_back(ctx, path, branch, current)
    return _discard(ctx, path, branch)


def _refused(ctx: Context, path: str, branch: str) -> Handled:
    """The human closed the acceptance: the report goes to main as refused, the drafts do not."""
    report = repo.show(ctx.root, branch, path)
    if report is None:
        raise RuntimeError(f"no report at {branch}:{path}")
    pr = int(ops.ticket_of(path, report).meta.get("pr") or 0)
    seen = int(ops.ticket_of(path, report).meta.get("comments_seen") or 0)
    said = github.human(ctx.github.view(pr).comments[seen:]) if pr else []
    reason = " ".join(c.body.strip() for c in said) or "no reason given"
    ops.to_main(ctx)
    cost = costs.one_line(ctx.root, path)
    meta, body = story.split(report)
    meta.update(stage="done", outcome="refused")
    meta.pop("claimed_at", None)
    body = story.insert_under(body, "Verdict", f"Refused by the human on {ctx.today}: {reason}")
    body = story.append(body, f"done (pull request closed by the human); {cost}")
    ops.write(ctx, path, story.render(meta, body))
    ops.commit_and_push(ctx, MAIN, ops.subject(path, "closed by the human"))
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
    seen = int(ops.meta(ctx, path).get("comments_seen") or 0)
    comments = ctx.github.view(pr).comments
    said = github.human(comments[seen:])
    entries = [f"human (pull request comment, {c.date}): {c.body.strip()}" for c in said]
    ops.edit(ctx, path, *entries, comments_seen=len(comments))
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
    ops.to_branch(ctx, branch)
    _copy_comments(ctx, path, pr)
    rounds = int(ops.meta(ctx, path).get("round") or 0) + 1
    ops.edit(ctx, path, stage="doing", round=rounds)
    cap = ops.max_rounds(ctx, "demo")
    if _reason_given(story.split(ops.read(ctx, path))[1]) and rounds <= cap:
        ops.edit(ctx, path, blocked=None)
        ops.commit_and_push(ctx, branch, ops.subject(path, "accept → doing (pull request closed)"))
        return Handled(True, f"sent {path} back to the coder with the human's reason")
    first = (
        "The pull request was closed without a comment."
        if rounds <= cap
        else f"This story has now been sent back {rounds} times, more than {cap}."
    )
    question = f"{first} {SENT_BACK_QUESTION}"
    ops.edit(ctx, path, question)
    ops.edit(ctx, path, blocked="asked", comments_seen=ops.post(ctx, pr, question))
    what = "accept → doing (pull request closed; asked why)"
    ops.commit_and_push(ctx, branch, ops.subject(path, what))
    return Handled(True, f"reopened pull request {pr} and asked what should happen")


def _discard(ctx: Context, path: str, branch: str) -> Handled:
    """Closed before `accept`: the story goes back to `drafts/` as the human wrote it."""
    ops.to_main(ctx)
    draft = Path(path).parent.parent / "drafts" / Path(path).name
    (ctx.root / draft).parent.mkdir(parents=True, exist_ok=True)
    watch.git(ctx.root, "mv", path, draft.as_posix())
    ops.commit_and_push(ctx, MAIN, ops.subject(path, "discarded (pull request closed)"))
    repo.delete(ctx.root, branch)
    return Handled(True, f"discarded {path} to drafts/ and deleted {branch}")


# --- asking and answers ------------------------------------------------------------------------


def ask(ctx: Context, path: str) -> Handled:
    """Post the question on the pull request: the agent's last entry, or at the attempts cap
    the last stall and the offer to retry."""
    branch = ops.story_branch(ctx, path)
    text = repo.show(ctx.root, branch, path) if branch else None
    current = ops.ticket_of(path, text)
    pr = int(current.meta.get("pr") or 0)
    if branch is None or not pr:
        return Handled(True, f"question without a pull request on {path}")
    if current.meta.get("blocked") == "asked":
        return NOTHING
    ops.to_branch(ctx, branch)
    attempts = int(current.meta.get("attempts") or 0)
    last = story.last_entry(story.split(ops.read(ctx, path))[1])
    if attempts >= ops.max_attempts(ctx):
        question = (
            f"Stage {current.stage} stalled {attempts} times. The last time: {last} "
            "Comment anything to retry: the attempts go back to 0 and the stage runs again. "
            "Close the pull request to stop instead."
        )
        ops.edit(ctx, path, question)
    else:
        question = last
    ops.edit(ctx, path, blocked="asked", comments_seen=ops.post(ctx, pr, question))
    ops.commit_and_push(ctx, branch, ops.subject(path, "question asked on the pull request"))
    return Handled(True, f"asked the question of {path} on pull request {pr}")


def answers(ctx: Context, path: str) -> Handled:
    """Copy the human's new comments into the log. An answer unblocks the story; at the attempts
    cap any answer is a retry."""
    branch = ops.story_branch(ctx, path)
    if branch is None:
        return Handled(True, f"comments without a branch on {path}")
    current = ops.ticket_of(path, repo.show(ctx.root, branch, path))
    pr = int(current.meta.get("pr") or 0)
    seen = int(current.meta.get("comments_seen") or 0)
    if len(ctx.github.view(pr).comments) <= seen:
        return NOTHING
    ops.to_branch(ctx, branch)
    _, copied = _copy_comments(ctx, path, pr)
    if current.meta.get("blocked") == "asked" and copied:
        capped = int(current.meta.get("attempts") or 0) >= ops.max_attempts(ctx)
        ops.edit(ctx, path, blocked=None, **({"attempts": 0} if capped else {}))
    ops.commit_and_push(ctx, branch, ops.subject(path, "comments from the pull request"))
    return Handled(True, f"copied {copied} comments of pull request {pr} into {path}")


# --- corrections -------------------------------------------------------------------------------


def reject(ctx: Context, path: str, before: str, after: str) -> Handled:
    """Move an illegal stage change back, on the branch it was made on."""
    branch = repo.current_branch(ctx.root)
    ops.edit(ctx, path, f"illegal stage change {before} → {after}, moved back", stage=before)
    pr = int(ops.meta(ctx, path).get("pr") or 0)
    if pr:
        said = (
            f"The stage was changed from {before} to {after}, which `stages.yml` does not allow; "
            f"it is back at {before}."
        )
        ops.edit(ctx, path, comments_seen=ops.post(ctx, pr, said))
    what = f"illegal change {before} → {after}, moved back"
    ops.commit_and_push(ctx, branch, ops.subject(path, what))
    return Handled(True, f"moved {path} back to {before}")


def expired(ctx: Context, path: str) -> Handled:
    """The run that held the story is gone (lease over, or the machine restarted)."""
    watch.clear_running(ctx.root)
    branch = ops.story_branch(ctx, path)
    if branch is None:
        raise RuntimeError(f"a run on {path} without a branch")
    ops.to_branch(ctx, branch)
    current = ops.meta(ctx, path)
    attempts = int(current.get("attempts") or 0) + 1
    ops.edit(
        ctx,
        path,
        "run expired: the run that held it ended without finishing (lease over or machine "
        "restarted)",
        attempts=attempts,
    )
    pr = int(current.get("pr") or 0)
    if pr:
        said = (
            f"Stage {current.get('stage')} stalled: its run ended without finishing "
            f"(attempt {attempts} of {ops.max_attempts(ctx)}). Retrying."
        )
        ops.edit(ctx, path, comments_seen=ops.post(ctx, pr, said))
    ops.commit_and_push(ctx, branch, ops.subject(path, "run expired"))
    return Handled(True, f"cleared the expired run on {path}")


# --- run ---------------------------------------------------------------------------------------


def run(ctx: Context, name: str, path: str, where: str) -> Handled:
    """A stage is due. The watcher reads a pull request only while the human is expected to act,
    so a close or a merge while the stages work shows up here, before the next agent starts."""
    current, _branch = stage.current(ctx, path)
    if ctx.config["stages"].get(current.stage, {}).get("agent") != name:
        return NOTHING
    pr = int(current.meta.get("pr") or 0)
    state = ctx.github.view(pr).state if pr else "OPEN"
    if state == "CLOSED":
        return closed(ctx, path, current.branch)
    if state == "MERGED":
        return merged(ctx, path, current.branch)
    return stage.run(ctx, name, current, where)


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
