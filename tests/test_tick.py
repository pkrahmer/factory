"""The tick's decisions are pure functions; its state helpers use a throwaway repository."""

from __future__ import annotations

import importlib.metadata
import subprocess
from pathlib import Path

import pytest

from factory import preflight, tick, watch

S1 = "factory/features/F0001-thing/ongoing/F0001-S0001-thing.md"
S2 = "factory/features/F0001-thing/ongoing/F0001-S0002-new.md"
B1 = "ticket/F0001-S0001-thing"
RUN_CODER = f"run coder {S1} {B1}"


def ticket(path: str, **meta: object) -> watch.Ticket:
    return watch.Ticket(Path(path), {"stage": "doing", **meta})


# --- needs_model ----------------------------------------------------------------


def test_idle_and_busy_never_need_the_model() -> None:
    assert not tick.needs_model("idle", tick.Memo(), "abc", [])
    assert not tick.needs_model(f"busy {S1}", tick.Memo(), "abc", [])


def test_new_line_or_new_head_needs_the_model() -> None:
    memo = tick.Memo(line=RUN_CODER, head="abc")
    assert tick.needs_model(f"run tester {S1} {B1}", memo, "abc", [])
    assert tick.needs_model(RUN_CODER, memo, "def", [])


def test_same_line_on_same_head_was_already_handled() -> None:
    assert not tick.needs_model(RUN_CODER, tick.Memo(line=RUN_CODER, head="abc"), "abc", [])


def test_pull_request_line_needs_the_model_only_for_new_comments() -> None:
    tickets = [ticket(S1, pr=1, comments_seen=2)]
    assert not tick.needs_model(f"pr {S1} OPEN 2 NONE", tick.Memo(), "abc", tickets)
    assert tick.needs_model(f"pr {S1} OPEN 3 NONE", tick.Memo(), "abc", tickets)
    assert tick.needs_model(f"pr {S1} OPEN 3", tick.Memo(), "abc", tickets)  # a line from before


def test_a_change_request_at_the_gate_needs_the_model_once_even_without_a_comment() -> None:
    line = f"pr {S1} OPEN 2 CHANGES_REQUESTED"
    at_gate = [ticket(S1, stage="accept", pr=1, comments_seen=2)]
    assert tick.needs_model(line, tick.Memo(), "abc", at_gate)
    assert not tick.needs_model(line, tick.Memo(line=line, head="abc"), "abc", at_gate)  # handled
    asking = [ticket(S1, blocked="asked", pr=1, comments_seen=2)]  # no rework path outside the gate
    assert not tick.needs_model(line, tick.Memo(), "abc", asking)
    report = "factory/features/F0001-thing/ACCEPTANCE.md"  # an acceptance has no rework
    acceptance = [ticket(report, stage="accept", pr=1, comments_seen=2)]
    on_report = f"pr {report} OPEN 2 CHANGES_REQUESTED"
    assert not tick.needs_model(on_report, tick.Memo(), "abc", acceptance)


def test_only_the_ticks_own_unseen_comments_need_no_dispatcher() -> None:
    table = f"{tick.OWN_PREFIX} cost of this ticket so far"
    assert tick.unseen_are_own([table], seen=0)
    assert tick.unseen_are_own(["a question", "an answer", table], seen=2)
    assert not tick.unseen_are_own([table, "merge? not yet: rename it"], seen=0)
    assert not tick.unseen_are_own([table], seen=1)  # nothing unseen
    reply = f"{tick.OWN_PREFIX} fixed in 1a2b3c4: renamed"  # an agent's reply on the diff
    assert tick.unseen_are_own(["rename this", reply], seen=1)


def test_a_pull_request_line_with_only_the_cost_table_unseen_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tickets = [ticket(S1, stage="accept", pr=7, comments_seen=0)]
    comments = [f"{tick.OWN_PREFIX} cost of this ticket so far"]
    monkeypatch.setattr(tick, "pr_comment_bodies", lambda _root, _number: comments)
    assert tick.only_own_comments(Path("."), f"pr {S1} OPEN 1 NONE", tickets)
    # the human requested changes without a word: the cost table must not hide that
    assert not tick.only_own_comments(Path("."), f"pr {S1} OPEN 1 CHANGES_REQUESTED", tickets)
    comments.append("please rename the module")
    assert not tick.only_own_comments(Path("."), f"pr {S1} OPEN 2 NONE", tickets)
    assert not tick.only_own_comments(Path("."), RUN_CODER, tickets)


def test_a_claim_older_than_the_machine_is_expired_at_once() -> None:
    started = watch.parse_timestamp("2026-10-04T22:00:00Z")
    old = [ticket(S1, claimed_at="2026-10-04T21:55:00Z")]
    new = [ticket(S1, claimed_at="2026-10-04T22:01:00Z")]
    assert tick.outlived_claim(f"busy {S1}", old, started) == f"expired {S1}"
    assert tick.outlived_claim(f"busy {S1}", new, started) == f"busy {S1}"
    assert tick.outlived_claim(f"busy {S1}", old, None) == f"busy {S1}"  # start unknown
    assert tick.outlived_claim(RUN_CODER, old, started) == RUN_CODER


def test_the_machine_start_comes_from_the_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACTORY_STARTED_AT", "2026-10-04T22:00:00Z")
    assert tick.machine_started() == watch.parse_timestamp("2026-10-04T22:00:00Z")
    monkeypatch.delenv("FACTORY_STARTED_AT")
    assert tick.machine_started() is None


def test_failed_line_is_retried_until_the_tick_gives_up() -> None:
    assert tick.needs_model(RUN_CODER, tick.Memo(line=RUN_CODER, head="abc", failures=1), "abc", [])
    given_up = tick.Memo(line=RUN_CODER, head="abc", failures=tick.MAX_FAILURES)
    assert not tick.needs_model(RUN_CODER, given_up, "abc", [])
    assert tick.needs_model(RUN_CODER, given_up, "def", [])  # a new commit makes it try again


# --- small helpers ----------------------------------------------------------------


def test_lock_staleness_uses_the_lease_plus_a_margin() -> None:
    assert not tick.lock_is_stale(written=1000.0, now=1000.0 + 60 * 60, lease_minutes=60)
    assert tick.lock_is_stale(written=1000.0, now=1000.0 + 71 * 60, lease_minutes=60)


def test_claude_command_is_headless_and_asks_nobody() -> None:
    cmd = tick.claude_command("claude", RUN_CODER, "sonnet")
    assert cmd[:3] == ["claude", "-p", f"/factory {RUN_CODER}"]
    assert "--permission-prompts" in cmd
    assert cmd[cmd.index("--permission-prompts") + 1] == "none"
    assert cmd[cmd.index("--output-format") + 1] == "json"


# --- state under .git ---------------------------------------------------------------

STAGES_YML = (
    "version: 4\nroot: factory/features\nlease_minutes: 60\nmax_attempts: 2\n"
    "stages:\n"
    "  ready: {agent: intake, next: [tests]}\n"
    "  tests: {agent: tester, next: [demo]}\n"
    "  demo: {agent: demo, next: [accept]}\n"
    "  accept: {agent: null, gate: human, next: [done]}\n"
    "  done: {agent: null, next: []}\n"
)


def git(repo: Path, *args: str) -> str:
    identity = ("-c", "user.name=t", "-c", "user.email=t@example.invalid")
    return subprocess.run(
        ["git", *identity, *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def write_story(repo: Path, rel: str, stage: str, pr: int | None = None) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    pr_line = f"pr: {pr}\n" if pr else ""
    path.write_text(f"---\nstage: {stage}\n{pr_line}---\n# Thing\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "factory").mkdir()
    (tmp_path / "factory" / "stages.yml").write_text(STAGES_YML)
    write_story(tmp_path, S1, "ready", pr=7)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "init")
    stamp = tmp_path / ".git" / "factory-preflight-ok"  # the machine was checked today
    stamp.write_text(tick.preflight_stamp_value(tmp_path) + "\n")
    return tmp_path


def test_memo_round_trips_and_defaults_to_empty(repo: Path) -> None:
    assert tick.read_memo(repo) == tick.Memo()
    tick.write_memo(repo, tick.Memo(line="idle", head="abc", failures=2))
    assert tick.read_memo(repo) == tick.Memo(line="idle", head="abc", failures=2)
    assert (repo / ".git" / "factory-tick.json").exists()


def test_lock_is_exclusive_and_released(repo: Path) -> None:
    assert tick.acquire_lock(repo, lease_minutes=60)
    assert not tick.acquire_lock(repo, lease_minutes=60)
    tick.release_lock(repo)
    assert tick.acquire_lock(repo, lease_minutes=60)
    tick.release_lock(repo)


def test_pr_of_reads_the_story_named_in_the_line(repo: Path) -> None:
    assert tick.pr_of(repo, f"run intake {S1} main") == 7
    assert tick.pr_of(repo, "idle") is None


def test_a_successful_dispatch_asks_for_an_immediate_next_tick(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tick, "fetch", lambda _root: None)
    monkeypatch.setattr(tick, "run_dispatcher", lambda *_a: (True, "turns=1"))
    assert tick.tick(repo, claude="claude", model="sonnet") == tick.DISPATCHED
    assert tick.read_memo(repo).line == f"run intake {S1} main"
    # nothing changed since: the same line on the same HEAD is not dispatched again
    assert tick.tick(repo, claude="claude", model="sonnet") == 0


def test_a_failed_dispatch_counts_and_gives_up(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tick, "fetch", lambda _root: None)
    monkeypatch.setattr(tick, "run_dispatcher", lambda *_a: (False, "claude exit 1"))
    told: list[str] = []
    monkeypatch.setattr(tick, "give_up", lambda _r, line, _s: told.append(line))
    for expected in range(1, tick.MAX_FAILURES + 1):
        assert tick.tick(repo, claude="claude", model="sonnet") == 1
        assert tick.read_memo(repo).failures == expected
    assert told == [f"run intake {S1} main"]
    assert tick.tick(repo, claude="claude", model="sonnet") == 0  # given up, no more retries


def test_a_dispatch_that_should_commit_but_did_not_is_a_failure(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tick, "run_dispatcher", lambda *_a: (True, "nothing to do"))
    memo = tick.Memo()
    assert tick.dispatch(repo, ("claude", "sonnet"), f"expired {S1}", "abc", memo) == 1
    assert tick.read_memo(repo).failures == 1  # retried on the next tick, not remembered as done


def test_a_dispatch_that_committed_is_a_success(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def commit(*_a: object) -> tuple[bool, str]:
        git(repo, "commit", "-q", "--allow-empty", "-m", "ticket F0001-S0001: claim expired")
        return True, "cleared the claim"

    monkeypatch.setattr(tick, "run_dispatcher", commit)
    line = f"expired {S1}"
    assert tick.dispatch(repo, ("claude", "sonnet"), line, "abc", tick.Memo()) == tick.DISPATCHED
    assert tick.read_memo(repo) == tick.Memo(line=line, head="abc", failures=0)


def test_cost_table_is_posted_once_the_story_reaches_the_gate(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    posted: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(args: list[str], **kw: object) -> object:
        if args[0] == "gh":
            posted.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")
        return real_run(args, **kw)  # type: ignore[call-overload]

    monkeypatch.setattr(subprocess, "run", fake_run)
    write_story(repo, S1, "demo", pr=7)
    git(repo, "commit", "-qam", "ticket F0001-S0001: → demo")
    tick.tell_cost_when_ready(repo, f"run tester {S1} {B1}")
    assert posted == []  # demo has an agent; the human is not asked yet
    write_story(repo, S1, "accept", pr=7)
    git(repo, "commit", "-qam", "ticket F0001-S0001: demo → accept")
    tick.tell_cost_when_ready(repo, f"run demo {S1} {B1}")
    assert len(posted) == 1
    assert posted[0][:4] == ["gh", "pr", "comment", "7"]
    assert posted[0][-1].startswith("factory: cost of this ticket so far")


def test_leftovers_on_a_story_branch_are_committed_and_the_tick_goes_on(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tick, "fetch", lambda _root: None)
    git(repo, "checkout", "-qb", B1)
    (repo / "half-done.txt").write_text("an agent was here\n")
    assert tick.tick(repo, claude="claude", model="sonnet", dry_run=True) == 0
    subject = git(repo, "log", "-1", "--format=%s").strip()
    assert subject == "ticket F0001-S0001: work left uncommitted by an interrupted run"
    assert not git(repo, "status", "--porcelain").strip()


def test_leftovers_on_main_stop_the_tick(repo: Path) -> None:
    (repo / "stray.txt").write_text("not the loop's doing\n")
    assert tick.tick(repo, claude="claude", model="sonnet", dry_run=True) == 1
    assert "dirty on main" in (repo / ".git" / "factory-tick.log").read_text()


def test_tick_fast_forwards_main_so_new_stories_reach_the_working_tree(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    remote = tmp_path_factory.mktemp("remote")  # outside the checkout, which must stay clean
    origin = remote / "origin.git"
    git(repo, "init", "-q", "--bare", "-b", "main", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    other = remote / "other"
    git(repo, "clone", "-q", "-b", "main", str(origin), str(other))
    write_story(other, S2, "ready")
    git(other, "add", "-A")
    git(other, "commit", "-qm", "F0001: start S0002")
    git(other, "push", "-q", "origin", "main")
    assert tick.tick(repo, claude="claude", model="sonnet", dry_run=True) == 0
    assert (repo / S2).exists()
    assert "main fast-forwarded to origin/main" in (repo / ".git" / "factory-tick.log").read_text()


def test_dry_run_logs_the_decision_without_starting_anything(repo: Path) -> None:
    assert tick.tick(repo, claude="/nonexistent/claude", model="sonnet", dry_run=True) == 0
    log = (repo / ".git" / "factory-tick.log").read_text()
    assert f"would dispatch: run intake {S1} main" in log
    assert not (repo / ".git" / "factory-tick.lock").exists()


def test_a_changed_stage_table_or_factory_version_invalidates_the_preflight_stamp(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran: list[int] = []

    def fake_evaluate(*_a: object, **_kw: object) -> list[object]:
        ran.append(1)
        return []

    monkeypatch.setattr(preflight, "evaluate", fake_evaluate)
    assert tick.preflight_ok(repo) and ran == []  # stamp fits: no run
    (repo / "factory" / "stages.yml").write_text(STAGES_YML + "  x: {agent: y, next: []}\n")
    assert tick.preflight_ok(repo) and len(ran) == 1  # table changed: preflight ran, stamp renewed
    assert tick.preflight_ok(repo) and len(ran) == 1
    monkeypatch.setattr(importlib.metadata, "version", lambda _n: "9.9.9")
    assert tick.preflight_ok(repo) and len(ran) == 2  # new image: preflight ran again
