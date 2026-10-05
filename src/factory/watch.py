"""Deterministic router for the delivery pipeline.

Stories live under features: `factory/features/<F0001-slug>/ongoing/<F0001-S0003-slug>.md`
is a story in the pipeline, `drafts/` beside it is the human's, `done/` the archive. The
stage is in the frontmatter, one branch per story (`ticket/<file stem>`), a GitHub pull
request as the channel to the human. The watcher reads frontmatter, branches and PR state
and prints one line saying what should happen next. It never moves files, never commits,
never calls a model. The contract is `docs/WATCH_CONTRACT.md`.

    factory-watch --once
    factory-watch --follow
    factory-watch --board
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

Config = dict[str, Any]  # parsed stages.yml; our own file, validated loosely
Change = tuple[Path, str, str]  # (ticket path, stage before, stage after) in the last commit
PrState = tuple[str, int]  # (OPEN | MERGED | CLOSED, number of writings on it)
PrLookup = Callable[["Ticket"], PrState | None]
Writing = tuple[datetime, str]  # (when, text) of one thing written on a pull request

CORRECTION_MARKER = "moved back"  # commit subjects with this are exempt from reject
ID_PATTERN = re.compile(r"^(F\d{4}-S\d{4})(?:-[a-z0-9]+)*$")  # a story's file stem
FEATURE_PATTERN = re.compile(r"^(F\d{4})(?:-[a-z0-9]+)*$")  # a feature's folder name
TICKET_REFS = (
    "refs/heads/ticket/",
    "refs/remotes/origin/ticket/",
    "refs/heads/acceptance/",
    "refs/remotes/origin/acceptance/",
)
DEFAULT_ROOT = "factory/features"
LIVE = "ongoing"  # the one subfolder the watcher reads; drafts and done are not its business
ACCEPTANCE = "ACCEPTANCE.md"  # the feature's acceptance report, a ticket of its own
FEATURE_STAGE = "feature"  # the stage a due acceptance starts in; its agent runs on main
MAIN_STAGES = ("ready", FEATURE_STAGE)  # stages whose agent runs on main and creates the branch


@dataclass(frozen=True)
class Ticket:
    path: Path  # relative to the repository root
    meta: dict[str, Any]

    @property
    def is_acceptance(self) -> bool:
        """A feature's acceptance report, `<feature>/ACCEPTANCE.md`, runs like a story: an
        agent writes it on a branch, the human merges or closes its pull request."""
        return self.path.name == ACCEPTANCE

    @property
    def ticket_id(self) -> str:
        if self.is_acceptance:
            return self.feature
        match = ID_PATTERN.match(self.path.stem)
        return match.group(1) if match else self.path.stem

    @property
    def feature(self) -> str:
        """The feature folder's name, `F0001-slug`; empty when the path is not under one."""
        parts = self.path.parts
        if self.is_acceptance and len(parts) >= 2:
            return parts[-2]
        return parts[-3] if len(parts) >= 3 and parts[-2] == LIVE else ""

    @property
    def stage(self) -> str:
        return str(self.meta.get("stage") or "ready")

    @property
    def branch(self) -> str:
        if self.is_acceptance:
            return f"acceptance/{self.feature}"
        return f"ticket/{self.path.stem}"

    @property
    def claimed(self) -> bool:
        return bool(self.meta.get("claimed_at"))

    def claim_age(self, now: datetime) -> timedelta:
        return now - parse_timestamp(str(self.meta["claimed_at"]))


# --- reading ---------------------------------------------------------------


def parse_timestamp(value: str) -> datetime:
    """ISO 8601; a naive value is taken as UTC, which is what agents write."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_frontmatter(text: str) -> dict[str, Any]:
    """The YAML block between the first two `---` lines. Nothing else is read."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    loaded = yaml.safe_load(text[4:end])
    return dict(loaded) if isinstance(loaded, dict) else {}


def load_config(root: Path) -> Config:
    loaded = yaml.safe_load((root / "factory" / "stages.yml").read_text(encoding="utf-8"))
    return dict(loaded)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, encoding="utf-8"
    )
    return result.stdout


MAIN_REF = "refs/remotes/origin/main"


def main_ref(root: Path) -> str | None:
    """Where tickets without a branch are read from: `origin/main` when the remote is known
    (the checkout may sit on a ticket branch, and new tickets arrive on main), else nowhere."""
    return MAIN_REF if _ref_exists(root, MAIN_REF) else None


def _ref_exists(root: Path, ref: str) -> bool:
    args = ["git", "rev-parse", "--verify", "-q", ref]
    return subprocess.run(args, cwd=root, check=False, capture_output=True).returncode == 0


def merged_into_main(root: Path, ref: str) -> bool:
    """True when `ref` is an ancestor of main (`origin/main` when known): merged, so the
    ticket on main is the newer copy. HEAD is not the yardstick: between stages the checkout
    sits on the ticket branch itself, which is trivially an ancestor of HEAD."""
    main = main_ref(root) or ("refs/heads/main" if _ref_exists(root, "refs/heads/main") else None)
    if main is None:
        return False
    args = ["git", "merge-base", "--is-ancestor", ref, main]
    return subprocess.run(args, cwd=root, check=False, capture_output=True).returncode == 0


def ticket_branches(root: Path) -> dict[str, str]:
    """Branch name → ref to read from. Local wins over remote; merged branches are left out."""
    out = git(root, "for-each-ref", "--format=%(refname)", *TICKET_REFS)
    refs: dict[str, str] = {}
    for ref in sorted(out.split(), key=lambda r: r.startswith("refs/remotes/")):  # local first
        name = ref.removeprefix("refs/remotes/origin/").removeprefix("refs/heads/")
        if not merged_into_main(root, ref):
            refs.setdefault(name, ref)
    return refs


def features_dir(config: Config) -> Path:
    return Path(str(config.get("root") or DEFAULT_ROOT))


def _is_live(features: Path, name: str) -> bool:
    """`<features>/<feature>/ongoing/<story>.md`, nothing deeper, nothing beside."""
    rel = Path(name)
    try:
        inner = rel.relative_to(features).parts
    except ValueError:
        return False
    return len(inner) == 3 and inner[1] == LIVE and inner[2].endswith(".md")


def ticket_paths(root: Path, features: Path, base: str | None) -> list[Path]:
    if base is None:
        return [p.relative_to(root) for p in (root / features).glob(f"*/{LIVE}/*.md")]
    listed = git(root, "ls-tree", "-r", "--name-only", base, "--", f"{features.as_posix()}/")
    return [Path(name) for name in listed.split("\n") if _is_live(features, name)]


def _read(root: Path, ref: str | None, rel: Path) -> str | None:
    """The file at `ref` (a branch tip or `origin/main`), or in the working tree; None if absent."""
    if ref:
        try:
            return git(root, "show", f"{ref}:{rel.as_posix()}")
        except subprocess.CalledProcessError:
            return None
    path = root / rel
    return path.read_text(encoding="utf-8") if path.is_file() else None


def feature_files(root: Path, features: Path, base: str | None) -> dict[str, list[Path]]:
    """Every file under every feature folder, by folder name, from `base` or the working tree."""
    if base is None:
        names = [p.relative_to(root) for p in (root / features).rglob("*") if p.is_file()]
    else:
        listed = git(root, "ls-tree", "-r", "--name-only", base, "--", f"{features.as_posix()}/")
        names = [Path(n) for n in listed.split("\n") if n]
    by_feature: dict[str, list[Path]] = {}
    for rel in names:
        try:
            inner = rel.relative_to(features).parts
        except ValueError:
            continue
        if inner and FEATURE_PATTERN.match(inner[0]):
            by_feature.setdefault(inner[0], []).append(rel)
    return by_feature


def done_stories(files: list[Path]) -> list[str]:
    """Ids of the stories archived under `done/`, sorted."""
    ids = []
    for rel in files:
        if len(rel.parts) >= 2 and rel.parts[-2] == "done" and rel.suffix == ".md":
            match = ID_PATTERN.match(rel.stem)
            if match:
                ids.append(match.group(1))
    return sorted(ids)


def acceptance_ticket(
    root: Path, rel: Path, files: list[Path], *, ref: str | None, branch: str | None
) -> Ticket | None:
    """The feature's acceptance (`rel` is its `ACCEPTANCE.md`) as a ticket, when one is due
    or in flight.

    Due: the feature has archived stories, nothing in `ongoing/` or `drafts/`, and no report
    that covers exactly those stories (`stories` in the report's frontmatter). In flight: the
    `acceptance/<feature>` branch exists; the report is read from there. Otherwise None."""
    if branch:
        text = _read(root, branch, rel)
        if text is not None:
            return Ticket(rel, parse_frontmatter(text))
    text = _read(root, ref, rel)
    report = parse_frontmatter(text) if text is not None else None
    if report is not None and report.get("stage") != "done":
        # Merged, not yet booked: the merge brought the report and its drafts to main and made
        # the branch count as absent; the drafts make the feature look unfinished, but the
        # merge still needs its line, or the report never reaches `done`.
        return Ticket(rel, report)
    done = done_stories(files)
    waiting = [f for f in files if len(f.parts) >= 2 and f.parts[-2] in (LIVE, "drafts")]
    if not done or waiting:
        return None
    if report is not None and sorted(str(s) for s in report.get("stories") or []) == done:
        return None
    return Ticket(rel, {"stage": FEATURE_STAGE})


def scan_tickets(root: Path, config: Config) -> list[Ticket]:
    """Every story in an `ongoing/` folder plus every due or running feature acceptance,
    lowest id first — which is feature by feature, then story by story, then the feature's
    acceptance. Read from its branch tip when a branch exists, else from `origin/main` when
    that ref exists, else from the working tree."""
    features = features_dir(config)
    branches = ticket_branches(root)
    base = main_ref(root)
    found: list[Ticket] = []
    for rel in ticket_paths(root, features, base):
        text = _read(root, branches.get(f"ticket/{rel.stem}") or base, rel)
        if text is not None:
            found.append(Ticket(rel, parse_frontmatter(text)))
    for name, files in feature_files(root, features, base).items():
        rel = features / name / ACCEPTANCE
        branch = branches.get(f"acceptance/{name}")
        ticket = acceptance_ticket(root, rel, files, ref=base, branch=branch)
        if ticket is not None:
            found.append(ticket)
    return sorted(found, key=lambda t: t.ticket_id)


def last_change(root: Path, config: Config) -> Change | None:
    """The stage change of a ticket in the last commit, if any and if not a correction.
    A story that moved folders (promoted, archived) has no "before" at its path: not a change."""
    features = features_dir(config).as_posix()
    try:
        subject = git(root, "log", "-1", "--format=%s")
        changed = git(root, "diff", "--name-only", "HEAD~1", "HEAD", "--", features).split()
    except subprocess.CalledProcessError:
        return None  # fewer than two commits
    if CORRECTION_MARKER in subject or _is_merge(root):
        return None  # a merge brings stage changes that were legal where they happened
    for name in changed:
        try:
            before = parse_frontmatter(git(root, "show", f"HEAD~1:{name}")).get("stage", "ready")
            after = parse_frontmatter(git(root, "show", f"HEAD:{name}")).get("stage", "ready")
        except subprocess.CalledProcessError:
            continue  # added or deleted in this commit
        if before != after:
            return Path(name), str(before), str(after)
    return None


def _is_merge(root: Path) -> bool:
    args = ["git", "rev-parse", "--verify", "-q", "HEAD^2"]
    return subprocess.run(args, cwd=root, check=False, capture_output=True).returncode == 0


@dataclass(frozen=True)
class PullRequest:
    state: str  # OPEN | MERGED | CLOSED
    writings: list[Writing]  # everything `comments_seen` counts, oldest first


def pull_request(
    view: dict[str, Any], diff_comments: list[dict[str, Any]], reviews: list[dict[str, Any]]
) -> PullRequest:
    """Pure: the pull request from what `gh` returned. Its writings are the conversation's
    comments, the comments on lines of the diff and the text of submitted reviews. A review
    still pending is the human's draft: GitHub shows it to the token's owner only."""
    submitted = [r for r in reviews if r.get("submitted_at") and r.get("state") != "PENDING"]
    writings = [
        (parse_timestamp(c["createdAt"]), str(c["body"])) for c in view.get("comments") or []
    ]
    writings += [(parse_timestamp(c["created_at"]), str(c["body"])) for c in diff_comments]
    writings += [
        (parse_timestamp(r["submitted_at"]), str(r["body"])) for r in submitted if r["body"]
    ]
    return PullRequest(str(view["state"]), sorted(writings, key=lambda w: w[0]))


def _gh(root: Path, *args: str) -> str | None:
    try:
        return subprocess.run(
            ["gh", *args], cwd=root, check=True, capture_output=True, encoding="utf-8"
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def read_pull_request(root: Path, number: int) -> PullRequest | None:
    """Ask GitHub: state and conversation, comments on the diff, reviews. None when gh fails."""
    api = f"repos/{{owner}}/{{repo}}/pulls/{number}"
    view = _gh(root, "pr", "view", str(number), "--json", "state,comments")
    diff = _gh(root, "api", "--paginate", f"{api}/comments", "--jq", ".[] | {created_at, body}")
    reviews = _gh(
        root, "api", "--paginate", f"{api}/reviews", "--jq", ".[] | {submitted_at, state, body}"
    )
    if view is None or diff is None or reviews is None:
        return None
    diff_comments = [json.loads(line) for line in diff.splitlines() if line.strip()]
    review_items = [json.loads(line) for line in reviews.splitlines() if line.strip()]
    return pull_request(json.loads(view), diff_comments, review_items)


def gh_pr_state(root: Path, ticket: Ticket) -> PrState | None:
    """Ask GitHub about the ticket's pull request. None when gh fails or no PR is recorded."""
    number = ticket.meta.get("pr")
    pull = read_pull_request(root, int(number)) if number else None
    return None if pull is None else (pull.state, len(pull.writings))


# --- deciding --------------------------------------------------------------


def _rejected(config: Config, change: Change | None) -> str | None:
    if change is None:
        return None
    path, before, after = change
    allowed = config["stages"].get(before, {}).get("next", [])
    if after in allowed:
        return None
    return f"reject {path.as_posix()} {before} {after}"


def _duplicated(tickets: list[Ticket]) -> str | None:
    seen: dict[str, Ticket] = {}
    for ticket in tickets:
        first = seen.setdefault(ticket.ticket_id, ticket)
        if first is not ticket:
            return f"duplicate {ticket.ticket_id} {first.path.as_posix()} {ticket.path.as_posix()}"
    return None


def _at_gate(config: Config, ticket: Ticket) -> bool:
    """A stage with `gate` has no agent; the human leaves it by merging or closing."""
    return config["stages"].get(ticket.stage, {}).get("gate") is not None


def _asked_on_pr(ticket: Ticket) -> bool:
    """A question has been posted on the pull request; the answer comes back the same way."""
    return ticket.meta.get("blocked") == "asked"


def _polls_pr(config: Config, ticket: Ticket) -> bool:
    """Pull requests are read only while the human is the one expected to act."""
    return bool(ticket.meta.get("pr")) and (_at_gate(config, ticket) or _asked_on_pr(ticket))


def _pull_requests(config: Config, tickets: list[Ticket], lookup: PrLookup) -> str | None:
    for ticket in tickets:
        if not _polls_pr(config, ticket):
            continue
        state = lookup(ticket)
        if state is None:
            return f"error pr-lookup {ticket.path.as_posix()}"
        verdict, writings = state
        if verdict == "MERGED":
            return f"merged {ticket.path.as_posix()} {ticket.branch}"
        if verdict == "CLOSED":
            return f"closed {ticket.path.as_posix()} {ticket.branch}"
        return f"pr {ticket.path.as_posix()} OPEN {writings}"
    return None


def _asking(config: Config, tickets: list[Ticket]) -> str | None:
    for ticket in tickets:
        waiting_without_pr = _at_gate(config, ticket) and not ticket.meta.get("pr")
        if ticket.meta.get("blocked") == "question" or waiting_without_pr:
            return f"ask {ticket.path.as_posix()}"
    return None


def _leased(config: Config, tickets: list[Ticket], now: datetime) -> str | None:
    lease = timedelta(minutes=int(config["lease_minutes"]))
    for ticket in tickets:
        if ticket.claimed:
            verb = "busy" if ticket.claim_age(now) < lease else "expired"
            return f"{verb} {ticket.path.as_posix()}"
    return None


def _runnable(config: Config, tickets: list[Ticket]) -> str | None:
    max_attempts = int(config.get("max_attempts", 2))
    for ticket in tickets:
        agent = config["stages"].get(ticket.stage, {}).get("agent")
        if not agent:
            continue
        if int(ticket.meta.get("attempts") or 0) >= max_attempts:
            return f"ask {ticket.path.as_posix()}"
        where = "main" if ticket.stage in MAIN_STAGES else ticket.branch
        return f"run {agent} {ticket.path.as_posix()} {where}"
    return None


def evaluate(
    config: Config,
    tickets: list[Ticket],
    change: Change | None,
    now: datetime,
    lookup: PrLookup = lambda _ticket: None,
) -> str:
    """Pure: same inputs, same line. First match wins, in contract order."""
    return (
        _rejected(config, change)
        or _duplicated(tickets)
        or _pull_requests(config, tickets, lookup)
        or _asking(config, tickets)
        or _leased(config, tickets, now)
        or _runnable(config, tickets)
        or "idle"
    )


# --- running ---------------------------------------------------------------


def evaluate_repo(root: Path) -> str:
    config = load_config(root)
    return evaluate(
        config,
        scan_tickets(root, config),
        last_change(root, config),
        datetime.now(UTC),
        lambda ticket: gh_pr_state(root, ticket),
    )


def acceptance_status(folder: Path, drafts: int, live: int, done: int, in_flight: str) -> str:
    """One word for the board: `-` (incomplete), `due`, `running`, `accepted` or `refused`."""
    if in_flight:
        return in_flight
    report = folder / ACCEPTANCE
    meta = parse_frontmatter(report.read_text(encoding="utf-8")) if report.is_file() else {}
    covered = sorted(str(s) for s in meta.get("stories") or [])
    # The verdict stands until another story is archived, drafts or not: a merged acceptance
    # brings its proposed drafts with it.
    if (
        done
        and meta.get("stage") == "done"
        and covered == done_stories(list(folder.glob("done/*.md")))
    ):
        return str(meta.get("outcome") or "accepted")
    if not done or drafts or live:
        return "-"
    return "due"


def feature_counts(
    root: Path, config: Config, running: dict[str, str] | None = None
) -> list[tuple[str, int, int, int, str]]:
    """(feature folder, drafts, ongoing, done, acceptance) from the working tree, one row per
    feature; `running` maps a feature to the stage of its acceptance when one is in flight."""
    rows: list[tuple[str, int, int, int, str]] = []
    for folder in sorted((root / features_dir(config)).glob("*/")):
        if not FEATURE_PATTERN.match(folder.name):
            continue
        drafts, live, done = (
            len(list((folder / sub).glob("*.md"))) for sub in ("drafts", LIVE, "done")
        )
        status = acceptance_status(folder, drafts, live, done, (running or {}).get(folder.name, ""))
        rows.append((folder.name, drafts, live, done, status))
    return rows


def board(root: Path) -> str:
    config = load_config(root)
    tickets = scan_tickets(root, config)
    running = {
        t.feature: ("running" if t.stage != FEATURE_STAGE else "due")
        for t in tickets
        if t.is_acceptance
    }
    rows = [f"{'feature':<40} {'drafts':>6} {'ongoing':>7} {'done':>5}  acceptance"]
    rows.extend(
        f"{name:<40} {d:>6} {o:>7} {done:>5}  {status}"
        for name, d, o, done, status in feature_counts(root, config, running)
    )
    rows.append("")
    rows.append(f"{'story':<13} {'stage':<8} {'pr':<5} {'claimed':<20} flags")
    for t in tickets:
        flags = [
            f"blocked:{t.meta.get('blocked')}" if t.meta.get("blocked") else "",
            f"round:{t.meta.get('round')}" if t.meta.get("round") else "",
            f"attempts:{t.meta.get('attempts')}" if t.meta.get("attempts") else "",
        ]
        rows.append(
            f"{t.ticket_id:<13} {t.stage:<8} {str(t.meta.get('pr') or '-'):<5} "
            f"{str(t.meta.get('claimed_at') or '-'):<20} {' '.join(f for f in flags if f)}"
        )
    return "\n".join(rows)


def fingerprint(root: Path, config: Config, tick: int, pr_every: int) -> str:
    """Changes when HEAD moves, the task tree is touched, a ticket branch moves,
    and every `pr_every` ticks, so pull request state gets re-read."""
    head = git(root, "rev-parse", "HEAD")
    status = git(root, "status", "--porcelain", "--", features_dir(config).as_posix())
    refs = git(root, "for-each-ref", "--format=%(refname) %(objectname)", *TICKET_REFS)
    return head + status + refs + str(tick // pr_every)


def _memo(root: Path) -> Path:
    """Where `--follow` keeps the last line it printed: inside `.git`, so it is never tracked."""
    return Path(git(root, "rev-parse", "--absolute-git-dir").strip()) / "factory-last-line"


def remembered_line(root: Path) -> str:
    try:
        return _memo(root).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def remember_line(root: Path, line: str) -> None:
    _memo(root).write_text(line + "\n", encoding="utf-8")


def follow(root: Path, interval: float, pr_every: int, max_ticks: int | None = None) -> None:
    """Print a line whenever it changes. The last printed line survives a restart, so a
    watcher that is re-armed every half hour does not repeat what the dispatcher already saw."""
    config = load_config(root)
    seen_fingerprint = ""
    seen_line = remembered_line(root)
    tick = 0
    while max_ticks is None or tick < max_ticks:
        current = fingerprint(root, config, tick, pr_every)
        if current != seen_fingerprint:
            seen_fingerprint = current
            line = evaluate_repo(root)
            if line != seen_line:
                seen_line = line
                remember_line(root, line)
                print(line, flush=True)
        tick += 1
        if max_ticks is None or tick < max_ticks:
            time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="print one line and exit")
    mode.add_argument("--follow", action="store_true", help="block and print on every change")
    mode.add_argument("--board", action="store_true", help="print the board and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="poll interval in seconds")
    parser.add_argument("--pr-every", type=int, default=15, help="re-read PR state every N polls")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    if args.board:
        print(board(args.root))
        return 0
    if args.once:
        print(evaluate_repo(args.root))
        return 0
    try:
        follow(args.root, args.interval, args.pr_every)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
