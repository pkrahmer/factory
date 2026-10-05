"""Cost summaries are sums over the tick's records; the records are written by hand here."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from factory import costs

TICKET = "factory/features/F0002-ops/ongoing/F0002-S0001-health-endpoint.md"
BRANCH = "ticket/F0002-S0001-health-endpoint"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    rows = [
        {
            "line": f"run intake {TICKET} main",
            "ok": True,
            "seconds": 38,
            "turns": 7,
            "cost": 0.16,
            "input": 1200,
            "cache_read": 90000,
            "cache_write": 20000,
            "output": 900,
        },
        {
            "line": f"run tester {TICKET} {BRANCH}",
            "ok": True,
            "seconds": 63,
            "turns": 12,
            "cost": 0.80,
            "input": 500,
            "cache_read": 300000,
            "cache_write": 30000,
            "output": 4000,
        },
        {"line": f"run tester {TICKET} {BRANCH}", "ok": False, "seconds": 5},
        {
            "line": f"merged {TICKET} {BRANCH}",
            "ok": True,
            "seconds": 20,
            "turns": 4,
            "cost": 0.05,
            "input": 300,
            "cache_read": 20000,
            "cache_write": 5000,
            "output": 300,
        },
        {
            "line": "run intake factory/features/F0002-ops/ongoing/F0002-S0002-other.md main",
            "ok": True,
            "seconds": 40,
            "turns": 7,
            "cost": 0.20,
            "input": 1000,
            "cache_read": 1000,
            "cache_write": 1000,
            "output": 1000,
        },
    ]
    (tmp_path / ".git" / costs.RECORDS).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return tmp_path


def test_stage_and_ticket_are_read_from_the_line() -> None:
    assert costs.stage_of(f"run tester {TICKET} ticket/x") == "tester"
    assert costs.stage_of(f"merged {TICKET} ticket/x") == "dispatcher"
    assert costs.ticket_of(f"pr {TICKET} OPEN 2") == TICKET
    assert costs.ticket_of("idle") is None


def test_buckets_sum_successful_runs_of_one_ticket_per_stage(repo: Path) -> None:
    by_stage = costs.buckets(repo, TICKET)
    assert set(by_stage) == {"intake", "tester", "dispatcher"}
    assert by_stage["tester"].runs == 1  # the failed run is not a cost of the stage's work
    assert by_stage["tester"].tokens["cache_read"] == 300000
    assert by_stage["intake"].cost == pytest.approx(0.16)


def test_table_has_a_row_per_stage_and_a_total(repo: Path) -> None:
    table = costs.table(repo, TICKET)
    assert "| intake | 1 | 0.6 | 7 | 21k | 90k | 900 | 0.16 |" in table
    assert "| **total** | 3 | 2.0 | 23 | 57k | 410k | 5k | 1.01 |" in table


def test_one_line_total_for_the_ticket_log(repo: Path) -> None:
    assert costs.one_line(repo, TICKET) == (
        "cost: 3 runs, 2.0 min, 23 turns, 57k tokens in (410k more from cache), 5k out, $1.01"
    )


def test_no_records_means_an_empty_but_valid_summary(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    assert costs.one_line(tmp_path, TICKET).startswith("cost: 0 runs")
    assert costs.table(tmp_path, TICKET).endswith("| **total** | 0 | 0.0 | 0 | 0 | 0 | 0 | 0.00 |")
