"""Starting a stage agent headless, without a model in between.

An agent is defined by its file in `~/.claude/agents/<name>.md`: model, tools, effort, a budget
in dollars and the skills it works by. Claude Code's `--agent` flag does not apply that file in
print mode (checked with Claude Code 2.1.289: no preloaded skills, no hooks, no turn limit), so
the runner reads it and passes everything as flags: the agent's text and its skills as an
appended system prompt, the lane guard as a hook in a settings file, the budget as
`--max-budget-usd` (`--max-turns` no longer exists). A run stopped by its budget is resumed
once, under the session id the runner chose, with a message telling the agent to finish.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from factory import watch

Process = Callable[[list[str], int], tuple[int, str] | None]  # (args, timeout s) -> (exit, stdout)
DEFAULT_BUDGET = 3.0
RESUME_SHARE = 0.25  # of the budget, for the one resume after a budget stop
MIN_RESUME = 0.5
BUDGET_STOP = "error_max_budget_usd"
# What a stage agent's session leaves out, measured in demo run 4 (docs/decisions.md, 2026-10-05):
# auto memory and the git snapshot (with its commit attribution) are text no stage uses, and
# bytecode files only lengthen the listings agents read. `--strict-mcp-config` in the command
# keeps the login's claude.ai connectors out; they arrived after the first call and rewrote the
# cached prefix.
AGENT_ENV = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}


class AgentMissingError(RuntimeError):
    """The agent or one of its skills is not installed."""


@dataclass(frozen=True)
class AgentSpec:
    name: str
    model: str
    tools: list[str]
    effort: str | None
    budget: float
    prompt: str


@dataclass
class AgentRun:
    ok: bool
    reason: str = ""
    result: str = ""
    structured: dict[str, Any] | None = None
    cost: float = 0.0
    turns: int = 0
    seconds: int = 0
    tokens: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(("input", "cache_read", "cache_write", "output"), 0)
    )
    denials: list[str] = field(default_factory=list)


def _body(text: str) -> str:
    """A Markdown file without its frontmatter."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            text = text[end + len("\n---") :]
    return text.strip()


def load(name: str, home: Path) -> AgentSpec:
    path = home / "agents" / f"{name}.md"
    if not path.is_file():
        raise AgentMissingError(f"agent {name!r} is not installed ({path})")
    text = path.read_text(encoding="utf-8")
    try:
        meta = watch.parse_frontmatter(text)
    except yaml.YAMLError as broken:
        message = str(broken).split("\n", 1)[0]
        raise AgentMissingError(f"agent {name!r}: its file is not valid YAML ({message})") from None
    parts = [_body(text)]
    for skill in meta.get("skills") or []:
        skill_file = home / "skills" / str(skill) / "SKILL.md"
        if not skill_file.is_file():
            raise AgentMissingError(f"skill {skill!r} of agent {name!r} is not installed")
        parts.append(f"# Skill {skill}\n\n{_body(skill_file.read_text(encoding='utf-8'))}")
    return AgentSpec(
        name=name,
        model=str(meta.get("model") or "sonnet"),
        tools=[t.strip() for t in str(meta.get("tools") or "").split(",") if t.strip()],
        effort=str(meta["effort"]) if meta.get("effort") else None,
        budget=float(meta.get("budget_usd") or DEFAULT_BUDGET),
        prompt="\n\n".join(parts) + "\n",
    )


def command(  # noqa: PLR0913 — one keyword per part of the command
    claude: str,
    spec: AgentSpec,
    message: str,
    *,
    session: str,
    state: Path,
    budget: float,
    resume: bool = False,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    """The `claude -p` command for one run of the agent. Its prompt and settings are written
    into `state` (under `.git`, never the work tree)."""
    state.mkdir(parents=True, exist_ok=True)
    prompt = state / f"agent-{spec.name}.md"
    prompt.write_text(spec.prompt, encoding="utf-8")
    guard = {"type": "command", "command": f"factory-guard {spec.name}"}
    settings = state / f"agent-{spec.name}-settings.json"
    hooks = {"PreToolUse": [{"matcher": "Edit|Write", "hooks": [guard]}]}
    settings.write_text(json.dumps({"hooks": hooks}), encoding="utf-8")
    cmd = [claude, "-p", message, "--model", spec.model]
    if spec.effort:
        cmd += ["--effort", spec.effort]
    if spec.tools:
        cmd += ["--tools", ",".join(spec.tools)]
    cmd += ["--resume" if resume else "--session-id", session]
    cmd += [
        "--append-system-prompt-file",
        str(prompt),
        "--settings",
        str(settings),
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "--strict-mcp-config",
        "--max-budget-usd",
        f"{budget:.2f}",
        "--output-format",
        "json",
    ]
    if schema is not None:
        cmd += ["--json-schema", json.dumps(schema)]
    return cmd


def subprocess_process(root: Path) -> Process:
    def run(args: list[str], timeout: int) -> tuple[int, str] | None:
        try:
            proc = subprocess.run(
                args,
                cwd=root,
                capture_output=True,
                encoding="utf-8",
                check=False,
                timeout=timeout,
                env={**os.environ, **AGENT_ENV},
            )
        except subprocess.TimeoutExpired:
            return None
        return proc.returncode, proc.stdout

    return run


def _denial(entry: dict[str, Any]) -> str:
    tool = str(entry.get("tool_name") or "?")
    given = entry.get("tool_input") or {}
    detail = given.get("command") or given.get("file_path") or json.dumps(given)[:200]
    return f"{tool}: {detail}"


def _absorb(run: AgentRun, data: dict[str, Any]) -> None:
    run.cost += float(data.get("total_cost_usd") or 0)
    run.turns += int(data.get("num_turns") or 0)
    raw_usage = data.get("usage")
    usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
    for key, source in (
        ("input", "input_tokens"),
        ("cache_read", "cache_read_input_tokens"),
        ("cache_write", "cache_creation_input_tokens"),
        ("output", "output_tokens"),
    ):
        run.tokens[key] += int(usage.get(source) or 0)
    run.denials += [_denial(d) for d in data.get("permission_denials") or []]
    run.result = str(data.get("result") or "")
    structured = data.get("structured_output")
    run.structured = structured if isinstance(structured, dict) else None


def run(  # noqa: PLR0913 — the definition, the message and how to run them
    spec: AgentSpec,
    message: str,
    *,
    state: Path,
    timeout: int,
    process: Process,
    claude: str = "claude",
    finish: str = "Finish now and hand back.",
    schema: dict[str, Any] | None = None,
) -> AgentRun:
    """One run of the agent, resumed once if it hit its budget."""
    started = time.time()
    session = str(uuid.uuid4())
    outcome = AgentRun(ok=False)
    budget, text, resume = spec.budget, message, False
    for _attempt in range(2):
        args = command(
            claude,
            spec,
            text,
            session=session,
            state=state,
            budget=budget,
            resume=resume,
            schema=schema,
        )
        answered = process(args, timeout)
        if answered is None:
            outcome.reason = f"timed out after {timeout // 60} min"
            break
        code, out = answered
        try:
            data = json.loads(out)
        except ValueError:
            outcome.reason = f"no result from claude (exit {code}): {out.strip()[-200:]}"
            break
        _absorb(outcome, data)
        subtype = str(data.get("subtype") or "")
        if subtype == BUDGET_STOP and not resume:
            budget, text, resume = max(MIN_RESUME, spec.budget * RESUME_SHARE), finish, True
            continue
        outcome.ok = code == 0 and not data.get("is_error")
        if not outcome.ok:
            errors = "; ".join(str(e) for e in data.get("errors") or [])
            outcome.reason = f"{subtype or 'error'}" + (f": {errors}" if errors else "")
            if subtype == BUDGET_STOP:
                outcome.reason = f"budget of ${spec.budget:.2f} spent, and the resume too"
        break
    outcome.seconds = int(time.time() - started)
    return outcome
