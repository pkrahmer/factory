"""Starting a stage agent: its definition read from the agent file, the command, the result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from factory import agent

AGENT = """---
name: coder
description: Doing-stage agent.
model: opus
tools: Read, Grep, Glob, Edit, Write, Bash
effort: medium
budget_usd: 3
skills: [factory-rules, role-coder]
---
Process the ticket named in your task.
"""


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "coder.md").write_text(AGENT)
    for name, text in (("factory-rules", "R1. Git is the only truth."), ("role-coder", "Code.")):
        (tmp_path / "skills" / name).mkdir(parents=True)
        (tmp_path / "skills" / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: x\n---\n\n{text}\n"
        )
    return tmp_path


def test_the_agent_file_and_its_skills_make_the_definition(home: Path) -> None:
    spec = agent.load("coder", home)
    assert (spec.model, spec.effort, spec.budget) == ("opus", "medium", 3.0)
    assert spec.tools == ["Read", "Grep", "Glob", "Edit", "Write", "Bash"]
    assert spec.prompt == (
        "Process the ticket named in your task.\n\n"
        "# Skill factory-rules\n\nR1. Git is the only truth.\n\n"
        "# Skill role-coder\n\nCode.\n"
    )


def test_a_missing_agent_or_skill_is_an_error(home: Path) -> None:
    with pytest.raises(agent.AgentMissingError, match="agent 'tester' is not installed"):
        agent.load("tester", home)
    (home / "skills" / "role-coder" / "SKILL.md").unlink()
    with pytest.raises(agent.AgentMissingError, match="skill 'role-coder'"):
        agent.load("coder", home)


def test_the_command_carries_the_definition_and_the_guard(home: Path, tmp_path: Path) -> None:
    spec = agent.load("coder", home)
    cmd = agent.command("claude", spec, "Ticket: x", session="s-1", state=tmp_path, budget=3.0)
    assert cmd[:3] == ["claude", "-p", "Ticket: x"]
    flags = dict(zip(cmd[3::2], cmd[4::2], strict=False))
    assert flags["--model"] == "opus"
    assert flags["--effort"] == "medium"
    assert flags["--tools"] == "Read,Grep,Glob,Edit,Write,Bash"
    assert flags["--session-id"] == "s-1"
    assert flags["--max-budget-usd"] == "3.00"
    assert flags["--permission-prompts"] == "none"
    assert Path(flags["--append-system-prompt-file"]).read_text() == spec.prompt
    settings = json.loads(Path(flags["--settings"]).read_text())
    hook = settings["hooks"]["PreToolUse"][0]
    assert hook["matcher"] == "Edit|Write"
    assert hook["hooks"][0]["command"] == "factory-guard coder"
    resumed = agent.command(
        "claude", spec, "Finish.", session="s-1", state=tmp_path, budget=1.0, resume=True
    )
    assert "--resume" in resumed and "--session-id" not in resumed


def result(subtype: str = "success", cost: float = 0.3, **extra: object) -> str:
    return json.dumps(
        {
            "type": "result",
            "subtype": subtype,
            "is_error": subtype != "success",
            "num_turns": 9,
            "total_cost_usd": cost,
            "session_id": "s-1",
            "result": "handed back",
            "usage": {"input_tokens": 10, "cache_read_input_tokens": 100, "output_tokens": 5},
            **extra,
        }
    )


def test_a_successful_run(home: Path, tmp_path: Path) -> None:
    outputs = [
        (
            0,
            result(
                permission_denials=[
                    {"tool_name": "Bash", "tool_input": {"command": "git push --force"}},
                    {"tool_name": "Write", "tool_input": {"file_path": "/w/tests/x.py"}},
                ]
            ),
        )
    ]
    run = agent.run(
        agent.load("coder", home),
        "task",
        state=tmp_path,
        timeout=60,
        process=lambda _args, _t: outputs.pop(0),
    )
    assert run.ok and run.result == "handed back"
    assert (run.cost, run.turns, run.tokens["cache_read"]) == (0.3, 9, 100)
    assert run.denials == ["Bash: git push --force", "Write: /w/tests/x.py"]


def test_a_budget_stop_is_resumed_once_with_the_finish_message(home: Path, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    outputs = [(1, result("error_max_budget_usd", 3.1)), (0, result(cost=0.4))]

    def process(args: list[str], _timeout: int) -> tuple[int, str]:
        calls.append(args)
        return outputs.pop(0)

    run = agent.run(
        agent.load("coder", home),
        "task",
        state=tmp_path,
        timeout=60,
        process=process,
        finish="Finish now.",
    )
    assert run.ok and run.cost == pytest.approx(3.5) and run.turns == 18
    assert calls[1][2] == "Finish now." and "--resume" in calls[1]


def test_a_second_budget_stop_or_a_timeout_fails(home: Path, tmp_path: Path) -> None:
    spec = agent.load("coder", home)
    twice = [(1, result("error_max_budget_usd")), (1, result("error_max_budget_usd"))]
    run = agent.run(spec, "task", state=tmp_path, timeout=60, process=lambda _a, _t: twice.pop(0))
    assert not run.ok and "budget" in run.reason
    run = agent.run(spec, "task", state=tmp_path, timeout=60, process=lambda _a, _t: None)
    assert not run.ok and run.reason == "timed out after 1 min"
    run = agent.run(spec, "task", state=tmp_path, timeout=60, process=lambda _a, _t: (1, "boom"))
    assert not run.ok and run.reason.startswith("no result from claude (exit 1)")


def test_every_installed_agent_and_its_skills_load() -> None:
    """The agent files and skills this repository ships, as the dispatcher reads them."""
    shipped = Path(__file__).resolve().parent.parent / "claude"
    names = sorted(p.stem for p in (shipped / "agents").glob("*.md"))
    assert names == ["acceptor", "coder", "demo", "documenter", "intake", "reviewer", "tester"]
    for name in names:
        spec = agent.load(name, shipped)
        assert spec.model and spec.tools and spec.budget > 0, name


def test_an_agent_file_that_is_not_valid_yaml_is_missing_not_a_crash(home: Path) -> None:
    (home / "agents" / "coder.md").write_text("---\nname: coder\ndescription: a: b: c\n---\nx\n")
    with pytest.raises(agent.AgentMissingError, match="not valid YAML"):
        agent.load("coder", home)
