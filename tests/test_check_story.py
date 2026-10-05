"""The story format check: what intake used to check by reading, now checked by code."""

from __future__ import annotations

from pathlib import Path

import pytest

from factory import story

FORM = """# <Title>

## Assignment (as of log entry 1)

## Interface

## Acceptance criteria

## Demo

## Log (append only)

1. 2026-01-01 human: created.
"""

GOOD = """# Health endpoint

## Assignment (as of log entry 1)

Build it.

## Interface

```python
def health() -> dict[str, str]: ...
```

## Acceptance criteria

1. `GET /health` answers 200
   with three fields.
2. `make check` stays green.
3. docs: `docs/api.md` describes `/health`.

## Demo

```bash
uv run python -c "print('ok')"
```
Expect: `ok`.

```bash
curl -s localhost:8000/health
```

Expect: the JSON.

## Log (append only)

1. 2026-10-04 human: created.
2. intake: accepted
"""

REQUIRED = story.required_sections(FORM)


def test_the_sections_come_from_the_repositorys_ticket_form() -> None:
    assert REQUIRED == ["Assignment", "Interface", "Acceptance criteria", "Demo", "Log"]


def test_a_story_in_the_form_passes() -> None:
    assert story.check(GOOD, REQUIRED) == []


def test_a_missing_section_and_title() -> None:
    text = GOOD.replace("# Health endpoint\n", "").replace("## Interface", "## Interfaces")
    assert story.check(text, REQUIRED) == [
        "there is no title line (`# …`)",
        "the section `## Interface` is missing",
    ]


def test_a_demo_command_without_expect_is_named() -> None:
    text = GOOD.replace("\nExpect: the JSON.\n", "\n")
    assert story.check(text, REQUIRED) == ["Demo command block 2 has no `Expect:` line after it"]
    no_blocks = (
        GOOD.split("## Demo", maxsplit=1)[0] + "## Demo\n\nRun it.\n\n## Log (append only)\n"
    )
    assert "the Demo has no command block" in story.check(no_blocks, REQUIRED)


def test_the_closing_criteria_stay_last_and_the_numbers_run_on() -> None:
    moved = GOOD.replace(
        "3. docs: `docs/api.md` describes `/health`.",
        "3. docs: `docs/api.md` describes `/health`.\n4. A criterion carried in from an answer.",
    )
    assert story.check(moved, REQUIRED) == [
        "the second-to-last criterion is not `make check` stays green",
        "the last criterion does not start with `docs:`",
    ]
    gap = GOOD.replace("2. `make check` stays green.", "4. `make check` stays green.")
    assert story.check(gap, REQUIRED) == ["the criteria are not numbered 1 to 3: 1, 4, 3"]


def test_log_entries_run_on_without_gaps() -> None:
    text = GOOD.replace("2. intake: accepted", "- intake: accepted\n4. intake: again")
    assert story.check(text, REQUIRED) == ["the log entries are not numbered 1 to 2: 1, 4"]


def test_the_place_of_a_story() -> None:
    features = Path("factory/features")
    good = features / "F0002-ops" / "ongoing" / "F0002-S0001-health.md"
    assert story.check_place(good, feature_md=True) == []
    assert story.check_place(good, feature_md=False) == ["`FEATURE.md` is missing in `F0002-ops`"]
    wrong = features / "F0001-todo" / "ongoing" / "F0002-S0001-health.md"
    assert story.check_place(wrong, feature_md=True) == [
        "story F0002-S0001 sits in feature folder `F0001-todo`"
    ]
    odd = features / "F0002-ops" / "ongoing" / "health.md"
    assert story.check_place(odd, feature_md=True) == [
        "the file name `health.md` is not `F0002-S<nnnn>-<slug>.md`"
    ]


def test_the_command_checks_files_against_the_repositorys_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "factory" / "features" / "F0002-ops" / "ongoing").mkdir(parents=True)
    (tmp_path / "factory" / "TICKET.md").write_text(FORM)
    rel = "factory/features/F0002-ops/ongoing/F0002-S0001-health.md"
    (tmp_path / rel).write_text(GOOD.replace("\nExpect: the JSON.\n", "\n"))
    monkeypatch.chdir(tmp_path)
    assert story.main([rel]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"{rel}: `FEATURE.md` is missing in `F0002-ops`",
        f"{rel}: Demo command block 2 has no `Expect:` line after it",
    ]
    (tmp_path / "factory" / "features" / "F0002-ops" / "FEATURE.md").write_text("# Ops\n")
    (tmp_path / rel).write_text(GOOD)
    assert story.main([rel]) == 0
