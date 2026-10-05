"""The gh wrapper: the commands it builds, the marker on every post, what it reads back."""

from __future__ import annotations

import json

import pytest

from factory import github

Call = tuple[list[str], str | None]


def recorder(stdout: str = "", code: int = 0) -> tuple[list[Call], github.Runner]:
    calls: list[Call] = []

    def run(args: list[str], stdin: str | None) -> tuple[int, str]:
        calls.append((args, stdin))
        return code, stdout

    return calls, run


def test_view_reads_state_and_comments_oldest_first() -> None:
    out = json.dumps(
        {
            "state": "OPEN",
            "comments": [
                {"body": "a question", "createdAt": "2026-10-05T09:00:00Z"},
                {"body": "an answer", "createdAt": "2026-10-05T10:30:00Z"},
            ],
        }
    )
    calls, run = recorder(out)
    pr = github.GitHub(run).view(7)
    assert calls[0][0] == ["gh", "pr", "view", "7", "--json", "state,comments"]
    assert pr.state == "OPEN"
    assert [(c.body, c.date) for c in pr.comments] == [
        ("a question", "2026-10-05"),
        ("an answer", "2026-10-05"),
    ]


def test_every_post_carries_the_marker() -> None:
    calls, run = recorder()
    github.GitHub(run).comment(7, "Stage review stalled.")
    args, stdin = calls[0]
    assert args == ["gh", "pr", "comment", "7", "--body-file", "-"]
    assert stdin == f"Stage review stalled.\n\n{github.MARKER}"


def test_own_comments_are_known_by_marker_or_the_old_prefix() -> None:
    assert github.is_own(f"Retrying.\n\n{github.MARKER}")
    assert github.is_own("factory: cost of this ticket so far")
    assert not github.is_own("please rename the module")


def test_human_comments_skip_the_factorys_own() -> None:
    comments = [
        github.Comment("asked", "2026-10-05", own=True),
        github.Comment("yes, 200", "2026-10-05", own=False),
    ]
    assert [c.body for c in github.human(comments)] == ["yes, 200"]


def test_a_failing_gh_raises() -> None:
    _, run = recorder(code=1)
    with pytest.raises(github.GitHubError):
        github.GitHub(run).view(7)


def test_reopen_reports_success_and_ready_undo_is_a_draft() -> None:
    calls, run = recorder()
    gh = github.GitHub(run)
    assert gh.reopen(7)
    gh.to_draft(7)
    assert [c[0] for c in calls] == [
        ["gh", "pr", "reopen", "7"],
        ["gh", "pr", "ready", "--undo", "7"],
    ]
    _, failing = recorder(code=1)
    assert not github.GitHub(failing).reopen(7)
