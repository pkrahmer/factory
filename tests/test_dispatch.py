"""The line handlers, against a throwaway repository with a bare `origin`, a fake GitHub and a
fake agent. Every path the dispatcher skill described is here, including the ones no live run
has walked: the attempts cap and its retry, `reject`, an intake run on an existing branch."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from factory import agent, dispatch, github, stage, story, watch

STAGES_YML = """version: 5
root: factory/features
lease_minutes: 60
max_attempts: 2
lanes:
  intake:     ["factory/features/*/ongoing/*.md"]
  tester:     ["factory/features/*/ongoing/*.md", "tests/*"]
  coder:      ["factory/features/*/ongoing/*.md", "src/*"]
  reviewer:   ["factory/features/*/ongoing/*.md"]
  documenter: ["factory/features/*/ongoing/*.md", "README.md", "docs/*"]
  demo:       ["factory/features/*/ongoing/*.md"]
  acceptor:   ["factory/features/*/ACCEPTANCE.md", "factory/features/*/drafts/*.md"]
stages:
  ready: {agent: intake, next: [tests]}
  tests: {agent: tester, next: [doing], checks: [lint], records: [test]}
  doing: {agent: coder, next: [review, tests], checks: [check]}
  review: {agent: reviewer, next: [docs, doing], max_rounds: 2}
  docs: {agent: documenter, next: [demo, doing], max_rounds: 2, checks: [check]}
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
    created: list[tuple[str, str, str]] = field(default_factory=list)
    bodies: dict[int, str] = field(default_factory=dict)

    def create_draft(self, head: str, title: str, body: str) -> int:
        self.created.append((head, title, body))
        return 8 + len(self.created)

    def find(self, head: str) -> int | None:
        return next((8 + n for n, c in enumerate(self.created, 1) if c[0] == head), None)

    def edit_body(self, pr: int, body: str) -> None:
        self.bodies[pr] = body

    def ready(self, pr: int) -> None:
        self.calls.append(f"ready {pr}")

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
    schemas: list[dict[str, Any]] = field(default_factory=list)
    agent: Callable[[Path], agent.AgentRun] = lambda _root: agent.AgentRun(ok=True)
    gate_results: dict[str, tuple[bool, str]] = field(
        default_factory=lambda: {
            "check": (True, "check: green"),
            "lint": (True, "lint: green"),
            "test": (False, "1 failed, 3 passed"),
        }
    )
    gated: list[str] = field(default_factory=list)

    def context(self) -> dispatch.Context:
        def start(name: str, message: str, schema: dict[str, Any]) -> agent.AgentRun:
            self.started.append((name, message))
            self.schemas.append(schema)
            return self.agent(self.root)

        def gate(target: str) -> tuple[bool, str]:
            self.gated.append(target)
            return self.gate_results[target]

        return dispatch.Context(
            root=self.root,
            config=watch.load_config(self.root),
            github=self.gh,
            start=start,
            today="2026-10-05",
            gate=gate,
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
    assert (meta["stage"], meta["blocked"]) == ("done", None)
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
    assert (meta["stage"], meta["outcome"]) == ("done", "refused")
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
    world.on_branch(B1, stage="tests", blocked="question")
    with_entry(world, "tester: criterion 6 calls list(open_only=True); which is meant?")
    assert world.handle(f"ask {S1}").ok
    assert world.gh.posts(7) == [
        f"tester: criterion 6 calls list(open_only=True); which is meant?\n\n{github.MARKER}"
    ]
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["blocked"], meta["comments_seen"]) == ("asked", 1)
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


def test_an_expired_run_is_cleared_and_counted(world: World) -> None:
    world.on_branch(B1, stage="review", claimed_at="2026-10-05T08:00:00Z", comments_seen=3)
    watch.write_running(world.root, watch.Running(S1, watch.parse_timestamp("2026-10-05T08:00Z")))
    world.gh.comments[7] = [github.Comment("x", "2026-10-05", own=False)] * 3
    assert world.handle(f"expired {S1}").ok
    assert watch.read_running(world.root) is None
    meta = world.meta(S1, f"origin/{B1}")
    assert "claimed_at" not in meta  # a field of contract version 4, dropped on the next write
    assert (meta["attempts"], meta["comments_seen"]) == (1, 4)
    assert story.last_entry(world.read(S1, f"origin/{B1}")).startswith("run expired")
    assert world.gh.posts(7) == [
        "Stage review stalled: its run ended without finishing (attempt 1 of 2). Retrying."
        f"\n\n{github.MARKER}"
    ]


# --- run -------------------------------------------------------------------------------------


def outcome(
    result: str | None,
    entry: str = "done",
    *,
    edits: dict[str, str] | None = None,
    commit: str | None = None,
    ok: bool = True,
) -> Callable[[Path], agent.AgentRun]:
    """A fake agent: it edits files, maybe commits, and ends with an outcome."""

    def act(root: Path) -> agent.AgentRun:
        for path, text in (edits or {}).items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="")
        if commit:
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", commit)
        structured = {"outcome": result, "entry": entry} if result else None
        return agent.AgentRun(ok=ok, structured=structured, cost=0.2, turns=7, result="handed back")

    return act


def subjects(world: World, ref: str, n: int) -> list[str]:
    return git(world.root, "log", f"-{n}", "--format=%s", ref).split("\n")[:n]


def test_intake_gets_a_branch_a_pull_request_and_its_task(world: World) -> None:
    world.agent = outcome("tests", "accepted; the Interface names `thing()`")
    handled = world.handle(f"run intake {S1} main")
    assert handled.ok and handled.run is not None and handled.run.cost == 0.2
    name, message = world.started[0]
    assert name == "intake"
    assert message == (
        f"Ticket: {S1}\nId: F0001-S0001\nStage: ready\n"
        "Allowed outcomes: tests, question, stuck\n"
        f"Branch: {B1}\nPull request: 9\nRound: 0\n"
        "Format check: passed\n"
        "End with your outcome and your log entry; the factory commits, pushes and moves the story."
    )
    assert world.schemas[0]["properties"]["outcome"]["enum"] == ["tests", "question", "stuck"]
    head, title, body = world.gh.created[0]
    assert (head, title) == (B1, "F0001-S0001: Thing")
    assert body.startswith("## Assignment\n\nBuild it.\n\n## Acceptance criteria\n\n1. `thing()`")
    meta = world.meta(S1, f"origin/{B1}")
    assert meta == {
        "stage": "tests",
        "pr": 9,
        "blocked": None,
        "comments_seen": 0,
        "round": 0,
        "attempts": 0,
    }
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == (
        "intake: accepted; the Interface names `thing()`"
    )
    assert subjects(world, f"origin/{B1}", 2) == [
        "ticket F0001-S0001: ready → tests",
        "ticket F0001-S0001: intake starts",
    ]
    assert world.read(S1, "origin/main") == DRAFT  # main keeps the human's text


def test_intake_after_an_answer_continues_on_the_existing_branch(world: World) -> None:
    world.on_branch(B1, stage="ready")
    git(world.root, "checkout", "-q", "main")
    world.agent = outcome("tests", "accepted with the answer of entry 2")
    assert world.handle(f"run intake {S1} main").ok
    assert f"Branch: {B1} (exists; intake asked before)\nPull request: 7\n" in world.started[0][1]
    assert world.gh.created == []
    assert world.meta(S1, f"origin/{B1}")["stage"] == "tests"


def test_a_branch_without_a_pull_request_gets_one_or_finds_its_own(world: World) -> None:
    world.on_branch(B1, stage="ready", pr=None)
    world.agent = outcome("tests", "accepted")
    assert world.handle(f"run intake {S1} main").ok
    assert world.meta(S1, f"origin/{B1}")["pr"] == 9
    assert len(world.gh.created) == 1


def test_intake_cannot_accept_a_story_the_format_check_refuses(world: World) -> None:
    world.write(S1, DRAFT.replace("Expect: `ok`.\n", ""))
    world.commit("F0001: a Demo without Expect")
    git(world.root, "push", "-q")
    world.agent = outcome("tests", "accepted")
    assert world.handle(f"run intake {S1} main").ok
    message = world.started[0][1]
    assert "Format check found: 1. Demo command block 1 has no `Expect:` line after it." in message
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["blocked"]) == ("ready", "question")
    assert story.last_entry(text) == (
        "intake: accepted\n\n"
        "The format check found what has to change before the story can start: "
        "Demo command block 1 has no `Expect:` line after it."
    )
    assert subjects(world, f"origin/{B1}", 1) == ["ticket F0001-S0001: ready asks"]


def test_the_coder_moves_on_when_the_gate_is_green(world: World) -> None:
    world.on_branch(B1, stage="doing")
    world.agent = outcome(
        "review",
        "built `thing()` in src/app.py; rejected a class",
        edits={"src/app.py": "def thing() -> None: ...\n"},
        commit="ticket F0001-S0001: feat(app): thing",
    )
    assert world.handle(f"run coder {S1} {B1}").ok
    assert world.gated == ["check"]
    assert world.meta(S1, f"origin/{B1}")["stage"] == "review"
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == (
        "coder: built `thing()` in src/app.py; rejected a class\n\n`make check`: check: green"
    )
    assert subjects(world, f"origin/{B1}", 2) == [
        "ticket F0001-S0001: doing → review",
        "ticket F0001-S0001: feat(app): thing",
    ]
    assert world.read("src/app.py", f"origin/{B1}") == "def thing() -> None: ...\n"


def test_a_red_gate_holds_the_stage_and_counts_a_stall(world: World) -> None:
    world.on_branch(B1, stage="doing")
    world.gate_results["check"] = (False, "FAILED tests/test_app.py::test_thing\n1 failed")
    world.agent = outcome("review", "done", edits={"src/app.py": "broken\n"})
    assert world.handle(f"run coder {S1} {B1}").ok
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["attempts"]) == ("doing", 1)
    assert story.entries(story.split(text)[1])[-2][1] == "coder: done"
    assert story.last_entry(text) == (
        "stage doing stalled: `make check` is red after the stage:\n"
        "FAILED tests/test_app.py::test_thing\n1 failed; partial work committed"
    )
    assert world.read("src/app.py", f"origin/{B1}") == "broken\n"
    assert world.gh.posts(7)[0].startswith("Stage doing stalled (attempt 1 of 2)")


def test_a_rework_counts_a_round_and_the_cap_asks(world: World) -> None:
    world.on_branch(B1, stage="review")
    world.agent = outcome("doing", "1. src/app.py:1 no docstring; add one")
    assert world.handle(f"run reviewer {S1} {B1}").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["round"], meta["blocked"]) == ("doing", 1, None)
    assert subjects(world, f"origin/{B1}", 1) == ["ticket F0001-S0001: review → doing"]
    assert world.gated == []
    world.write(S1, story.update(world.read(S1), stage="review", round=2))
    world.commit("ticket F0001-S0001: doing → review")
    git(world.root, "push", "-q")
    assert world.handle(f"run reviewer {S1} {B1}").ok
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["round"], meta["blocked"]) == ("review", 3, "question")
    assert story.last_entry(text) == (
        "reviewer: 1. src/app.py:1 no docstring; add one\n\n"
        "This story has now been sent back 3 times, more than 2. What should happen? "
        "Answer with a comment; close the pull request to discard the story."
    )
    assert subjects(world, f"origin/{B1}", 1) == ["ticket F0001-S0001: review asks (round cap)"]


def test_a_question_blocks_the_story_at_its_stage(world: World) -> None:
    world.on_branch(B1, stage="tests")
    world.agent = outcome("question", "Criterion 1 names `thing()`, the Interface `thing(x)`?")
    assert world.handle(f"run tester {S1} {B1}").ok
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["blocked"]) == ("tests", "question")
    assert subjects(world, f"origin/{B1}", 1) == ["ticket F0001-S0001: tests asks"]
    assert world.gated == []


@pytest.mark.parametrize(
    ("result", "ok", "reason"),
    [
        ("stuck", True, "make is not installed"),
        (None, True, "the agent gave no outcome"),
        ("accept", True, "outcome accept is not one of review, tests, question, stuck"),
        ("review", False, "error_during_execution"),
    ],
)
def test_a_run_that_did_not_finish_is_a_stall(
    world: World, result: str | None, ok: bool, reason: str
) -> None:
    world.on_branch(B1, stage="doing")

    def act(root: Path) -> agent.AgentRun:
        running = watch.read_running(root)
        assert running is not None and running.path == S1  # the run file names the story
        (root / "src" / "half.py").parent.mkdir(exist_ok=True)
        (root / "src" / "half.py").write_text("half\n")
        structured = {"outcome": result, "entry": "make is not installed"} if result else None
        return agent.AgentRun(
            ok=ok,
            reason="error_during_execution",
            structured=structured,
            denials=["Bash: git push --force"],
        )

    world.agent = act
    assert world.handle(f"run coder {S1} {B1}").ok
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["attempts"], meta["comments_seen"]) == ("doing", 1, 1)
    assert story.last_entry(text) == (
        f"stage doing stalled: {reason}; denied: Bash: git push --force; partial work committed"
    )
    assert world.read("src/half.py", f"origin/{B1}") == "half\n"
    assert subjects(world, f"origin/{B1}", 1) == ["ticket F0001-S0001: doing stalled"]
    assert watch.read_running(world.root) is None


def test_writes_outside_the_lane_and_to_the_frontmatter_are_undone(world: World) -> None:
    other = f"{FEATURE}/ongoing/F0001-S0002-other.md"
    world.write(other, DRAFT)
    world.commit("F0001: start S0002")
    git(world.root, "push", "-q")
    world.on_branch(B1, stage="review")
    meta, body = story.split(world.read(S1))
    tampered = story.render({**meta, "stage": "accept"}, story.append(body, "reviewer: my own"))
    world.agent = outcome(
        "docs",
        "pass",
        edits={S1: tampered, "src/hack.py": "x = 1\n", other: "# overwritten\n"},
    )
    assert world.handle(f"run reviewer {S1} {B1}").ok
    text = world.read(S1, f"origin/{B1}")
    assert watch.parse_frontmatter(text)["stage"] == "docs"
    assert [t for _n, t in story.entries(story.split(text)[1])] == [
        "human: created.",
        "reviewer: pass\n\n"
        f"The factory undid changes outside the reviewer's lane: {other}, src/hack.py",
    ]
    assert world.read(other, f"origin/{B1}") == DRAFT
    with pytest.raises(subprocess.CalledProcessError):
        world.read("src/hack.py", f"origin/{B1}")
    assert not (world.root / "src" / "hack.py").exists()


def test_the_tester_leaves_tests_red_and_lint_green(world: World) -> None:
    world.on_branch(B1, stage="tests")
    world.agent = outcome("doing", "criterion 1: test_thing_returns", edits={"tests/t.py": "x\n"})
    assert world.handle(f"run tester {S1} {B1}").ok
    assert world.gated == ["lint", "test"]
    assert world.meta(S1, f"origin/{B1}")["stage"] == "doing"
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == (
        "tester: criterion 1: test_thing_returns\n\n`make lint`: lint: green\n"
        "`make test`: 1 failed, 3 passed"
    )
    world.write(S1, story.update(world.read(S1), stage="tests"))
    world.commit("ticket F0001-S0001: back to tests")
    git(world.root, "push", "-q")
    world.gate_results["lint"] = (False, "tests/t.py:1: F821 undefined name")
    world.gated.clear()
    assert world.handle(f"run tester {S1} {B1}").ok
    assert world.gated == ["lint"]
    meta = world.meta(S1, f"origin/{B1}")
    assert (meta["stage"], meta["attempts"]) == ("tests", 1)


def test_the_tester_is_told_when_it_makes_an_approved_test_change(world: World) -> None:
    world.on_branch(B1, stage="tests")
    meta, body = story.split(world.read(S1))
    body = story.append(body, "coder: criterion 1 says `blank`, test_thing expects `empty`")
    world.write(S1, story.render(meta, body))
    world.commit("ticket F0001-S0001: doing → tests (test change approved)")
    git(world.root, "push", "-q")
    world.agent = outcome("doing", "changed test_thing to `blank`")
    assert world.handle(f"run tester {S1} {B1}").ok
    message = world.started[0][1]
    assert "Mode: a test change the human approved; the coder's entry 2 names it.\n" in message


DEMO_ENTRIES = (
    "tester: criterion 1: test_thing_returns",
    "reviewer: no findings",
    "documenter: README mentions thing()",
)


def test_demo_hands_over_with_the_pull_request_body_from_the_story(world: World) -> None:
    world.on_branch(B1, stage="demo")
    meta, body = story.split(world.read(S1))
    for entry in DEMO_ENTRIES:
        body = story.append(body, entry)
    world.write(S1, story.render(meta, body))
    world.commit("ticket F0001-S0001: docs → demo")
    git(world.root, "push", "-q")
    world.agent = outcome("accept", "1 command, as expected:\n```\nok\n```")
    assert world.handle(f"run demo {S1} {B1}").ok
    assert world.meta(S1, f"origin/{B1}")["stage"] == "accept"
    assert "ready 7" in world.gh.calls
    pr_body = world.gh.bodies[7]
    for part in (
        "## Assignment\n\nBuild it.",
        "## Acceptance criteria\n\n1. `thing()` returns.",
        "## Tests\n\ntester: criterion 1: test_thing_returns",
        "## Review\n\nreviewer: no findings",
        "## Documentation\n\ndocumenter: README mentions thing()",
        "## Demo\n\ndemo: 1 command, as expected:\n```\nok\n```",
        "## Commits\n\n",
        "ticket F0001-S0001: demo → accept",
        "This is the last story of F0001-thing; merging completes the feature.",
        stage.STORY_CLOSING,
    ):
        assert part in pr_body, part


def test_the_acceptor_gets_its_branch_report_and_facts(world: World) -> None:
    done = f"{FEATURE}/done/F0001-S0001-thing.md"
    (world.root / FEATURE / "done").mkdir()
    git(world.root, "mv", S1, done)
    meta, body = story.split(DRAFT)
    body = story.append(
        body,
        "done (pull request merged); cost: 6 runs, 7.3 min, 30 turns, "
        "114k tokens in (769k more from cache), 5k out, $1.92",
    )
    world.write(done, story.render({"stage": "done"}, body))
    world.commit("ticket F0001-S0001: accept → done (pull request merged)")
    git(world.root, "push", "-q")
    report = (
        "---\nstage: feature\n---\n# Acceptance of Thing\n\n## Verdict\n\naccepted with drafts: "
        "one survivor\n\n## 1 Scope\n\nnone\n\n## Proposed stories\n\n- F0001-S0002 pin it\n"
    )
    world.agent = outcome(
        "accept",
        "accepted with drafts; 1 draft proposed; make mutants 9/10",
        edits={ACCEPT: report, f"{FEATURE}/drafts/F0001-S0002-pin.md": "# Pin it\n"},
    )
    assert world.handle(f"run acceptor {ACCEPT} main").ok
    message = world.started[0][1]
    assert f"Branch: {AB}\nPull request: 9\n" in message
    assert "Archived stories: F0001-S0001\n" in message
    assert "Next free story number: F0001-S0002\n" in message
    assert "Cost of the stories: 6 runs, 7.3 min, $1.92\n" in message
    assert world.gh.created[0][:2] == (AB, "F0001-thing: acceptance")
    text = world.read(ACCEPT, f"origin/{AB}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["pr"], meta["stories"]) == ("accept", 9, ["F0001-S0001"])
    assert "## Verdict\n\naccepted with drafts: one survivor" in text
    assert world.read(f"{FEATURE}/drafts/F0001-S0002-pin.md", f"origin/{AB}") == "# Pin it\n"
    assert subjects(world, f"origin/{AB}", 2) == [
        "acceptance F0001-thing: feature → accept",
        "acceptance F0001-thing: acceptance starts",
    ]
    pr_body = world.gh.bodies[9]
    assert pr_body.startswith("## Verdict\n\naccepted with drafts: one survivor")
    assert "## Proposed stories\n\n- F0001-S0002 pin it" in pr_body
    assert pr_body.endswith(stage.ACCEPTANCE_CLOSING)
    assert "ready 9" in world.gh.calls


def test_a_stage_that_breaks_the_storys_form_is_held(world: World) -> None:
    world.on_branch(B1, stage="doing")
    broken = world.read(S1).replace("Expect: `ok`.\n", "")
    world.agent = outcome("review", "built it", edits={S1: broken})
    assert world.handle(f"run coder {S1} {B1}").ok
    text = world.read(S1, f"origin/{B1}")
    meta = watch.parse_frontmatter(text)
    assert (meta["stage"], meta["attempts"]) == ("doing", 1)
    assert story.last_entry(text) == (
        "stage doing stalled: the story's form broke: Demo command block 1 has no `Expect:` "
        "line after it; partial work committed"
    )


def test_a_stage_on_its_branch_first_takes_main_in(world: World) -> None:
    world.on_branch(B1, stage="doing")
    git(world.root, "checkout", "-q", "main")
    world.write("factory/note.md", "a change on main\n")
    world.commit("F0002: draft")
    git(world.root, "push", "-q")
    world.agent = outcome("review", "built it")
    assert world.handle(f"run coder {S1} {B1}").ok
    assert (world.root / "factory" / "note.md").exists()
    assert "ticket F0001-S0001: merge main" in git(world.root, "log", "--format=%s", f"origin/{B1}")


def test_a_closed_pull_request_discards_instead_of_starting_the_agent(world: World) -> None:
    world.on_branch(B1, stage="doing")
    world.gh.states[7] = "CLOSED"
    assert world.handle(f"run coder {S1} {B1}").ok
    assert world.started == []
    assert (world.root / FEATURE / "drafts" / "F0001-S0001-thing.md").exists()


def test_a_story_that_moved_on_is_not_run_again(world: World) -> None:
    world.on_branch(B1, stage="review")
    assert world.handle(f"run coder {S1} {B1}").summary == "nothing to do"
    assert world.started == []


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


def test_an_entry_the_agent_already_prefixed_is_not_prefixed_twice(world: World) -> None:
    world.on_branch(B1, stage="review")
    world.agent = outcome("docs", "reviewer: no findings")
    assert world.handle(f"run reviewer {S1} {B1}").ok
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == "reviewer: no findings"
    world.write(S1, story.update(world.read(S1), stage="review"))
    world.commit("ticket F0001-S0001: back to review")
    git(world.root, "push", "-q")
    world.agent = outcome("docs", "review: no findings")  # the stage's name, not the agent's
    assert world.handle(f"run reviewer {S1} {B1}").ok
    assert story.last_entry(world.read(S1, f"origin/{B1}")) == "reviewer: no findings"


def test_a_red_make_is_recorded_by_its_last_own_line(world: World) -> None:
    world.on_branch(B1, stage="tests")
    world.gate_results["test"] = (
        False,
        "E   ModuleNotFoundError: No module named 'src.greet'\n"
        "FAILED (errors=1)\nmake: *** [Makefile:8: test] Error 1",
    )
    world.agent = outcome("doing", "criterion 1: test_greets")
    assert world.handle(f"run tester {S1} {B1}").ok
    assert story.last_entry(world.read(S1, f"origin/{B1}")).endswith(
        "`make test`: FAILED (errors=1)"
    )
