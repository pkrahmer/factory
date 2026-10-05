"""The preflight is a pure function of (platform, which, runner); nothing here touches the host."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.preflight import Check, evaluate, platform_key

ALL_TOOLS = ("git", "gh", "uv", "make", "apt-get", "sh", "grep", "rm", "touch")


def which_from(*present: str) -> Callable[[str], str | None]:
    return lambda tool: f"/usr/bin/{tool}" if tool in present else None


def runner_from(*succeeding: str) -> Callable[..., bool]:
    return lambda *args: " ".join(args) in succeeding


def all_green() -> Callable[..., bool]:
    return lambda *_args: True


def by_name(checks: list[Check]) -> dict[str, Check]:
    return {c.name: c for c in checks}


STAGES_YML = (
    "stages:\n  ready: {agent: intake, next: [tests]}\n  tests: {agent: tester, next: []}\n"
)


@pytest.fixture
def synced(tmp_path: Path) -> Path:
    (tmp_path / ".venv").mkdir()
    (tmp_path / "factory").mkdir()
    (tmp_path / "factory" / "stages.yml").write_text(STAGES_YML)
    return tmp_path


@pytest.fixture
def agents(tmp_path: Path) -> Path:
    folder = tmp_path / "home" / ".claude" / "agents"
    folder.mkdir(parents=True)
    for name in ("intake", "tester"):
        (folder / f"{name}.md").write_text("---\nname: x\n---\n")
    return folder


def test_platform_key_uses_the_package_manager_on_linux() -> None:
    assert platform_key("linux", which_from("apt-get")) == "apt"
    assert platform_key("linux", which_from("dnf")) == "dnf"
    assert platform_key("linux", which_from()) == "other"


def test_platform_key_passes_windows_and_mac_through() -> None:
    assert platform_key("win32", which_from()) == "win32"
    assert platform_key("darwin", which_from()) == "darwin"


def test_everything_present_is_all_ok(synced: Path, agents: Path) -> None:
    checks = evaluate(
        "linux", which_from(*ALL_TOOLS), all_green(), root=synced, agents_dir=agents, gate=False
    )
    assert all(c.ok for c in checks)
    assert [c.name for c in checks] == [
        "git",
        "gh",
        "uv",
        "make",
        "git identity",
        "gh auth",
        "venv",
        "shell tools",
        "agents",
    ]


def test_an_agent_named_in_stages_but_not_installed_fails_the_preflight(
    synced: Path, agents: Path
) -> None:
    (synced / "factory" / "stages.yml").write_text(
        STAGES_YML + "  docs: {agent: documenter, next: []}\n"
    )
    checks = by_name(
        evaluate("linux", which_from(*ALL_TOOLS), all_green(), root=synced, agents_dir=agents)
    )
    assert not checks["agents"].ok
    assert "documenter" in checks["agents"].fix
    assert not checks["make lint"].ok  # the gate waits for the rest


def test_missing_tool_names_the_install_command_for_the_platform(synced: Path) -> None:
    checks = by_name(
        evaluate("win32", which_from("git", "gh", "uv"), all_green(), root=synced, gate=False)
    )
    assert checks["make"].line() == "missing make: winget install ezwinports.make"
    linux = by_name(
        evaluate(
            "linux", which_from("git", "gh", "uv", "apt-get"), all_green(), root=synced, gate=False
        )
    )
    assert linux["make"].line() == "missing make: sudo apt-get install -y make"


def test_state_checks_depend_on_their_tool(synced: Path) -> None:
    checks = by_name(
        evaluate("linux", which_from("git", "uv", "make"), all_green(), root=synced, gate=False)
    )
    assert not checks["gh auth"].ok
    assert checks["gh auth"].fix == "gh auth login"


def test_gh_auth_failure_is_reported(synced: Path) -> None:
    runner = runner_from("git config user.name", "git config user.email")
    checks = by_name(evaluate("linux", which_from(*ALL_TOOLS), runner, root=synced, gate=False))
    assert checks["git identity"].ok
    assert not checks["gh auth"].ok


def test_gate_is_skipped_while_anything_is_missing(synced: Path) -> None:
    checks = by_name(evaluate("linux", which_from("git", "gh", "uv"), all_green(), root=synced))
    assert checks["make lint"].line() == "missing make lint: fix the lines above first"


def test_gate_runs_make_lint_when_the_rest_is_ok(synced: Path, agents: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(*args: str) -> bool:
        seen.append(args)
        return True

    checks = by_name(
        evaluate("linux", which_from(*ALL_TOOLS), runner, root=synced, agents_dir=agents)
    )
    assert ("make", "lint") in seen
    assert ("make", "check") not in seen  # a ticket branch may be red on purpose
    assert checks["make lint"].ok


def test_missing_shell_tools_point_to_git_bash_on_windows(synced: Path) -> None:
    checks = by_name(
        evaluate("win32", which_from("git", "gh", "uv", "make", "sh"), all_green(), root=synced)
    )
    assert not checks["shell tools"].ok
    assert checks["shell tools"].fix.startswith("run the loop from Git Bash")
    assert "grep, rm, touch" in checks["shell tools"].fix


def test_missing_venv_asks_for_uv_sync(tmp_path: Path) -> None:
    checks = by_name(
        evaluate("linux", which_from(*ALL_TOOLS), all_green(), root=tmp_path, gate=False)
    )
    assert checks["venv"].line() == "missing venv: uv sync"


def test_lines_have_the_two_shapes() -> None:
    assert Check("x", True).line() == "ok x"
    assert Check("x", False, "do y").line() == "missing x: do y"
