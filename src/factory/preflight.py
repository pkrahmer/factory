"""Check that the machine can run the loop before the dispatcher starts it.

One line per check, in a fixed order: `ok <name>` or `missing <name>: <fix>`.
Exit 0 when everything is present, 1 otherwise. The fix is a command the
dispatcher may offer to run after asking the human; it never runs anything on
its own, and nothing in the loop substitutes for a missing tool.

`factory-preflight` in the repository to check. The tick
runs it once a day; its failures go to the tick log.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

TOOLS = ("git", "gh", "uv", "make")
SHELL_TOOLS = ("sh", "grep", "rm", "touch")  # what the Makefile's recipes call

# Install commands per platform. Linux is told apart by its package manager.
INSTALL: dict[str, dict[str, str]] = {
    "win32": {
        "git": "winget install Git.Git",
        "gh": "winget install GitHub.cli",
        "uv": "winget install astral-sh.uv",
        "make": "winget install ezwinports.make",
    },
    "darwin": {
        "git": "xcode-select --install",
        "gh": "brew install gh",
        "uv": "brew install uv",
        "make": "xcode-select --install",
    },
    "apt": {
        "git": "sudo apt-get install -y git",
        "gh": "sudo apt-get install -y gh",
        "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "make": "sudo apt-get install -y make",
    },
    "dnf": {
        "git": "sudo dnf install -y git",
        "gh": "sudo dnf install -y gh",
        "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "make": "sudo dnf install -y make",
    },
    "other": {
        "git": "install git with your package manager",
        "gh": "install the GitHub CLI: https://cli.github.com",
        "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "make": "install GNU make with your package manager",
    },
}


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    fix: str = ""

    def line(self) -> str:
        return f"ok {self.name}" if self.ok else f"missing {self.name}: {self.fix}"


def platform_key(platform: str, which: Callable[[str], str | None]) -> str:
    """Which column of INSTALL applies here."""
    if platform in ("win32", "darwin"):
        return platform
    for manager in ("apt", "dnf"):
        if which(f"{manager}-get" if manager == "apt" else manager):
            return manager
    return "other"


def run(*args: str) -> bool:
    """True when the command exits 0, in the current directory. Output is discarded."""
    try:
        return subprocess.run(args, capture_output=True, check=False).returncode == 0
    except OSError:
        return False


def tool_checks(key: str, which: Callable[[str], str | None]) -> list[Check]:
    return [Check(tool, which(tool) is not None, INSTALL[key][tool]) for tool in TOOLS]


def state_checks(
    have: Callable[[str], bool], runner: Callable[..., bool], root: Path
) -> list[Check]:
    """Checks that need the tools above; each is skipped as missing when its tool is absent."""
    checks: list[Check] = []
    git = have("git")
    checks.append(
        Check(
            "git identity",
            git and runner("git", "config", "user.name") and runner("git", "config", "user.email"),
            'git config --global user.name "<name>" && git config --global user.email "<email>"',
        )
    )
    checks.append(Check("gh auth", have("gh") and runner("gh", "auth", "status"), "gh auth login"))
    checks.append(Check("venv", have("uv") and (root / ".venv").is_dir(), "uv sync"))
    return checks


def shell_check(platform: str, which: Callable[[str], str | None]) -> Check:
    """GNU make runs its recipes through `sh`; on Windows that means Git Bash on the PATH."""
    missing = [tool for tool in SHELL_TOOLS if which(tool) is None]
    fix = (
        "run the loop from Git Bash (Git for Windows), which provides " + ", ".join(missing)
        if platform == "win32"
        else "install coreutils: " + ", ".join(missing)
    )
    return Check("shell tools", not missing, fix)


def agents_check(root: Path, agents_dir: Path) -> Check:
    """Every agent `stages.yml` names must be installed, or a stage stalls on 'agent not found'
    halfway through a story: the repository's configuration may be newer than the image."""
    try:
        config = yaml.safe_load((root / "factory" / "stages.yml").read_text(encoding="utf-8"))
    except OSError:
        return Check("agents", False, "factory/stages.yml is missing in this repository")
    named = {str(s.get("agent")) for s in (config.get("stages") or {}).values() if s.get("agent")}
    missing = sorted(a for a in named if not (agents_dir / f"{a}.md").is_file())
    return Check(
        "agents",
        not missing,
        f"stages.yml names agents the installation lacks: {', '.join(missing)}; "
        "update the factory (rebuild the image) or the repository's stages.yml",
    )


def gate_check(checks: list[Check], runner: Callable[..., bool]) -> Check:
    """`make lint` as a probe: make, its shell and `uv run` work together. It judges the machine,
    not the code; a ticket branch may be red on purpose while a question is open."""
    if not all(c.ok for c in checks):
        return Check("make lint", False, "fix the lines above first")
    return Check("make lint", runner("make", "lint"), "run `make lint` and read its output")


def evaluate(  # noqa: PLR0913 — one keyword per injectable dependency
    platform: str,
    which: Callable[[str], str | None],
    runner: Callable[..., bool],
    *,
    root: Path | None = None,
    agents_dir: Path | None = None,
    gate: bool = True,
) -> list[Check]:
    root = root or Path.cwd()
    key = platform_key(platform, which)
    tools = tool_checks(key, which)
    present = {c.name for c in tools if c.ok}
    checks = tools + state_checks(lambda t: t in present, runner, root)
    checks.append(shell_check(platform, which))
    checks.append(agents_check(root, agents_dir or Path.home() / ".claude" / "agents"))
    if gate:
        checks.append(gate_check(checks, runner))
    return checks


def main() -> int:
    checks = evaluate(sys.platform, shutil.which, run, gate="--no-gate" not in sys.argv[1:])
    for check in checks:
        print(check.line())
    return 0 if all(c.ok for c in checks) else 1


def cli() -> int:
    return main()


if __name__ == "__main__":
    sys.exit(cli())
