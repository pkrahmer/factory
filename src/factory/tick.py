"""One tick of the delivery loop, for a scheduler that runs it every couple of minutes.

A tick evaluates the repository with the watcher and decides whether the line it got
needs the dispatcher. `idle` and `busy` never do; `pr … OPEN n` only when `n` exceeds
the ticket's `comments_seen` and one of the unseen comments is not the tick's own; every
other line only when it, or `HEAD`, differs from what the previous tick handled. Only then
is a model started: `claude -p "/factory <line>"`, headless, which handles that one line
and exits. Tokens are spent on events, not on time.

State lives next to the repository's own, under `.git/`: a lock while a tick runs, the
last handled (line, HEAD) pair with a failure count, a preflight stamp, and a log.

Exit codes: 0 nothing to do, DISPATCHED (3) the dispatcher ran and changed the repository —
evaluate again right away, the next stage is probably due — and 1 for a failure.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from factory import costs, preflight, watch

# Consecutive dispatcher failures on one (line, HEAD) before the tick gives up on it.
MAX_FAILURES = 3
DISPATCHED = 3  # exit code: something happened, do not wait for the next interval
PREFLIGHT_EVERY_HOURS = 24
MAX_TURNS = 80
# The pipeline's own pull request posts (the tick's cost table, the agents' replies) start with
# this; the dispatcher never copies them into a story.
OWN_PREFIX = "factory:"
GATE = "accept"  # the human's stage, where a change request sends a story back to the coder
# Lines whose handling always ends in a commit. A run that reports success on one of them but
# moved no branch did not handle it, and the tick would otherwise remember it as handled.
MUST_COMMIT = ("expired", "merged", "closed", "reject")


@dataclass(frozen=True)
class Memo:
    line: str = ""
    head: str = ""
    failures: int = 0


def git_dir(root: Path) -> Path:
    return Path(watch.git(root, "rev-parse", "--absolute-git-dir").strip())


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- decisions (pure) ---------------------------------------------------------


def needs_model(line: str, memo: Memo, head: str, tickets: list[watch.Ticket]) -> bool:
    """Whether this line, in this repository state, needs the dispatcher."""
    parts = line.split()
    kind = parts[0]
    if kind in ("idle", "busy"):
        return False
    if kind == "pr":
        ticket = _ticket(tickets, parts[1])
        seen = int(ticket.meta.get("comments_seen") or 0) if ticket else 0
        if int(parts[3]) > seen:
            return True
        if not changes_requested(line, tickets):
            return False
        # A change request may come without a word; it is handled once, like any other line.
    if (line, head) == (memo.line, memo.head):
        # Seen before: handled (no retry), failed (retry), or given up (the pull request knows).
        return 0 < memo.failures < MAX_FAILURES
    return True


def _ticket(tickets: list[watch.Ticket], path: str) -> watch.Ticket | None:
    return next((t for t in tickets if t.path.as_posix() == path), None)


def changes_requested(line: str, tickets: list[watch.Ticket]) -> bool:
    """A `pr` line on which the human requested changes to a story at the gate: the rework
    path. An acceptance has no rework; its review means nothing to the pipeline."""
    parts = line.split()
    if parts[0] != "pr" or parts[-1] != watch.CHANGES_REQUESTED:
        return False
    ticket = _ticket(tickets, parts[1])
    return ticket is not None and ticket.stage == GATE and not ticket.is_acceptance


def unseen_are_own(bodies: list[str], seen: int) -> bool:
    """Whether the writings after the first `seen` are all the pipeline's own (and there are
    some)."""
    unseen = bodies[seen:]
    return bool(unseen) and all(body.startswith(OWN_PREFIX) for body in unseen)


def outlived_claim(line: str, tickets: list[watch.Ticket], started: datetime | None) -> str:
    """`busy` for a claim made before this machine started is `expired`. No run survives a
    restart, so nobody holds that claim; waiting out the lease would idle the story for up to
    an hour after every restart. Any other line, or no known start, is returned as it is."""
    parts = line.split()
    if started is None or parts[0] != "busy":
        return line
    ticket = next((t for t in tickets if t.path.as_posix() == parts[1]), None)
    if ticket is None or not ticket.claimed:
        return line
    claimed = watch.parse_timestamp(str(ticket.meta["claimed_at"]))
    return f"expired {parts[1]}" if claimed < started else line


def machine_started() -> datetime | None:
    """When the container started its loop (`FACTORY_STARTED_AT`, set by the entrypoint)."""
    value = os.environ.get("FACTORY_STARTED_AT")
    try:
        return watch.parse_timestamp(value) if value else None
    except ValueError:
        return None


def lock_is_stale(written: float, now: float, lease_minutes: int) -> bool:
    return now - written > (lease_minutes + 10) * 60


def claude_command(claude: str, line: str, model: str) -> list[str]:
    return [
        claude,
        "-p",
        f"/factory {line}",
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "--model",
        model,
        "--output-format",
        "json",
        "--max-turns",
        str(MAX_TURNS),
    ]


# --- state under .git ---------------------------------------------------------


def read_memo(root: Path) -> Memo:
    try:
        return Memo(**json.loads((git_dir(root) / "factory-tick.json").read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return Memo()


def write_memo(root: Path, memo: Memo) -> None:
    (git_dir(root) / "factory-tick.json").write_text(json.dumps(asdict(memo)), encoding="utf-8")


def log(root: Path, message: str) -> None:
    line = f"{now_iso()} {message}"
    print(line, flush=True)
    with (git_dir(root) / "factory-tick.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def acquire_lock(root: Path, lease_minutes: int) -> bool:
    """One tick at a time. A lock older than the lease plus a margin belongs to a dead tick."""
    lock = git_dir(root) / "factory-tick.lock"
    if lock.exists():
        try:
            written = float(lock.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            written = 0.0
        if not lock_is_stale(written, time.time(), lease_minutes):
            return False
        lock.unlink(missing_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as fh:
            fh.write(str(time.time()))
    except FileExistsError:
        return False
    return True


def release_lock(root: Path) -> None:
    (git_dir(root) / "factory-tick.lock").unlink(missing_ok=True)


def recover_dirty_tree(root: Path) -> bool:
    """An interrupted run (container restart, killed process) leaves an agent's edits behind.
    On a ticket branch they are committed as they are, so the record is complete and the
    loop can go on; the claim stays and the lease decides when the stage is retried.
    On main nothing is committed: that is not a situation the loop creates."""
    branch = watch.git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if not branch.startswith(("ticket/", "acceptance/")):
        return False
    name = branch.split("/", 1)[1]
    match = watch.ID_PATTERN.match(name)
    ticket_id = match.group(1) if match else name
    watch.git(root, "add", "-A")
    watch.git(
        root,
        "commit",
        "-q",
        "-m",
        f"ticket {ticket_id}: work left uncommitted by an interrupted run",
    )
    subprocess.run(["git", "push", "-q"], cwd=root, check=False, capture_output=True)
    log(root, f"committed leftovers of an interrupted run on {branch}")
    return True


def sync_main(root: Path) -> None:
    """On main, fast-forward to origin/main: a ticket committed there must be in the working
    tree before the dispatcher looks for it. On a ticket branch nothing moves; the dispatcher
    merges main in when it starts the next stage."""
    branch = watch.git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch != "main" or watch.main_ref(root) is None:
        return
    before = watch.git(root, "rev-parse", "HEAD").strip()
    args = ["git", "merge", "-q", "--ff-only", watch.MAIN_REF]
    result = subprocess.run(args, cwd=root, check=False, capture_output=True, encoding="utf-8")
    if result.returncode != 0:
        log(root, f"main could not fast-forward to origin/main: {result.stderr.strip()[:200]}")
    elif watch.git(root, "rev-parse", "HEAD").strip() != before:
        log(root, "main fast-forwarded to origin/main")


def fetch(root: Path) -> None:
    """New tickets land on main and answers on branches; the tick, not the watcher, fetches."""
    subprocess.run(
        ["git", "fetch", "-q", "--prune", "origin"], cwd=root, check=False, capture_output=True
    )


def preflight_stamp_value(root: Path) -> str:
    """What a passed preflight vouches for: this factory version against this `stages.yml`.
    The stamp lives in the checkout's `.git`, which outlives an image rebuild, so the version
    is part of it; a new image or a changed stage table means a new preflight."""
    try:
        version = importlib.metadata.version("factory")
    except importlib.metadata.PackageNotFoundError:
        version = "dev"
    try:
        config = (root / "factory" / "stages.yml").read_bytes()
    except OSError:
        config = b""
    return f"{version} {hashlib.sha256(config).hexdigest()[:12]}"


def preflight_ok(root: Path) -> bool:
    """Run the preflight once a day, and again whenever the factory or the stage table changed;
    its failures go to the log, there is nobody to ask."""
    stamp = git_dir(root) / "factory-preflight-ok"
    value = preflight_stamp_value(root)
    fresh = stamp.exists() and time.time() - stamp.stat().st_mtime < PREFLIGHT_EVERY_HOURS * 3600
    if fresh and stamp.read_text(encoding="utf-8").strip() == value:
        return True
    checks = preflight.evaluate(sys.platform, shutil.which, preflight.run, root=root)
    missing = [c.line() for c in checks if not c.ok]
    if missing:
        log(root, "preflight failed: " + "; ".join(missing))
        return False
    stamp.write_text(value + "\n", encoding="utf-8")
    return True


# --- the tick -----------------------------------------------------------------


def run_dispatcher(root: Path, claude: str, line: str, model: str) -> tuple[bool, str]:
    """Start the headless dispatcher for one line. Returns (ok, one-line summary) and
    records the run — turns, seconds, tokens, dollars — for `factory.costs`."""
    started = time.time()
    proc = subprocess.run(
        claude_command(claude, line, model),
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    seconds = int(time.time() - started)
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["no output"]
        record(root, line, ok=False, seconds=seconds)
        return False, f"claude exit {proc.returncode} after {seconds}s: {tail[0][:200]}"
    ok = proc.returncode == 0 and not data.get("is_error")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    fields = {
        "turns": int(data.get("num_turns") or 0),
        "cost": float(data.get("total_cost_usd") or 0),
        "input": int(usage.get("input_tokens") or 0),
        "cache_read": int(usage.get("cache_read_input_tokens") or 0),
        "cache_write": int(usage.get("cache_creation_input_tokens") or 0),
        "output": int(usage.get("output_tokens") or 0),
    }
    record(root, line, ok=ok, seconds=seconds, **fields)
    summary = (
        f"turns={fields['turns']} cost=${fields['cost']:.2f} seconds={seconds} "
        f"tokens={fields['input'] + fields['cache_write']}+{fields['cache_read']}cached/"
        f"{fields['output']}out result={str(data.get('result', ''))[:200]!r}"
    )
    return ok, summary


def record(root: Path, line: str, *, ok: bool, seconds: int, **fields: float) -> None:
    """One JSON line per dispatcher run; `factory.costs` sums them per ticket and stage."""
    entry = {"time": now_iso(), "line": line, "ok": ok, "seconds": seconds, **fields}
    with (git_dir(root) / costs.RECORDS).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def tell_cost_when_ready(root: Path, line: str) -> None:
    """After a run that left the story at the gate (its stage has no agent, the human leaves
    it by merging), put the bill on the pull request, prefixed `factory:` so the dispatcher
    never mistakes it for an answer."""
    if not line.startswith("run "):
        return
    path = costs.ticket_of(line)
    config = watch.load_config(root)
    ticket = next((t for t in watch.scan_tickets(root, config) if t.path.as_posix() == path), None)
    if ticket is None or not ticket.meta.get("pr"):
        return
    if config["stages"].get(ticket.stage, {}).get("gate") is None:
        return
    body = f"factory: cost of this ticket so far\n\n{costs.table(root, str(path))}"
    args = ["gh", "pr", "comment", str(ticket.meta["pr"]), "--body", body]
    subprocess.run(args, cwd=root, check=False, capture_output=True)
    log(root, f"posted the cost table on pull request {ticket.meta['pr']}")


def tick(root: Path, claude: str, model: str, *, dry_run: bool = False) -> int:
    config = watch.load_config(root)
    if not acquire_lock(root, int(config["lease_minutes"])):
        return 0  # a tick is still running; the scheduler will come back
    try:
        if not preflight_ok(root):
            return 1
        if watch.git(root, "status", "--porcelain").strip() and not recover_dirty_tree(root):
            log(
                root, "working tree is dirty on main; a human needs to look before the loop goes on"
            )
            return 1
        fetch(root)
        sync_main(root)
        tickets = watch.scan_tickets(root, config)
        line = outlived_claim(watch.evaluate_repo(root), tickets, machine_started())
        head = watch.git(root, "rev-parse", "HEAD").strip()
        memo = read_memo(root)
        if not needs_model(line, memo, head, tickets) or only_own_comments(root, line, tickets):
            return 0
        if dry_run:
            log(root, f"would dispatch: {line}")
            return 0
        return dispatch(root, (claude, model), line, head, memo)
    finally:
        release_lock(root)


def dispatch(root: Path, runner: tuple[str, str], line: str, head: str, memo: Memo) -> int:
    """Start the dispatcher (claude binary, model) for the line and record how it went."""
    claude, model = runner
    log(root, f"dispatch: {line}")
    before = branch_tips(root)
    ok, summary = run_dispatcher(root, claude, line, model)
    if ok and line.split(maxsplit=1)[0] in MUST_COMMIT and branch_tips(root) == before:
        ok, summary = False, f"no commit for a line that needs one; {summary}"
    if ok:
        write_memo(root, Memo(line=line, head=head, failures=0))
        log(root, f"done: {summary}")
        tell_cost_when_ready(root, line)
        return DISPATCHED
    failures = memo.failures + 1 if (line, head) == (memo.line, memo.head) else 1
    write_memo(root, Memo(line=line, head=head, failures=failures))
    log(root, f"failed ({failures}/{MAX_FAILURES}): {summary}")
    if failures >= MAX_FAILURES:
        give_up(root, line, summary)
    return 1


def branch_tips(root: Path) -> str:
    """Every local branch with its commit: changes whenever the dispatcher commits anything."""
    return watch.git(root, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads/")


def give_up(root: Path, line: str, summary: str) -> None:
    """After repeated failures on one line, tell the pull request; the tick stops retrying."""
    pr = pr_of(root, line)
    message = (
        f"The dispatcher failed {MAX_FAILURES} times on `{line}` and has stopped retrying it. "
        f"Last failure: {summary}. A human needs to look at the machine; a new commit on the "
        f"branch makes the tick try again."
    )
    log(root, "giving up: " + ("posted on pull request" if pr else "no pull request to tell"))
    if pr:
        args = ["gh", "pr", "comment", str(pr), "--body", message]
        subprocess.run(args, cwd=root, check=False, capture_output=True)


def only_own_comments(root: Path, line: str, tickets: list[watch.Ticket]) -> bool:
    """A `pr` line whose unseen writings are all the pipeline's own (the cost table, an agent's
    replies) needs no dispatcher: it would only raise `comments_seen`, and it would push to the
    branch just when the human is invited to merge. The count catches up with the human's next
    comment, which the dispatcher reads together with the rest. A change request is the human's
    act whatever was written with it."""
    parts = line.split()
    if parts[0] != "pr" or changes_requested(line, tickets):
        return False
    ticket = _ticket(tickets, parts[1])
    number = ticket.meta.get("pr") if ticket else None
    if ticket is None or not number:
        return False
    bodies = pr_comment_bodies(root, int(number))
    seen = int(ticket.meta.get("comments_seen") or 0)
    return bodies is not None and unseen_are_own(bodies, seen)


def pr_comment_bodies(root: Path, number: int) -> list[str] | None:
    """What is written on the pull request, oldest first, in the order `comments_seen` counts
    it (conversation, comments on the diff, review texts); None when gh cannot answer."""
    pull = watch.read_pull_request(root, number)
    return None if pull is None else [body for _, body in pull.writings]


def pr_of(root: Path, line: str) -> int | None:
    parts = line.split()
    path = next((p for p in parts[1:] if p.endswith(".md")), None)
    if path is None:
        return None
    config = watch.load_config(root)
    ticket = next((t for t in watch.scan_tickets(root, config) if t.path.as_posix() == path), None)
    number = ticket.meta.get("pr") if ticket else None
    return int(number) if number else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--claude", default=os.environ.get("FACTORY_CLAUDE", "claude"))
    parser.add_argument("--model", default=os.environ.get("FACTORY_MODEL", "sonnet"))
    parser.add_argument("--dry-run", action="store_true", help="decide and log, start nothing")
    args = parser.parse_args(argv)
    claude = shutil.which(args.claude) or args.claude
    return tick(args.root.resolve(), claude, args.model, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
