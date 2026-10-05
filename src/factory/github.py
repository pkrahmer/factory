"""The factory's side of a pull request, through the `gh` CLI.

Everything the factory posts carries `MARKER`, an HTML comment GitHub does not show, so the
factory's own comments are told apart from the human's by the text alone (the pull requests
are opened with the owner's token, so the author does not tell them apart). Comments posted
before the marker existed start with `factory:` and count as own too.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

MARKER = "<!-- factory -->"
OLD_PREFIX = "factory:"

Runner = Callable[[list[str], str | None], tuple[int, str]]  # (args, stdin) -> (exit, stdout)


class GitHubError(RuntimeError):
    """`gh` failed; the message names the command."""


@dataclass(frozen=True)
class Comment:
    body: str
    date: str  # YYYY-MM-DD
    own: bool


@dataclass(frozen=True)
class PullRequest:
    state: str  # OPEN, MERGED or CLOSED
    comments: list[Comment]


def is_own(body: str) -> bool:
    return MARKER in body or body.startswith(OLD_PREFIX)


def human(comments: list[Comment]) -> list[Comment]:
    return [c for c in comments if not c.own]


def gh_runner(root: Path) -> Runner:
    def run(args: list[str], stdin: str | None) -> tuple[int, str]:
        proc = subprocess.run(
            args, cwd=root, input=stdin, capture_output=True, encoding="utf-8", check=False
        )
        return proc.returncode, proc.stdout

    return run


class GitHub:
    def __init__(self, run: Runner) -> None:
        self._run = run

    def _gh(self, *args: str, stdin: str | None = None) -> str:
        command = ["gh", *args]
        code, out = self._run(command, stdin)
        if code != 0:
            raise GitHubError(" ".join(command) + f" exited {code}")
        return out

    def view(self, pr: int) -> PullRequest:
        data = json.loads(self._gh("pr", "view", str(pr), "--json", "state,comments"))
        comments = []
        for raw in data.get("comments") or []:
            body = str(raw.get("body") or "")
            comments.append(Comment(body, str(raw.get("createdAt") or "")[:10], is_own(body)))
        return PullRequest(str(data["state"]), comments)

    def comment(self, pr: int, body: str) -> None:
        self._gh("pr", "comment", str(pr), "--body-file", "-", stdin=f"{body}\n\n{MARKER}")

    def reopen(self, pr: int) -> bool:
        try:
            self._gh("pr", "reopen", str(pr))
        except GitHubError:
            return False
        return True

    def to_draft(self, pr: int) -> None:
        self._gh("pr", "ready", "--undo", str(pr))
