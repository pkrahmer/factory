"""A story file as text: the frontmatter, the sections, and the numbered log.

Everything the pipeline writes into a story goes through here, so the format is decided once:
the frontmatter in a fixed key order, a log entry as the next number of the list under
`## Log (append only)`, its continuation lines indented to stay inside the item. Nothing here
reads git or calls a model.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

from factory import watch

# The machine fields in the order they are written; any other key follows in its own order.
FIELDS = ("stage", "pr", "blocked", "comments_seen", "round", "attempts")
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


# --- the format check --------------------------------------------------------------------------

FENCE = "```"


def required_sections(form: str) -> list[str]:
    """The `## ` headings of the repository's story form, without their parenthesised notes."""
    return [line[3:].split(" (")[0].strip() for line in form.split("\n") if line.startswith("## ")]


def _has_section(body: str, name: str) -> bool:
    pattern = re.compile(rf"^## {re.escape(name)}(?:\s|\(|$)", re.MULTILINE)
    return bool(pattern.search(body))


def _numbered(lines: list[str]) -> list[tuple[int, str]]:
    """Top-level numbered items with their continuation lines."""
    items: list[tuple[int, list[str]]] = []
    for line in lines:
        match = ENTRY.match(line)
        if match:
            items.append((int(match.group(1)), [line[match.end() :]]))
        elif items:
            items[-1][1].append(line.strip())
    return [(n, " ".join(t).strip()) for n, t in items]


def _sequence(what: str, numbers: list[int]) -> list[str]:
    if numbers == list(range(1, len(numbers) + 1)):
        return []
    shown = ", ".join(str(n) for n in numbers)
    return [f"the {what} are not numbered 1 to {len(numbers)}: {shown}"]


def _criteria(body: str) -> list[str]:
    items = _numbered(section(body, "Acceptance criteria").split("\n"))
    found = _sequence("criteria", [n for n, _ in items])
    if len(items) >= 2:  # noqa: PLR2004 — the two closing criteria
        gate, docs = items[-2][1], items[-1][1]
        if not ("make check" in gate and "green" in gate):
            found.append("the second-to-last criterion is not `make check` stays green")
        if not docs.startswith("docs:"):
            found.append("the last criterion does not start with `docs:`")
    return found


def _demo(body: str) -> list[str]:
    lines = section(body, "Demo").split("\n")
    fences = [i for i, line in enumerate(lines) if line.startswith(FENCE)]
    closing = fences[1::2]
    if not closing:
        return ["the Demo has no command block"]
    found = []
    for number, end in enumerate(closing, start=1):
        after = next((line for line in lines[end + 1 :] if line.strip()), "")
        if not after.startswith("Expect:"):
            found.append(f"Demo command block {number} has no `Expect:` line after it")
    return found


def check(text: str, required: list[str]) -> list[str]:
    """What is wrong with the story's form, one sentence each; empty when nothing is."""
    _, body = split(text)
    found = []
    if not any(line.startswith("# ") for line in body.split("\n")):
        found.append("there is no title line (`# …`)")
    present = [name for name in required if _has_section(body, name)]
    found += [f"the section `## {name}` is missing" for name in required if name not in present]
    if "Acceptance criteria" in present:
        found += _criteria(body)
    if "Demo" in present:
        found += _demo(body)
    found += _sequence("log entries", [n for n, _ in entries(body)])
    return found


def check_place(path: Path, *, feature_md: bool) -> list[str]:
    """Whether the story sits where its id says: `<F0001-slug>/<folder>/<F0001-S…>.md`."""
    folder = path.parent.parent.name
    match = watch.FEATURE_PATTERN.match(folder)
    feature = match.group(1) if match else folder
    found = []
    story_id = watch.ID_PATTERN.match(path.stem)
    if story_id is None:
        found.append(f"the file name `{path.name}` is not `{feature}-S<nnnn>-<slug>.md`")
    elif not story_id.group(1).startswith(f"{feature}-"):
        found.append(f"story {story_id.group(1)} sits in feature folder `{folder}`")
    if not feature_md:
        found.append(f"`FEATURE.md` is missing in `{folder}`")
    return found


def check_file(root: Path, path: Path) -> list[str]:
    """The format check of a story in the working tree, against the repository's story form."""
    form = (root / "factory" / "TICKET.md").read_text(encoding="utf-8")
    text = (root / path).read_text(encoding="utf-8")
    feature_md = (root / path).parent.parent.joinpath("FEATURE.md").is_file()
    return check_place(path, feature_md=feature_md) + check(text, required_sections(form))


def main(argv: list[str] | None = None) -> int:
    """`factory-check-story <path>…`: one line per finding, exit 1 when there is any."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: factory-check-story <story path>…", file=sys.stderr)
        return 2
    found = 0
    for name in args:
        for finding in check_file(Path.cwd(), Path(name)):
            print(f"{name}: {finding}")
            found += 1
    return 1 if found else 0
