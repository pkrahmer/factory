"""The line handlers, against a throwaway repository with a bare `origin`, a fake GitHub and a
fake agent. Every path the dispatcher skill described is here, including the ones no live run
has walked: the attempts cap and its retry, `reject`, an intake run on an existing branch."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from factory import agent, dispatch, github, story, watch

STAGES_YML = """version: 4
root: factory/features
lease_minutes: 60
max_attempts: 2
stages:
  ready: {agent: intake, next: [tests]}
  tests: {agent: tester, next: [doing]}
  doing: {agent: coder, next: [review, tests]}
  review: {agent: reviewer, next: [docs, doing], max_rounds: 2}
  docs: {agent: documenter, next: [demo, doing], max_rounds: 2}
  demo: {agent: demo, next: [accept, doing], max_rounds: 2}
  accept: {agent: null, gate: human, next: [done, doing]}
  feature: {agent: acceptor, next: [accept]}
  done: {agent: null, next: []}
"""
FEATURE = "factory/features/F0001-thing"
S1 = f"{FEATURE}/ongoing/F0001-S0001-thing.md"
B1 = "ticket/F0001-S0001-thing"
ACCEPT = f"{FEATURE}/ACCEPTANCE.md"
AB = "acceptance/F0001-thing"
DRAFT = """# Thing

## Assignment

Build it.

## Interface

`thing() -> None`

## Acceptance criteria

1. `thing()` returns.
2. `make check` stays green.
3. docs: none (internal).

## Demo

```bash
uv run python -c "print('ok')"
```
Expect: `ok`.

## Log (append only)

1. human: created.
"""
FORM = "# <Title>\n\n## Assignment\n\n## Interface\n\n## Acceptance criteria\n\n## Demo\n\n## Log\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, encoding="utf-8"
    ).stdout


@dataclass
class FakeGitHub:
    states: dict[int, str] = field(default_factory=dict)
    comments: dict[int, list[github.Comment]] = field(default_factory=dict)
    reopen_works: bool = True
    calls: list[str] = field(default_factory=list)

    def view(self, pr: int) -> github.PullRequest:
        return github.PullRequest(self.states.get(pr, "OPEN"), list(self.comments.get(pr, [])))

    def comment(self, pr: int, body: str) -> None:
        text = f"{body}\n\n{github.MARKER}"
        self.comments.setdefault(pr, []).append(github.Comment(text, "2026-10-05", own=True))
        self.calls.append(f"comment {pr}")

    def reopen(self, pr: int) -> bool:
        self.calls.append(f"reopen {pr}")
        if self.reopen_works:
            self.states[pr] = "OPEN"
        return self.reopen_works

    def to_draft(self, pr: int) -> None:
        self.calls.append(f"draft {pr}")

    def human_says(self, pr: int, *bodies: str) -> None:
        for body in bodies:
            self.comments.setdefault(pr, []).append(github.Comment(body, "2026-10-05", own=False))

    def posts(self, pr: int) -> list[str]:
        return [c.body for c in self.comments.get(pr, []) if c.own]


@dataclass
class World:
    root: Path
    gh: FakeGitHub
    started: list[tuple[str, str]] = field(default_factory=list)
    agent: Callable[[Path], agent.AgentRun] = lambda _root: agent.AgentRun(ok=True)

    def context(self) -> dispatch.Context:
        def start(name: str, message: str) -> agent.AgentRun:
            self.started.append((name, message))
            return self.agent(self.root)

        return dispatch.Context(
            root=self.root,
            config=watch.load_config(self.root),
            github=self.gh,
            start=start,
            today="2026-10-05",
        )

    def handle(self, line: str) -> dispatch.Handled:
        return dispatch.handle(self.context(), line)

    def read(self, path: str, ref: str = "HEAD") -> str:
        return git(self.root, "show", f"{ref}:{path}")

    def meta(self, path: str, ref: str = "HEAD") -> dict[str, object]:
        return watch.parse_frontmatter(self.read(path, ref))

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="")

    def commit(self, subject: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", subject)

    def on_branch(self, branch: str, path: str = S1, **meta: object) -> None:
        """Create `branch` from main with the story at the given frontmatter, pushed."""
        git(self.root, "checkout", "-q", "main")
        git(self.root, "checkout", "-q", "-b", branch)
        fields = {
            "stage": "doing",
            "pr": 7,
            "blocked": None,
            "comments_seen": 0,
            "claimed_at": None,
            "round": 0,
            "attempts": 0,
            **meta,
        }
        self.write(path, story.render(fields, story.split(DRAFT)[1]))
        self.commit(f"ticket F0001-S0001: {fields['stage']}")
        git(self.root, "push", "-q", "-u", "origin", branch)

    def merge_on_github(self, branch: str) -> None:
        git(self.root, "checkout", "-q", "main")
        git(self.root, "merge", "-q", "--no-ff", "-m", "Merge pull request #7", branch)
        git(self.root, "push", "-q", "origin", "main")
        git(self.root, "checkout", "-q", branch)

    def tip(self, ref: str) -> str:
        return git(self.root, "rev-parse", ref).strip()


@pytest.fixture
def world(tmp_path: Path) -> World:
    origin = tmp_path / "origin.git"
    root = tmp_path / "work"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "init", "-q", "-b", "main", str(root))
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "remote", "add", "origin", str(origin))
    w = World(root, FakeGitHub())
    w.write("factory/stages.yml", STAGES_YML)
    w.write("factory/TICKET.md", FORM)
    w.write(f"{FEATURE}/FEATURE.md", "# Thing\n")
    w.write(S1, DRAFT)
    w.commit("F0001: start S0001")
    git(root, "push", "-q", "-u", "origin", "main")
    return w


# --- merged ----------------------------------------------------------------------------------


def test_a_merged_story_is_archived_on_main_and_its_branch_deleted(world: World) -> None:
    world.on_branch(B1, stage="accept")
    world.merge_on_github(B1)
    handled = world.handle(f"merged {S1} {B1}")
    assert handled.ok
    done = f"{FEATURE}/done/F0001-S0001-thing.md"
    meta = world.meta(done, "origin/main")
    assert (meta["stage"], meta["blocked"], meta["claimed_at"]) == ("done", None, None)
    assert story.last_entry(world.read(done, "origin/main")).startswith(
        "done (pull request merged); cost: 0 runs"
    )
    assert git(world.root, "log", "-1", "--format=%s", "origin/main").strip() == (
        "ticket F0001-S0001: accept → done (pull request merged)"
    )
    assert not (world.root / S1).exists()
    assert git(world.root, "branch", "--list", B1).strip() == ""
    assert git(world.root, "ls-remote", "--heads", "origin", B1).strip() == ""


def test_a_merged_acceptance_is_booked_as_accepted(world: World) -> None:
    world.on_branch(AB, path=ACCEPT, stage="accept", stories=["F0001-S0000"])
    world.merge_on_github(AB)
    assert world.handle(f"merged {ACCEPT} {AB}").ok
    meta = world.meta(ACCEPT, "origin/main")
    assert (meta["stage"], meta["outcome"], meta["stories"]) == (
        "done",
        "accepted",
        ["F0001-S0000"],
    )
    assert git(world.root, "log", "-1", "--format=%s", "origin/main").strip() == (
        "acceptance F0001-thing: accept → done (pull request merged)"
    )


# --- closed ----------------------------------------------------------------------------------


def test_a_refused_acceptance_keeps_its_report_on_main_without_the_drafts(world: World) -> None:
    world.on_branch(AB, path=ACCEPT, stage="accept", stories=["F0001-S0000"])
    report = world.read(ACCEPT).replace(
        "## Assignment", "## Verdict\n\naccepted with drafts\n\n## Old"
    )
    world.write(ACCEPT, report)
    world.write(f"{FEATURE}/drafts/F0001-S0002-proposed.md", "# Proposed\n")
    world.commit("acceptance F0001-thing: feature → accept")
    git(world.root, "push", "-q")
    world.gh.human_says(7, "the order draft belongs to F0001")
    assert world.handle(f"closed {ACCEPT} {AB}").ok
    text = world.read(ACCEPT, "origin/main")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["outcome"], meta["claimed_at"]) == ("done", "refused", None)
    refusal = "Refused by the human on 2026-10-05: the order draft belongs to F0001"
    assert f"## Verdict\n\n{refusal}\n\naccepted with drafts" in text
    assert story.last_entry(text).startswith("done (pull request closed by the human); cost:")
    assert not (world.root / FEATURE / "drafts").exists()
    assert git(world.root, "ls-remote", "--heads", "origin", AB).strip() == ""


def test_a_close_at_accept_with_a_reason_sends_the_story_to_the_coder(world: World) -> None:
    world.on_branch(B1, stage="accept", comments_seen=1)
    text = story.split(world.read(S1))
    world.write(
        S1, story.render(text[0], story.append(text[1], "demo: 2 commands, all as expected"))
    )
    world.commit("ticket F0001-S0001: demo → accept")
    git(world.root, "push", "-q")
    world.gh.comments[7] = [github.Comment("factory: cost", "2026-10-05", own=True)]
    world.gh.human_says(7, "name the API Todo service")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"closed {S1} {B1}").ok
    assert world.gh.calls == ["reopen 7", "draft 7"]
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["round"], meta["blocked"], meta["comments_seen"]) == (
        "doing",
        1,
        None,
        2,
    )
    body = world.read(S1, f"origin/{B1}")
    assert story.last_entry(body) == (
        "human (pull request comment, 2026-10-05): name the API Todo service"
    )
    assert git(world.root, "log", "-1", "--format=%s", f"origin/{B1}").strip() == (
        "ticket F0001-S0001: accept → doing (pull request closed)"
    )


def test_a_silent_close_at_accept_is_answered_with_a_question(world: World) -> None:
    world.on_branch(B1, stage="accept")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"closed {S1} {B1}").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["round"], meta["blocked"], meta["comments_seen"]) == (
        "doing",
        1,
        "asked",
        1,
    )
    question = story.last_entry(world.read(S1, f"origin/{B1}"))
    assert question.startswith("The pull request was closed without a comment. What should happen?")
    assert world.gh.posts(7) == [f"{question}\n\n{github.MARKER}"]


def test_a_close_past_the_round_cap_asks_even_with_a_reason(world: World) -> None:
    world.on_branch(B1, stage="accept", round=2)
    world.gh.human_says(7, "still wrong")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"closed {S1} {B1}").ok
    question = story.last_entry(world.read(S1, f"origin/{B1}"))
    assert question.startswith("This story has now been sent back 3 times, more than 2.")
    assert world.meta(S1, f"origin/{B1}")["blocked"] == "asked"


def test_a_close_that_cannot_be_reopened_changes_nothing(world: World) -> None:
    world.on_branch(B1, stage="accept")
    world.gh.states[7] = "CLOSED"
    world.gh.reopen_works = False
    tip = world.tip(f"origin/{B1}")
    handled = world.handle(f"closed {S1} {B1}")
    assert not handled.ok and "reopen" in handled.summary
    assert world.tip(f"origin/{B1}") == tip


def test_a_close_before_accept_discards_the_story_to_drafts(world: World) -> None:
    world.on_branch(B1, stage="tests", blocked="asked")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"closed {S1} {B1}").ok
    draft = f"{FEATURE}/drafts/F0001-S0001-thing.md"
    assert world.read(draft, "origin/main") == DRAFT  # the human's text, untouched
    assert git(world.root, "log", "-1", "--format=%s", "origin/main").strip() == (
        "ticket F0001-S0001: discarded (pull request closed)"
    )
    assert git(world.root, "ls-remote", "--heads", "origin", B1).strip() == ""


# --- ask and pr ------------------------------------------------------------------------------


def with_entry(world: World, entry: str) -> None:
    meta, body = story.split(world.read(S1))
    world.write(S1, story.render(meta, story.append(body, entry)))
    world.commit("ticket F0001-S0001: asked")
    git(world.root, "push", "-q")


def test_a_question_is_posted_verbatim_and_marked_asked(world: World) -> None:
    world.on_branch(B1, stage="tests", blocked="question", claimed_at="2026-10-05T09:00:00Z")
    with_entry(world, "tester: criterion 6 calls list(open_only=True); which is meant?")
    assert world.handle(f"ask {S1}").ok
    assert world.gh.posts(7) == [
        f"tester: criterion 6 calls list(open_only=True); which is meant?\n\n{github.MARKER}"
    ]
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["blocked"], meta["comments_seen"], meta["claimed_at"]) == ("asked", 1, None)
    tip = world.tip(f"origin/{B1}")
    assert world.handle(f"ask {S1}").ok  # already asked: nothing more
    assert world.tip(f"origin/{B1}") == tip and len(world.gh.posts(7)) == 1


def test_a_question_without_a_pull_request_waits_for_the_human_on_main(world: World) -> None:
    handled = world.handle(f"ask {S1}")
    assert handled.ok and handled.summary == f"question without a pull request on {S1}"


def test_the_attempts_cap_asks_and_any_answer_retries(world: World) -> None:
    world.on_branch(B1, stage="doing", attempts=2)
    with_entry(world, "stage doing stalled: Agent type 'coder' not found; partial work committed")
    assert world.handle(f"ask {S1}").ok
    question = world.gh.posts(7)[0]
    assert question.startswith("Stage doing stalled 2 times")
    assert "Comment anything to retry" in question
    world.gh.human_says(7, "fixed the machine")
    assert world.handle(f"pr {S1} OPEN 2").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["attempts"], meta["blocked"], meta["comments_seen"]) == (0, None, 2)


def test_an_answer_is_copied_into_the_log_and_the_story_unblocked(world: World) -> None:
    world.on_branch(B1, stage="tests", blocked="asked", comments_seen=1)
    world.gh.comments[7] = [github.Comment(f"q\n\n{github.MARKER}", "2026-10-05", own=True)]
    world.gh.human_says(7, "open_only is a typo; use done=False")
    assert world.handle(f"pr {S1} OPEN 2").ok
    text = world.read(S1, f"origin/{B1}")
    assert story.last_entry(text) == (
        "human (pull request comment, 2026-10-05): open_only is a typo; use done=False"
    )
    meta = watch.parse_frontmatter(text)
    assert (meta["blocked"], meta["comments_seen"], meta["attempts"]) == (None, 2, 0)


def test_a_comment_at_the_gate_is_only_recorded(world: World) -> None:
    world.on_branch(B1, stage="accept", comments_seen=0)
    world.gh.human_says(7, "looks good so far")
    assert world.handle(f"pr {S1} OPEN 1").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["blocked"], meta["comments_seen"]) == ("accept", None, 1)


# --- reject and expired ----------------------------------------------------------------------


def test_an_illegal_stage_change_is_moved_back_and_said_on_the_pull_request(world: World) -> None:
    world.on_branch(B1, stage="tests")
    meta, body = story.split(world.read(S1))
    world.write(S1, story.render({**meta, "stage": "demo"}, body))
    world.commit("ticket F0001-S0001: tests → demo")
    assert world.handle(f"reject {S1} tests demo").ok
    assert world.meta(S1, f"origin/{B1}")["stage"] == "tests"
    subject = git(world.root, "log", "-1", "--format=%s", f"origin/{B1}").strip()
    assert subject == "ticket F0001-S0001: illegal change tests → demo, moved back"
    assert watch.last_change(world.root, watch.load_config(world.root)) is None
    assert world.gh.posts(7)[0].startswith("The stage was changed from tests to demo")


def test_an_expired_claim_is_cleared_and_counted(world: World) -> None:
    world.on_branch(B1, stage="review", claimed_at="2026-10-05T08:00:00Z", comments_seen=3)
    world.gh.comments[7] = [github.Comment("x", "2026-10-05", own=False)] * 3
    assert world.handle(f"expired {S1}").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["claimed_at"], meta["attempts"], meta["comments_seen"]) == (None, 1, 4)
    assert story.last_entry(world.read(S1, f"origin/{B1}")).startswith("claim expired")
    assert world.gh.posts(7) == [
        "Stage review stalled: its run ended without finishing (attempt 1 of 2). Retrying."
        f"\n\n{github.MARKER}"
    ]


# --- run -------------------------------------------------------------------------------------


def stage_agent(
    stage: str, path: str = S1, branch: str = B1, *, create: bool = False, **extra: object
) -> Callable[[Path], agent.AgentRun]:
    """A fake agent that moves the story to `stage` on `branch` and pushes."""

    def act(root: Path) -> agent.AgentRun:
        if create:
            git(root, "checkout", "-q", "-b", branch)
        target = root / path
        meta, body = story.split(target.read_text(encoding="utf-8"))
        fields = {
            "stage": stage,
            "pr": meta.get("pr") or 7,
            "blocked": None,
            "comments_seen": 0,
            "claimed_at": None,
            "round": 0,
            "attempts": 0,
        }
        target.write_text(
            story.render({**meta, **fields, **extra}, body), encoding="utf-8", newline=""
        )
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", f"ticket F0001-S0001: → {stage}")
        git(root, "push", "-q", "-u", "origin", branch)
        return agent.AgentRun(ok=True, cost=0.2, turns=7)

    return act


def test_intake_runs_on_main_and_is_told_to_create_the_branch(world: World) -> None:
    world.agent = stage_agent("tests", create=True)
    handled = world.handle(f"run intake {S1} main")
    assert handled.ok and handled.run is not None and handled.run.cost == 0.2
    name, message = world.started[0]
    assert name == "intake"
    assert message == (
        f"Ticket: {S1}\nId: F0001-S0001\nStage: ready\nAllowed next stages: tests\n"
        f"Branch: main; create {B1}\nPull request: none yet\n"
        "Format check: passed\n"
        "Follow your preloaded stage skill. End with a pushed commit that contains the ticket file."
    )


def test_intake_after_an_answer_continues_on_the_existing_branch(world: World) -> None:
    world.on_branch(B1, stage="ready", blocked=None)
    git(world.root, "checkout", "-q", "main")
    world.agent = stage_agent("tests")
    assert world.handle(f"run intake {S1} main").ok
    assert f"Branch: {B1} (exists; intake asked before)" in world.started[0][1]
    assert world.meta(S1, f"origin/{B1}")["stage"] == "tests"


def test_a_stage_on_its_branch_first_takes_main_in(world: World) -> None:
    world.on_branch(B1, stage="doing")
    git(world.root, "checkout", "-q", "main")
    world.write("factory/note.md", "a change on main\n")
    world.commit("F0002: draft")
    git(world.root, "push", "-q")
    world.agent = stage_agent("review")
    assert world.handle(f"run coder {S1} {B1}").ok
    assert (world.root / "factory" / "note.md").exists()
    assert "ticket F0001-S0001: merge main" in git(world.root, "log", "--format=%s", f"origin/{B1}")


def test_a_closed_pull_request_discards_instead_of_starting_the_agent(world: World) -> None:
    world.on_branch(B1, stage="doing")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"run coder {S1} {B1}").ok
    assert world.started == []
    assert (world.root / FEATURE / "drafts" / "F0001-S0001-thing.md").exists()


def test_a_claimed_or_moved_story_is_not_run_again(world: World) -> None:
    world.on_branch(B1, stage="doing", claimed_at="2026-10-05T09:00:00Z")
    assert world.handle(f"run coder {S1} {B1}").summary == "nothing to do"
    world.write(S1, story.update(world.read(S1), claimed_at=None, stage="review"))
    world.commit("ticket F0001-S0001: doing → review")
    git(world.root, "push", "-q")
    assert world.handle(f"run coder {S1} {B1}").summary == "nothing to do"
    assert world.started == []


def test_a_run_without_progress_is_a_stall_with_its_reason(world: World) -> None:
    world.on_branch(B1, stage="doing")

    def claims_then_dies(root: Path) -> agent.AgentRun:
        target = root / S1
        target.write_text(story.update(target.read_text(), claimed_at="2026-10-05T09:00:00Z"))
        (root / "src.py").write_text("half\n")
        return agent.AgentRun(
            ok=False, reason="error_during_execution", denials=["Bash: git push --force"]
        )

    world.agent = claims_then_dies
    handled = world.handle(f"run coder {S1} {B1}")
    assert handled.ok and handled.run is not None
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["attempts"], meta["claimed_at"], meta["comments_seen"]) == (
        "doing",
        1,
        None,
        1,
    )
    assert story.last_entry(text) == (
        "stage doing stalled: error_during_execution; denied: Bash: git push --force; "
        "partial work committed"
    )
    assert world.read("src.py", f"origin/{B1}") == "half\n"
    assert world.gh.posts(7)[0].startswith("Stage doing stalled (attempt 1 of 2)")


def test_a_stall_before_the_branch_exists_commits_nothing_on_main(world: World) -> None:
    world.agent = lambda _root: agent.AgentRun(ok=False, reason="agent 'intake' is not installed")
    tip = world.tip("origin/main")
    handled = world.handle(f"run intake {S1} main")
    assert not handled.ok and "intake" in handled.summary
    assert world.tip("origin/main") == tip


def test_a_conflict_with_main_is_a_stall(world: World) -> None:
    world.on_branch(B1, stage="doing")
    world.write("shared.txt", "branch\n")
    world.commit("ticket F0001-S0001: feat")
    git(world.root, "push", "-q")
    git(world.root, "checkout", "-q", "main")
    world.write("shared.txt", "main\n")
    world.commit("other")
    git(world.root, "push", "-q")
    assert world.handle(f"run coder {S1} {B1}").ok
    assert world.started == []
    meta = world.meta(S1, f"origin/{B1}")
    assert meta["attempts"] == 1
    assert "merging main conflicts" in story.last_entry(world.read(S1, f"origin/{B1}"))


def test_lines_without_work_do_nothing(world: World) -> None:
    for line in ("idle", f"busy {S1}", f"duplicate F0001-S0001 {S1} {S1}", f"error pr-lookup {S1}"):
        assert world.handle(line).ok


def test_intake_cannot_accept_a_story_the_format_check_refuses(world: World) -> None:
    world.write(S1, DRAFT.replace("Expect: `ok`.\n", ""))
    world.commit("F0001: a Demo without Expect")
    git(world.root, "push", "-q")
    world.agent = stage_agent("tests", create=True)
    assert world.handle(f"run intake {S1} main").ok
    message = world.started[0][1]
    assert "Format check found: 1. Demo command block 1 has no `Expect:` line after it." in message
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["blocked"]) == ("ready", "question")
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == (
        "format check: the story cannot start until its form is right: "
        "Demo command block 1 has no `Expect:` line after it."
    )
    assert watch.last_change(world.root, watch.load_config(world.root)) is None  # moved back
