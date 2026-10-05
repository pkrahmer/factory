"""The guard hook refuses writes outside an agent's lane and anything owned by the human.
Lanes are glob patterns from `factory/stages.yml` in the repository the hook runs in."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from factory import guard

LANES = (
    "lanes:\n"
    '  tester: ["factory/features/*/ongoing/*.md", "tests/*"]\n'
    '  coder: ["factory/features/*/ongoing/*.md", "src/*"]\n'
    '  demo: ["factory/features/*/ongoing/*.md"]\n'
    '  acceptor: ["factory/features/*/ACCEPTANCE.md", "factory/features/*/drafts/*.md"]\n'
)
STORY = "factory/features/F0001-thing/ongoing/F0001-S0001-thing.md"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "factory").mkdir()
    (tmp_path / "factory" / "stages.yml").write_text(LANES)
    return tmp_path


def run(monkeypatch: pytest.MonkeyPatch, repo: Path, path: str, agent: str) -> int:
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(repo / path)}}))
    )
    return guard.main(["guard.py", agent])


def test_lane_allows_its_own_patterns(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    assert run(monkeypatch, repo, "tests/domain/test_x.py", "tester") == 0
    assert run(monkeypatch, repo, STORY, "tester") == 0
    assert run(monkeypatch, repo, "src/app/deep/down/x.py", "coder") == 0


def test_lane_refuses_other_folders(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    assert run(monkeypatch, repo, "src/app/x.py", "tester") == 2
    assert run(monkeypatch, repo, "tests/test_x.py", "coder") == 2


@pytest.mark.parametrize(
    "path",
    [
        "factory/features/F0001-thing/drafts/F0001-S0002-thing.md",
        "factory/features/F0001-thing/done/F0001-S0000-old.md",
        "factory/features/F0002-other/README.md",
    ],
)
def test_only_ongoing_stories_are_in_the_lane(
    monkeypatch: pytest.MonkeyPatch, repo: Path, path: str
) -> None:
    assert run(monkeypatch, repo, path, "coder") == 2


def test_agent_without_a_lane_writes_nothing(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    assert run(monkeypatch, repo, STORY, "stranger") == 2


def test_lanes_are_read_from_the_repository_config(
    monkeypatch: pytest.MonkeyPatch, repo: Path
) -> None:
    (repo / "factory" / "stages.yml").write_text('lanes:\n  coder: ["lib/*"]\n')
    assert run(monkeypatch, repo, "lib/x.py", "coder") == 0
    assert run(monkeypatch, repo, "src/x.py", "coder") == 2


@pytest.mark.parametrize(
    "path",
    [
        ".claude/agents/coder.md",
        "pyproject.toml",
        "uv.lock",
        "Makefile",
        "CLAUDE.md",
        "factory/stages.yml",
        "factory/TICKET.md",
        "factory/features/F0001-thing/FEATURE.md",
    ],
)
def test_human_owned_files_are_refused_in_every_lane(
    monkeypatch: pytest.MonkeyPatch, repo: Path, path: str
) -> None:
    (repo / "factory" / "stages.yml").write_text(
        'lanes:\n  coder: ["*"]\n'  # even a lane covering everything does not reach them
    )
    assert run(monkeypatch, repo, path, "coder") == 2


def test_outside_the_repository_is_refused(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"tool_input": {"file_path": "/etc/hosts"}}))
    )
    assert guard.main(["guard.py", "coder"]) == 2


def test_calls_without_a_path_pass(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": "ls"}})))
    assert guard.main(["guard.py", "coder"]) == 0


def test_the_acceptor_writes_the_report_and_drafts_and_nothing_else(
    monkeypatch: pytest.MonkeyPatch, repo: Path
) -> None:
    assert run(monkeypatch, repo, "factory/features/F0001-thing/ACCEPTANCE.md", "acceptor") == 0
    assert (
        run(monkeypatch, repo, "factory/features/F0001-thing/drafts/F0001-S0006-x.md", "acceptor")
        == 0
    )
    assert run(monkeypatch, repo, STORY, "acceptor") == 2
    assert run(monkeypatch, repo, "factory/features/F0001-thing/FEATURE.md", "acceptor") == 2
    assert (
        run(monkeypatch, repo, "factory/features/F0001-thing/done/F0001-S0001-x.md", "acceptor")
        == 2
    )
