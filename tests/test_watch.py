"""Tests for the watcher. `evaluate()` is pure, so routing is tested without git;
reading, branches and the last stage change use a throwaway repository under tmp_path."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory import watch

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
FEATURES = Path("factory/features")

CONFIG: watch.Config = {
    "version": 4,
    "root": FEATURES.as_posix(),
    "lease_minutes": 60,
    "max_attempts": 2,
    "stages": {
        "ready": {"agent": "intake", "next": ["tests"]},
        "tests": {"agent": "tester", "next": ["doing"]},
        "doing": {"agent": "coder", "next": ["review", "tests"]},
        "review": {"agent": "reviewer", "next": ["demo", "doing"], "max_rounds": 2},
        "demo": {"agent": "demo", "next": ["accept", "doing"], "max_rounds": 2},
        "feature": {"agent": "acceptor", "next": ["accept"]},
        "accept": {"agent": None, "next": ["done", "doing"], "gate": "human"},
        "done": {"agent": None, "next": []},
    },
}


def story_path(story_id: str, slug: str = "thing") -> Path:
    feature = story_id.split("-", 1)[0]
    return FEATURES / f"{feature}-{slug}" / "ongoing" / f"{story_id}-{slug}.md"


def ticket(stage: str, story_id: str, slug: str = "thing", **meta: object) -> watch.Ticket:
    return watch.Ticket(story_path(story_id, slug), {"stage": stage, **meta})


S1 = "factory/features/F0001-thing/ongoing/F0001-S0001-thing.md"
S2 = "factory/features/F0001-thing/ongoing/F0001-S0002-thing.md"
B1 = "ticket/F0001-S0001-thing"
B2 = "ticket/F0001-S0002-thing"


# --- evaluate: contract order --------------------------------------------------


def test_idle_when_no_tickets() -> None:
    assert watch.evaluate(CONFIG, [], None, NOW) == "idle"


def test_ready_runs_intake_on_main() -> None:
    line = watch.evaluate(CONFIG, [ticket("ready", "F0001-S0001")], None, NOW)
    assert line == f"run intake {S1} main"


def test_later_stages_run_on_the_story_branch() -> None:
    line = watch.evaluate(CONFIG, [ticket("doing", "F0001-S0002")], None, NOW)
    assert line == f"run coder {S2} {B2}"


def test_runs_lowest_id_first_which_is_feature_by_feature() -> None:
    tickets = sorted(
        [ticket("ready", "F0002-S0001"), ticket("doing", "F0001-S0002")],
        key=lambda t: t.ticket_id,
    )
    assert watch.evaluate(CONFIG, tickets, None, NOW) == f"run coder {S2} {B2}"


def test_done_has_no_agent() -> None:
    assert watch.evaluate(CONFIG, [ticket("done", "F0001-S0001")], None, NOW) == "idle"


def test_question_beats_run() -> None:
    tickets = [ticket("ready", "F0001-S0001"), ticket("doing", "F0001-S0002", blocked="question")]
    assert watch.evaluate(CONFIG, tickets, None, NOW) == f"ask {S2}"


def test_gate_without_pull_request_is_an_ask() -> None:
    assert watch.evaluate(CONFIG, [ticket("accept", "F0001-S0001")], None, NOW) == f"ask {S1}"


def test_open_pull_request_at_the_gate_reports_comment_count() -> None:
    tickets = [ticket("accept", "F0001-S0001", pr=7)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("OPEN", 3))
    assert line == f"pr {S1} OPEN 3"


def test_posted_question_polls_the_pull_request_for_the_answer() -> None:
    tickets = [ticket("doing", "F0001-S0002", blocked="asked", pr=2, comments_seen=1)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("OPEN", 2))
    assert line == f"pr {S2} OPEN 2"


def test_unposted_question_is_an_ask_and_does_not_poll() -> None:
    tickets = [ticket("doing", "F0001-S0002", blocked="question", pr=2)]
    looked_up: list[watch.Ticket] = []

    def lookup(t: watch.Ticket) -> watch.PrState | None:
        looked_up.append(t)
        return ("OPEN", 1)

    assert watch.evaluate(CONFIG, tickets, None, NOW, lookup) == f"ask {S2}"
    assert looked_up == []


def test_running_stage_with_pull_request_is_not_polled() -> None:
    tickets = [ticket("doing", "F0001-S0002", pr=2, claimed_at=NOW.isoformat())]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("OPEN", 5))
    assert line == f"busy {S2}"


def test_merged_pull_request_is_reported() -> None:
    tickets = [ticket("accept", "F0001-S0001", pr=7)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("MERGED", 0))
    assert line == f"merged {S1} {B1}"


def test_closed_pull_request_is_reported() -> None:
    tickets = [ticket("accept", "F0001-S0001", pr=7)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("CLOSED", 1))
    assert line == f"closed {S1} {B1}"


# A pull request closed at the gate without a reason: the dispatcher reopens it, moves the
# story to doing and posts a question with three answers. Each answer must route as follows.


def test_a_second_close_while_the_question_is_open_is_a_discard() -> None:
    tickets = [ticket("doing", "F0001-S0001", blocked="asked", pr=7, comments_seen=2)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("CLOSED", 2))
    assert line == f"closed {S1} {B1}"  # not at accept: the dispatcher discards to drafts


def test_a_merge_while_the_question_is_open_is_accepted() -> None:
    tickets = [ticket("doing", "F0001-S0001", blocked="asked", pr=7, comments_seen=2)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("MERGED", 2))
    assert line == f"merged {S1} {B1}"


def test_a_question_behind_a_closed_pull_request_is_never_asked() -> None:
    # Why the dispatcher reopens before it asks: a closed pull request wins over the question,
    # so a question left at accept behind it would come back as `closed` on every tick.
    tickets = [ticket("accept", "F0001-S0001", blocked="question", pr=7)]
    line = watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: ("CLOSED", 1))
    assert line == f"closed {S1} {B1}"


def test_failed_pull_request_lookup_is_an_error_line() -> None:
    tickets = [ticket("accept", "F0001-S0001", pr=7)]
    assert watch.evaluate(CONFIG, tickets, None, NOW, lambda _t: None) == f"error pr-lookup {S1}"


def test_live_claim_blocks_everything_else() -> None:
    claimed = ticket("tests", "F0001-S0001", claimed_at=(NOW - timedelta(minutes=5)).isoformat())
    tickets = [claimed, ticket("ready", "F0001-S0002")]
    assert watch.evaluate(CONFIG, tickets, None, NOW) == f"busy {S1}"


def test_stale_claim_is_reported_as_expired() -> None:
    stale = ticket("tests", "F0001-S0001", claimed_at=(NOW - timedelta(minutes=61)).isoformat())
    assert watch.evaluate(CONFIG, [stale], None, NOW) == f"expired {S1}"


def test_too_many_attempts_asks_instead_of_running() -> None:
    tickets = [ticket("doing", "F0001-S0001", attempts=2)]
    assert watch.evaluate(CONFIG, tickets, None, NOW) == f"ask {S1}"


def test_illegal_stage_change_is_rejected_before_anything_else() -> None:
    change: watch.Change = (Path(S1), "ready", "demo")
    tickets = [ticket("doing", "F0001-S0002", blocked="question")]
    assert watch.evaluate(CONFIG, tickets, change, NOW) == f"reject {S1} ready demo"


def test_legal_stage_change_is_not_rejected() -> None:
    change: watch.Change = (Path(S1), "ready", "tests")
    line = watch.evaluate(CONFIG, [ticket("tests", "F0001-S0001")], change, NOW)
    assert line == f"run tester {S1} {B1}"


def test_duplicate_id_is_reported() -> None:
    a = ticket("ready", "F0001-S0001", "thing")
    b = ticket("ready", "F0001-S0001", "other")
    line = watch.evaluate(CONFIG, [a, b], None, NOW)
    assert line == f"duplicate F0001-S0001 {a.path.as_posix()} {b.path.as_posix()}"


# --- reading -------------------------------------------------------------------


def test_frontmatter_is_the_first_yaml_block_only() -> None:
    text = "---\nstage: doing\npr: 3\n---\n\n# Title\n\n---\nnot: frontmatter\n---\n"
    assert watch.parse_frontmatter(text) == {"stage": "doing", "pr": 3}


def test_text_without_frontmatter_reads_as_a_fresh_story() -> None:
    t = watch.Ticket(Path(S1), watch.parse_frontmatter("# Just a title\n"))
    assert t.stage == "ready"
    assert not t.claimed


def test_id_feature_and_branch_come_from_the_path() -> None:
    t = watch.Ticket(Path("factory/features/F0003-api/ongoing/F0003-S0012-routes.md"), {})
    assert t.ticket_id == "F0003-S0012"
    assert t.feature == "F0003-api"
    assert t.branch == "ticket/F0003-S0012-routes"


def test_timestamp_with_z_suffix_is_utc() -> None:
    assert watch.parse_timestamp("2026-10-03T12:00:00Z") == NOW


# --- against a real repository ---------------------------------------------------


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


STAGES_YML = (
    "version: 4\nroot: factory/features\nlease_minutes: 60\nmax_attempts: 2\nstages:\n"
    "  ready: {agent: intake, next: [tests]}\n"
    "  tests: {agent: tester, next: [doing]}\n"
    "  doing: {agent: coder, next: [review, tests]}\n"
    "  review: {agent: reviewer, next: [demo, doing]}\n"
    "  demo: {agent: demo, next: [accept, doing]}\n"
    "  feature: {agent: acceptor, next: [accept]}\n"
    "  accept: {agent: null, next: [done, doing], gate: human}\n"
    "  done: {agent: null, next: []}\n"
)


def write_story(repo: Path, rel: str, stage: str = "ready") -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstage: {stage}\n---\n# Thing\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "factory").mkdir()
    (tmp_path / "factory" / "stages.yml").write_text(STAGES_YML)
    (tmp_path / FEATURES / "F0001-thing").mkdir(parents=True)
    (tmp_path / FEATURES / "F0001-thing" / "FEATURE.md").write_text("# Thing\n")
    write_story(tmp_path, S1)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "test")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "ticket F0001-S0001: created")
    return tmp_path


def set_stage(repo: Path, stage: str, subject: str) -> None:
    write_story(repo, S1, stage)
    git(repo, "commit", "-qam", subject)


def test_last_change_is_none_after_a_plain_edit(repo: Path) -> None:
    (repo / S1).write_text("---\nstage: ready\nclaimed_at: 2026-10-03T12:00:00Z\n---\n# Thing\n")
    git(repo, "commit", "-qam", "ticket F0001-S0001: claim")
    assert watch.last_change(repo, watch.load_config(repo)) is None


def test_last_change_sees_a_stage_change(repo: Path) -> None:
    set_stage(repo, "tests", "ticket F0001-S0001: ready → tests")
    assert watch.last_change(repo, watch.load_config(repo)) == (Path(S1), "ready", "tests")


def test_correction_commits_are_exempt(repo: Path) -> None:
    set_stage(repo, "done", "ticket F0001-S0001: illegal change ready → done, moved back")
    assert watch.last_change(repo, watch.load_config(repo)) is None


def test_promoting_a_draft_is_a_move_not_a_stage_change(repo: Path) -> None:
    draft = FEATURES / "F0001-thing" / "drafts" / "F0001-S0002-thing.md"
    (repo / draft).parent.mkdir()
    (repo / draft).write_text("# Second\n")  # drafts carry no frontmatter at all
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "F0001: draft S0002")
    git(repo, "mv", draft.as_posix(), S2)
    git(repo, "commit", "-qm", "F0001: start S0002")
    assert watch.last_change(repo, watch.load_config(repo)) is None
    tickets = watch.scan_tickets(repo, watch.load_config(repo))
    assert [(t.ticket_id, t.stage) for t in tickets] == [
        ("F0001-S0001", "ready"),
        ("F0001-S0002", "ready"),
    ]


def test_archiving_a_story_takes_it_off_the_board(repo: Path) -> None:
    done = FEATURES / "F0001-thing" / "done" / "F0001-S0001-thing.md"
    (repo / done).parent.mkdir()
    git(repo, "mv", S1, done.as_posix())
    write_story(repo, done.as_posix(), "done")  # stage and folder change in the same commit
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "ticket F0001-S0001: accept → done (pull request merged)")
    assert watch.last_change(repo, watch.load_config(repo)) is None
    # the feature is complete now: its acceptance is due, and that is the only ticket left
    tickets = watch.scan_tickets(repo, watch.load_config(repo))
    assert [(t.ticket_id, t.stage) for t in tickets] == [("F0001-thing", "feature")]
    assert watch.evaluate_repo(repo) == f"run acceptor {ACCEPT} main"


ACCEPT = "factory/features/F0001-thing/ACCEPTANCE.md"
AB = "acceptance/F0001-thing"


def archive(repo: Path, rel: str, subject: str) -> None:
    done = Path(rel).parent.parent / "done" / Path(rel).name
    (repo / done).parent.mkdir(exist_ok=True)
    git(repo, "mv", rel, done.as_posix())
    write_story(repo, done.as_posix(), "done")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", subject)


def write_report(repo: Path, stage: str, stories: list[str], pr: int | None = None) -> None:
    pr_line = f"pr: {pr}\n" if pr else ""
    (repo / ACCEPT).write_text(
        f"---\nstage: {stage}\n{pr_line}stories: [{', '.join(stories)}]\n---\n# Acceptance\n"
    )


def test_acceptance_is_not_due_while_a_story_is_drafted_or_running(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    draft = FEATURES / "F0001-thing" / "drafts" / "F0001-S0002-thing.md"
    (repo / draft).parent.mkdir()
    (repo / draft).write_text("# Second\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "F0001: draft S0002")
    assert watch.evaluate_repo(repo) == "idle"
    git(repo, "mv", draft.as_posix(), S2)
    git(repo, "commit", "-qm", "F0001: start S0002")
    assert watch.evaluate_repo(repo) == f"run intake {S2} main"


def test_acceptance_runs_once_per_set_of_archived_stories(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    write_report(repo, "done", ["F0001-S0001"])
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "F0001: acceptance done")
    assert watch.evaluate_repo(repo) == "idle"  # the report covers every archived story
    write_story(repo, S2)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "F0001: start S0002")
    archive(repo, S2, "ticket F0001-S0002: accept → done")
    assert watch.evaluate_repo(repo) == f"run acceptor {ACCEPT} main"  # a new story: due again


def test_running_acceptance_is_read_from_its_branch_and_waits_at_the_gate(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    git(repo, "checkout", "-qb", AB)
    write_report(repo, "accept", ["F0001-S0001"], pr=9)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "acceptance F0001-thing: feature → accept")
    git(repo, "checkout", "-q", "main")
    tickets = watch.scan_tickets(repo, watch.load_config(repo))
    assert [(t.ticket_id, t.stage, t.branch) for t in tickets] == [("F0001-thing", "accept", AB)]
    config = watch.load_config(repo)
    line = watch.evaluate(config, tickets, None, NOW, lambda _t: ("OPEN", 1))
    assert line == f"pr {ACCEPT} OPEN 1"
    line = watch.evaluate(config, tickets, None, NOW, lambda _t: ("MERGED", 1))
    assert line == f"merged {ACCEPT} {AB}"


def test_a_merged_acceptance_with_drafts_is_reported_until_it_is_booked(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    git(repo, "checkout", "-qb", AB)
    write_report(repo, "accept", ["F0001-S0001"], pr=9)
    draft = repo / FEATURES / "F0001-thing" / "drafts" / "F0001-S0002-proposed.md"
    draft.parent.mkdir()
    draft.write_text("# Proposed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "acceptance F0001-thing: feature → accept")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge pull request #9", AB)
    # the branch is merged (absent) and drafts/ is not empty, yet the merge needs its line
    config = watch.load_config(repo)
    tickets = watch.scan_tickets(repo, config)
    assert [(t.ticket_id, t.stage) for t in tickets] == [("F0001-thing", "accept")]
    line = watch.evaluate(config, tickets, None, NOW, lambda _t: ("MERGED", 1))
    assert line == f"merged {ACCEPT} {AB}"
    write_report(repo, "done", ["F0001-S0001"], pr=9)  # the dispatcher's bookkeeping
    git(repo, "commit", "-qam", "acceptance F0001-thing: accept → done (pull request merged)")
    assert watch.evaluate_repo(repo) == "idle"
    # drafts, ongoing, done, acceptance: the proposed draft does not hide the verdict
    assert watch.board(repo).splitlines()[1].split()[-4:] == ["1", "0", "1", "accepted"]


def test_a_report_with_non_ascii_text_is_read_whatever_the_locale(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    write_report(repo, "done", ["F0001-S0001"])
    with (repo / ACCEPT).open("a", encoding="utf-8") as fh:
        fh.write("`STRASSE` finds `Straße`, `ÁRVÍZ` finds `árvíz`\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "acceptance F0001-thing: closed by the human")
    # read through git show in the field; a Windows locale decoded it as cp1252, where the
    # second byte of `Á` (0x81) is undefined, the reader thread died and the report was lost
    assert watch.git(repo, "show", f"HEAD:{ACCEPT}").endswith("`ÁRVÍZ` finds `árvíz`\n")
    assert watch.evaluate_repo(repo) == "idle"


def test_acceptance_sorts_after_the_feature_s_stories_and_before_the_next_feature() -> None:
    accept = watch.Ticket(Path(ACCEPT), {"stage": "feature"})
    tickets = sorted(
        [ticket("ready", "F0002-S0001"), accept, ticket("doing", "F0001-S0002")],
        key=lambda t: t.ticket_id,
    )
    assert [t.ticket_id for t in tickets] == ["F0001-S0002", "F0001-thing", "F0002-S0001"]
    assert accept.feature == "F0001-thing"


def test_ticket_is_read_from_its_branch_when_one_exists(repo: Path) -> None:
    git(repo, "checkout", "-qb", B1)
    set_stage(repo, "doing", "ticket F0001-S0001: tests → doing")
    git(repo, "checkout", "-q", "main")
    tickets = watch.scan_tickets(repo, watch.load_config(repo))
    assert [t.stage for t in tickets] == ["doing"]
    assert watch.evaluate_repo(repo) == f"run coder {S1} {B1}"


def test_merged_branch_is_ignored_even_if_its_ref_remains(repo: Path) -> None:
    git(repo, "checkout", "-qb", B1)
    set_stage(repo, "accept", "ticket F0001-S0001: demo → accept")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge pull request #1", B1)
    set_stage(repo, "done", "ticket F0001-S0001: accept → done (pull request merged)")
    tickets = watch.scan_tickets(repo, watch.load_config(repo))
    assert [t.stage for t in tickets] == ["done"]
    assert watch.evaluate_repo(repo) == "idle"


def test_pull_request_merge_into_main_is_not_rejected(repo: Path) -> None:
    git(repo, "checkout", "-qb", B1)
    set_stage(repo, "accept", "ticket F0001-S0001: demo → accept")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge pull request #1", B1)
    # main went ready → accept in one commit: illegal as a stage edit, but that is how merges look
    assert watch.last_change(repo, watch.load_config(repo)) is None


def test_merging_main_into_the_branch_is_not_a_stage_change(repo: Path) -> None:
    git(repo, "checkout", "-qb", B1)
    set_stage(repo, "doing", "ticket F0001-S0001: tests → doing")
    git(repo, "checkout", "-q", "main")
    write_story(repo, "factory/features/F0002-new/ongoing/F0002-S0001-new.md")
    (repo / "factory" / "note.md").write_text("factory change on main\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "chore: feature F0002 and a factory change")
    git(repo, "checkout", "-q", B1)
    git(repo, "merge", "-q", "--no-edit", "-m", "ticket F0001-S0001: merge main", "main")
    assert watch.last_change(repo, watch.load_config(repo)) is None
    assert watch.evaluate_repo(repo) == f"run coder {S1} {B1}"


def test_tickets_without_a_branch_are_read_from_origin_main(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    remote = tmp_path_factory.mktemp("remote")
    origin = remote / "origin.git"
    git(repo, "init", "-q", "--bare", "-b", "main", str(origin))
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    # the human lands a new story on main while this checkout sits on a story branch
    other = remote / "other"
    git(repo, "clone", "-q", "-b", "main", str(origin), str(other))
    write_story(other, S2)
    identity = ("-c", "user.name=t", "-c", "user.email=t@example.invalid")
    git(other, *identity, "add", "-A")
    git(other, *identity, "commit", "-qm", "F0001: start S0002")
    git(other, "push", "-q", "origin", "main")
    git(repo, "checkout", "-qb", B1)
    set_stage(repo, "tests", "ticket F0001-S0001: ready → tests")
    git(repo, "fetch", "-q", "origin")
    ids = [t.ticket_id for t in watch.scan_tickets(repo, watch.load_config(repo))]
    assert ids == ["F0001-S0001", "F0001-S0002"]
    assert watch.evaluate_repo(repo) == f"run tester {S1} {B1}"


def test_follow_remembers_its_last_line_across_restarts(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    watch.follow(repo, interval=0, pr_every=15, max_ticks=1)
    assert capsys.readouterr().out == f"run intake {S1} main\n"
    watch.follow(repo, interval=0, pr_every=15, max_ticks=1)  # re-armed, nothing changed
    assert capsys.readouterr().out == ""
    set_stage(repo, "tests", "ticket F0001-S0001: ready → tests")
    watch.follow(repo, interval=0, pr_every=15, max_ticks=1)
    assert capsys.readouterr().out == f"run tester {S1} {B1}\n"


def test_board_shows_feature_counts_and_live_stories(repo: Path) -> None:
    archive = repo / FEATURES / "F0001-thing" / "done"
    archive.mkdir()
    (archive / "F0001-S0000-old.md").write_text("# Old\n")
    lines = watch.board(repo).splitlines()
    assert lines[1].startswith("F0001-thing")
    assert lines[1].split()[-4:] == ["0", "1", "1", "-"]  # drafts, ongoing, done, acceptance
    story_rows = [line for line in lines if line.startswith("F0001-S0001")]
    assert len(story_rows) == 1 and "ready" in story_rows[0]


def test_board_shows_the_acceptance_status_of_each_feature(repo: Path) -> None:
    archive(repo, S1, "ticket F0001-S0001: accept → done")
    assert watch.board(repo).splitlines()[1].split()[-1] == "due"
    write_report(repo, "done", ["F0001-S0001"])
    (repo / ACCEPT).write_text(
        (repo / ACCEPT).read_text().replace("---\n# ", "outcome: refused\n---\n# ", 1)
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "acceptance F0001-thing: closed by the human")
    assert watch.board(repo).splitlines()[1].split()[-1] == "refused"
    git(repo, "checkout", "-qb", AB)
    write_report(repo, "accept", ["F0001-S0001"], pr=9)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "acceptance F0001-thing: feature → accept")
    git(repo, "checkout", "-q", "main")
    assert watch.board(repo).splitlines()[1].split()[-1] == "running"
