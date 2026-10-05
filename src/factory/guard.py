"""PreToolUse hook for stage agents: refuse edits outside the agent's lane.

Claude Code pipes the tool call as JSON on stdin. Exit 2 blocks the call and
hands the message on stderr back to the agent. The hook is called with the
agent's name, `factory-guard coder`; the lane — glob patterns over repository
paths the agent may write to — comes from `lanes` in `factory/stages.yml`, so
the agents stay the same across repositories and the layout is the repository's.
Patterns are shell globs where `*` also crosses `/` (`src/*` covers the whole tree).
"""

from __future__ import annotations

import json
import sys
from fnmatch import fnmatch
from pathlib import Path

import yaml

# The human's files: no lane reaches them. Folders by first component, files by exact path.
NEVER_DIRS = (".claude",)
NEVER_FILES = (
    "pyproject.toml",
    "uv.lock",
    "Makefile",
    "CLAUDE.md",
    "factory/stages.yml",
    "factory/TICKET.md",
)
NEVER_NAMES = ("FEATURE.md",)
CONFIG = Path("factory") / "stages.yml"


def lanes(root: Path) -> dict[str, list[str]]:
    try:
        config = yaml.safe_load((root / CONFIG).read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    found = config.get("lanes") or {}
    return {str(agent): [str(f) for f in patterns or []] for agent, patterns in found.items()}


def refusal(root: Path, agent: str, target: str) -> str | None:
    """Why this write is refused, or None when it is within the lane."""
    try:
        rel = Path(target).resolve().relative_to(root)
    except ValueError:
        return f"{target} is outside the repository"
    posix = rel.as_posix()
    first = rel.parts[0] if rel.parts else ""
    if first in NEVER_DIRS or posix in NEVER_FILES or rel.name in NEVER_NAMES:
        return f"{rel} is owned by the human; a change there is a question (R15)"
    allowed = lanes(root).get(agent)
    if allowed is None:
        return f"no lane configured for {agent!r} in {CONFIG}"
    if not any(fnmatch(posix, pattern) for pattern in allowed):
        return f"{agent} writes only {', '.join(allowed)}; {rel} is out of lane"
    return None


def main(argv: list[str]) -> int:
    agent = argv[1] if len(argv) > 1 else ""
    try:
        call = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # not a tool call we understand; let Claude Code decide
    target = str((call.get("tool_input") or {}).get("file_path") or "")
    if not target:
        return 0
    why = refusal(Path.cwd().resolve(), agent, target)
    if why is None:
        return 0
    print(f"guard: {why}", file=sys.stderr)
    return 2


def cli() -> int:
    return main(sys.argv)


if __name__ == "__main__":
    sys.exit(cli())
