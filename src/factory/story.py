"""A story file as text: the frontmatter, the sections, and the numbered log.

Everything the pipeline writes into a story goes through here, so the format is decided once:
the frontmatter in a fixed key order, a log entry as the next number of the list under
`## Log (append only)`, its continuation lines indented to stay inside the item. Nothing here
reads git or calls a model.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from factory import watch

# The machine fields in the order they are written; any other key follows in its own order.
FIELDS = ("stage", "pr", "blocked", "comments_seen", "claimed_at", "round", "attempts")
TRAILING = ("stories", "outcome")  # the acceptance report's two extra fields
LOG_HEADING = "## Log"
ENTRY = re.compile(r"^(\d+)\. ")


def split(text: str) -> tuple[dict[str, Any], str]:
    """(frontmatter, body). A text without frontmatter has an empty one and is all body."""
    meta = watch.parse_frontmatter(text)
    if not text.startswith("---\n"):
        return meta, text
    end = text.find("\n---", 4)
    if end < 0:
        return meta, text
    body = text[end + len("\n---") :]
    return meta, body.removeprefix("\n")


def _scalar(value: Any) -> str:
    dumped = yaml.safe_dump(value, default_flow_style=True, allow_unicode=True, width=1000)
    return dumped.strip().removesuffix("...").strip()


def render(meta: dict[str, Any], body: str) -> str:
    """The story with `meta` as its frontmatter, known fields first, in their fixed order."""
    order = [k for k in FIELDS if k in meta] + [k for k in TRAILING if k in meta]
    order += [k for k in meta if k not in order]
    lines = [f"{key}: {_scalar(meta[key])}" for key in order]
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def update(text: str, **fields: Any) -> str:
    """The story with these frontmatter fields set (a missing frontmatter is created)."""
    meta, body = split(text)
    meta.update(fields)
    return render(meta, body)


# --- sections ------------------------------------------------------------------------------


def _headings(lines: list[str]) -> list[int]:
    return [i for i, line in enumerate(lines) if line.startswith("## ")]


def section(body: str, heading: str) -> str:
    """The text under the first `## <heading>…` line, up to the next `## ` heading."""
    lines = body.split("\n")
    starts = _headings(lines)
    for n, i in enumerate(starts):
        if lines[i].startswith(f"## {heading}"):
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            return "\n".join(lines[i + 1 : end]).strip("\n")
    return ""


def insert_under(body: str, heading: str, line: str) -> str:
    """`line` as the first paragraph under `## <heading>…`; unchanged without that heading."""
    lines = body.split("\n")
    for i, current in enumerate(lines):
        if current.startswith(f"## {heading}"):
            rest = lines[i + 1 :]
            while rest and not rest[0].strip():
                rest = rest[1:]
            return "\n".join([*lines[: i + 1], "", line, "", *rest])
    return body


# --- the log ---------------------------------------------------------------------------------


def _log_bounds(lines: list[str]) -> tuple[int, int] | None:
    starts = _headings(lines)
    for n, i in enumerate(starts):
        if lines[i].startswith(LOG_HEADING):
            return i, starts[n + 1] if n + 1 < len(starts) else len(lines)
    return None


def entries(body: str) -> list[tuple[int, str]]:
    """The log's entries as (number, text); continuation lines are dedented into the text."""
    lines = body.split("\n")
    bounds = _log_bounds(lines)
    if bounds is None:
        return []
    found: list[tuple[int, list[str]]] = []
    for line in lines[bounds[0] + 1 : bounds[1]]:
        match = ENTRY.match(line)
        if match:
            found.append((int(match.group(1)), [line[match.end() :]]))
        elif found:
            found[-1][1].append(line.strip())
    return [(number, "\n".join(text).strip()) for number, text in found]


def last_entry(body: str) -> str:
    found = entries(body)
    return found[-1][1] if found else ""


def append(body: str, text: str) -> str:
    """The body with `text` as the log's next numbered entry: one more than the last number under
    the log heading, whatever numbered lists stand above it. A body without a log gets one."""
    found = entries(body)
    number = found[-1][0] + 1 if found else 1
    marker = f"{number}. "
    pad = " " * len(marker)
    first, *rest = text.strip().split("\n")
    entry = [marker + first, *[(pad + line) if line.strip() else "" for line in rest]]
    lines = body.split("\n")
    bounds = _log_bounds(lines)
    if bounds is None:
        head = body.rstrip("\n")
        return head + "\n\n## Log (append only)\n\n" + "\n".join(entry) + "\n"
    start, end = bounds
    before, log, after = lines[:start], lines[start:end], lines[end:]
    while log and not log[-1].strip():
        log.pop()
    if len(log) == 1:
        log.append("")
    tail = ["", *after] if after else [""]
    return "\n".join([*before, *log, *entry, *tail])
