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


def test_a_draft_is_created_for_the_branch_and_its_number_read_from_the_url() -> None:
    calls, run = recorder("https://github.com/o/r/pull/12\n")
    assert github.GitHub(run).create_draft("ticket/F0001-S0001-x", "F0001-S0001: X", "body") == 12
    args, stdin = calls[0]
    assert args == [
        "gh",
        "pr",
        "create",
        "--draft",
        "--head",
        "ticket/F0001-S0001-x",
        "--title",
        "F0001-S0001: X",
        "--body-file",
        "-",
    ]
    assert stdin == "body"


def test_an_open_pull_request_is_found_by_its_branch_a_closed_one_is_not() -> None:
    _, run = recorder(json.dumps({"number": 5, "state": "OPEN"}))
    assert github.GitHub(run).find("ticket/x") == 5
    _, closed = recorder(json.dumps({"number": 4, "state": "CLOSED"}))
    assert github.GitHub(closed).find("ticket/x") is None  # a discarded story came back
    _, none = recorder(code=1)
    assert github.GitHub(none).find("ticket/x") is None


def test_the_body_is_replaced_and_the_pull_request_marked_ready() -> None:
    calls, run = recorder()
    gh = github.GitHub(run)
    gh.edit_body(7, "## Assignment")
    gh.ready(7)
    assert calls == [
        (["gh", "pr", "edit", "7", "--body-file", "-"], "## Assignment"),
        (["gh", "pr", "ready", "7"], None),
    ]
