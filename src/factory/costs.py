"""What a ticket cost: minutes, turns, tokens and dollars per stage, from the tick's records.

The tick appends one JSON line per dispatcher run to `.git/factory-dispatches.jsonl`
(see `tick.record`). This module sums them for one ticket. The tick posts the table on
the pull request when the ticket becomes ready for the human; the dispatcher puts the
one-line total into the ticket when it closes it (before the story moves to `done/`:
records are keyed by the path the line named). Nothing here calls a model.

    factory-costs factory/features/F0002-ops/ongoing/F0002-S0001-health-endpoint.md
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from factory import watch

RECORDS = "factory-dispatches.jsonl"
TOKEN_KEYS = ("input", "cache_read", "cache_write", "output")


@dataclass
class Bucket:
    runs: int = 0
    seconds: int = 0
    turns: int = 0
    cost: float = 0.0
    tokens: dict[str, int] = field(default_factory=lambda: dict.fromkeys(TOKEN_KEYS, 0))

    def add(self, record: dict[str, object]) -> None:
        self.runs += 1
        self.seconds += _num(record, "seconds")
        self.turns += _num(record, "turns")
        cost = record.get("cost")
        self.cost += float(cost) if isinstance(cost, (int, float)) else 0.0
        for key in TOKEN_KEYS:
            self.tokens[key] += _num(record, key)

    def merge(self, other: Bucket) -> None:
        self.runs += other.runs
        self.seconds += other.seconds
        self.turns += other.turns
        self.cost += other.cost
        for key in TOKEN_KEYS:
            self.tokens[key] += other.tokens[key]


def _num(record: dict[str, object], key: str) -> int:
    value = record.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def stage_of(line: str) -> str:
    """`run <agent> …` is the agent's stage; every other line is the dispatcher's own work."""
    parts = line.split()
    return parts[1] if parts and parts[0] == "run" and len(parts) > 1 else "dispatcher"


def ticket_of(line: str) -> str | None:
    return next((p for p in line.split() if p.endswith(".md")), None)


def records(root: Path) -> list[dict[str, object]]:
    path = Path(watch.git(root, "rev-parse", "--absolute-git-dir").strip()) / RECORDS
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, object]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def buckets(root: Path, ticket: str) -> dict[str, Bucket]:
    by_stage: dict[str, Bucket] = defaultdict(Bucket)
    for record in records(root):
        line = str(record.get("line", ""))
        if ticket_of(line) == ticket and record.get("ok"):
            by_stage[stage_of(line)].add(record)
    return dict(by_stage)


def _k(n: int) -> str:
    return f"{n / 1000:.0f}k" if n >= 1000 else str(n)


def table(root: Path, ticket: str) -> str:
    """A Markdown table for the pull request, one row per stage, totals last."""
    by_stage = buckets(root, ticket)
    total = Bucket()
    rows = ["| stage | runs | min | turns | in | cached | out | USD |", "|:-|-:|-:|-:|-:|-:|-:|-:|"]
    for stage, b in by_stage.items():
        rows.append(_row(stage, b))
        total.merge(b)
    rows.append(_row("**total**", total))
    return "\n".join(rows)


def _row(name: str, b: Bucket) -> str:
    fresh = b.tokens["input"] + b.tokens["cache_write"]
    return (
        f"| {name} | {b.runs} | {b.seconds / 60:.1f} | {b.turns} | {_k(fresh)} | "
        f"{_k(b.tokens['cache_read'])} | {_k(b.tokens['output'])} | {b.cost:.2f} |"
    )


def one_line(root: Path, ticket: str) -> str:
    """For the ticket log: the totals in one sentence."""
    total = Bucket()
    for b in buckets(root, ticket).values():
        total.merge(b)
    fresh = total.tokens["input"] + total.tokens["cache_write"]
    return (
        f"cost: {total.runs} runs, {total.seconds / 60:.1f} min, {total.turns} turns, "
        f"{_k(fresh)} tokens in ({_k(total.tokens['cache_read'])} more from cache), "
        f"{_k(total.tokens['output'])} out, ${total.cost:.2f}"
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: factory-costs <ticket path>", file=sys.stderr)
        return 2
    root = Path.cwd()
    print(table(root, args[0]))
    print()
    print(one_line(root, args[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
