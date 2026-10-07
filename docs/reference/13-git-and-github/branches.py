"""Figure 13-1: the branches of one clean story and of its feature's acceptance.

Renders `branches.svg` beside this script; `branches.md` describes it.

Time runs down, one row per commit. Three lanes: the story's branch on the left, the trunk in the
middle, the feature acceptance's branch on the right. A commit is a dot in the color of who makes
it (amber the human, blue the coder's work, green the factory's code); a branch or merge line is a
diagonal between two lanes; a pull request is a dashed bar on the outer side of its lane, grey
while it is a draft and amber once it is ready. The kit has no primitive for any of these, so this
script draws them as raw SVG, under the kit's text, and checks no more than the text.
"""

import sys
from pathlib import Path
from typing import Literal, NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import (  # noqa: E402
    BASE,
    EDGE_KINDS,
    FONTS,
    NODE_KINDS,
    Diagram,
    Text,
    save,
    text_width,
)

type Track = Literal["ticket", "main", "acceptance"]
type Who = Literal["human", "agent", "code"]
type Side = Literal["left", "right"]
type Mode = Literal["draft", "ready"]

WIDTH, HEIGHT = 850, 1128
LANE_X: dict[Track, int] = {"ticket": 232, "main": 424, "acceptance": 616}
HEAD_Y = 120  # the branch names' baseline
FIRST_Y, ROW = 168, 48  # the first commit's y, and the distance between two commits
TRUNK_TOP, TRUNK_END = 132, 1064  # the main branch, from under its name to below the last commit
DOT_R = 7.0  # a commit's dot
BAND_X, BAND_W = 12, 16  # a pull request's bar: its distance from the lane, and its width
LABEL_GAP = {"ticket": 36, "main": 14, "acceptance": 36}  # a label's distance from its lane
LEGEND_Y = HEIGHT - 24


class Commit(NamedTuple):
    """One commit, one row: its short name (from branches.md), lane, maker, label and label side."""

    key: str
    track: Track
    who: Who
    side: Side
    label: tuple[str, ...]


COMMITS = (
    Commit("m1", "main", "human", "right", ("drafts and `FEATURE.md`",)),
    Commit("m2", "main", "human", "right", ("promote: `git mv`", "into `ongoing/`")),
    Commit("t1", "ticket", "code", "left", ("`intake starts` ·", "draft pull request")),
    Commit("t2", "ticket", "code", "left", ("`ready → tests`",)),
    Commit("t3", "ticket", "code", "left", ("`tests → doing`",)),
    Commit("m3", "main", "human", "right", ("another draft",)),
    Commit("t4", "ticket", "code", "left", ("`merge main` ·", "only when `main` moved")),
    Commit("t5", "ticket", "agent", "left", ("`feat(<layer>): …`",)),
    Commit("t6", "ticket", "agent", "left", ("`refactor: …`",)),
    Commit("t7", "ticket", "code", "left", ("`doing → review`",)),
    Commit("t8", "ticket", "code", "left", ("`review → docs`",)),
    Commit("t9", "ticket", "code", "left", ("`docs → demo`",)),
    Commit("t10", "ticket", "code", "left", ("`demo → accept` ·", "ready")),
    Commit("m4", "main", "human", "right", ("merge commit,", "never a squash")),
    Commit(
        "m5",
        "main",
        "code",
        "left",
        ("`accept → done`: archived", "into `done/` · branch deleted"),
    ),
    Commit("a1", "acceptance", "code", "right", ("`acceptance starts` ·", "draft pull request")),
    Commit("a2", "acceptance", "code", "right", ("`feature → accept` ·", "ready")),
    Commit("m6", "main", "human", "left", ("merge commit:", "report and drafts")),
    Commit(
        "m7",
        "main",
        "code",
        "right",
        ("`accept → done`,", "`outcome: accepted` · branch deleted"),
    ),
)
ROWS = {commit.key: index for index, commit in enumerate(COMMITS)}

# The lanes of the story and of the acceptance run between their first and last commit; the
# branch and merge lines join a lane to the trunk.
LANE_SPANS: tuple[tuple[str, str], ...] = (("t1", "t10"), ("a1", "a2"))
JOINS: tuple[tuple[str, str], ...] = (
    ("m2", "t1"),
    ("m3", "t4"),
    ("t10", "m4"),
    ("m5", "a1"),
    ("a2", "m6"),
)
# Beside: the lane's key, the first and last commit of the bar, and whether the pull request is a
# draft or ready then.
BANDS: tuple[tuple[Track, str, str, Mode], ...] = (
    ("ticket", "t1", "t10", "draft"),
    ("ticket", "t10", "m4", "ready"),
    ("acceptance", "a1", "a2", "draft"),
    ("acceptance", "a2", "m6", "ready"),
)
HEADS: tuple[tuple[Track, str], ...] = (
    ("ticket", "`ticket/<file stem>`"),
    ("main", "`main`"),
    ("acceptance", "`acceptance/<feature>`"),
)

STATIC_CSS = """\
.lane, .guide { fill: none; stroke-linecap: round; stroke-linejoin: round; }
.trunk { stroke-width: 4; } .twig { stroke-width: 2.5; }
.guide { stroke-width: 1; stroke-dasharray: 2 4; }
.dot { stroke-width: 2; }
.pr { stroke-width: 1.25; stroke-dasharray: 4 3; }
.pr-t { font-size: 11px; font-weight: 600; }
"""


# --- geometry ---------------------------------------------------------------------------------


def _at(key: str) -> tuple[float, float]:
    """The center of a commit's dot."""
    commit = COMMITS[ROWS[key]]
    return float(LANE_X[commit.track]), float(FIRST_Y + ROW * ROWS[key])


def _g(value: float) -> str:
    return f"{value:g}"


def _path(css: str, *points: tuple[float, float]) -> str:
    (x0, y0), *rest = points
    steps = " ".join(f"L {_g(x)} {_g(y)}" for x, y in rest)
    return f'<path class="{css}" d="M {_g(x0)} {_g(y0)} {steps}"/>'


# --- the drawing ------------------------------------------------------------------------------


def _lines() -> list[str]:
    """Under everything: the guides to the lanes' names, the trunk, the lanes, the joins."""
    parts = []
    for first in ("t1", "a1"):  # a dotted guide from the lane's name down to where it starts
        x, y = _at(first)
        parts.append(_path("guide", (x, TRUNK_TOP), (x, y - DOT_R - 6)))
    parts.append(_path("lane trunk", (LANE_X["main"], TRUNK_TOP), (LANE_X["main"], TRUNK_END)))
    parts += [_path("lane twig", _at(first), _at(last)) for first, last in LANE_SPANS]
    parts += [_path("lane twig", _at(a), _at(b)) for a, b in JOINS]
    return parts


def _band(track: Track, first: str, last: str, mode: Mode) -> list[str]:
    """A pull request's bar beside its lane, with its word set along it."""
    x = LANE_X[track] - BAND_X - BAND_W if track == "ticket" else LANE_X[track] + BAND_X
    top = _at(first)[1] + (1.5 if mode == "ready" else 0)  # the two bars of a lane do not touch
    bottom = _at(last)[1] - (1.5 if mode == "draft" else 0)
    shape = (
        f'<rect class="pr pr-{mode}" x="{_g(x)}" y="{_g(top)}" width="{BAND_W}" '
        f'height="{_g(bottom - top)}" rx="4"/>'
    )
    centre = (x + BAND_W / 2 + FONTS["tx-small"].size * 0.34, (top + bottom) / 2)
    word = (
        f'<text class="pr-t pr-t-{mode}" transform="translate({_g(centre[0])} {_g(centre[1])}) '
        f'rotate(-90)" text-anchor="middle">{mode}</text>'
    )
    return [shape, word]


def _dots() -> list[str]:
    return [
        f'<circle class="dot dot-{c.who}" cx="{_g(_at(c.key)[0])}" cy="{_g(_at(c.key)[1])}" '
        f'r="{_g(DOT_R)}"/>'
        for c in COMMITS
    ]


def _legend() -> list[str]:
    """The key: three dots, then two bars; the kit's legend only knows its own node kinds."""
    entries = (
        ("human", "the human", 16),
        ("agent", "the coder's work", 16),
        ("code", "the factory's code", 16),
        ("draft", "pull request, draft", 26),
        ("ready", "pull request, ready", 26),
    )
    parts, x = [], 40.0
    for kind, label, swatch in entries:
        if swatch == 16:
            parts.append(
                f'<circle class="dot dot-{kind}" cx="{_g(x + 8)}" cy="{LEGEND_Y - 4}" r="6"/>'
            )
        else:
            parts.append(
                f'<rect class="pr pr-{kind}" x="{_g(x)}" y="{LEGEND_Y - 10.5}" width="26" '
                'height="13" rx="3"/>'
            )
        parts.append(f'<text class="lg" x="{_g(x + swatch + 8)}" y="{LEGEND_Y}">{label}</text>')
        x += swatch + 8 + text_width(label, FONTS["lg"]) + (44 if kind == "code" else 28)
    return parts


# --- colors, in both modes --------------------------------------------------------------------


def _mode_css(dark: bool) -> list[str]:
    base = BASE[dark]
    flow = EDGE_KINDS["flow"]
    tones = {kind: (spec.dark if dark else spec.light) for kind, spec in NODE_KINDS.items()}
    rules = [
        f".lane {{ stroke: {flow.dark if dark else flow.light}; }}",
        f".guide {{ stroke: {base.group}; }}",
        f".dot {{ stroke: {base.bg}; }}",
        f".pr-draft {{ fill: {tones['quiet'].fill}; stroke: {tones['quiet'].stroke}; }}",
        f".pr-ready {{ fill: {tones['human'].fill}; stroke: {tones['human'].stroke}; }}",
        f".pr-t-draft {{ fill: {tones['quiet'].accent}; }}",
        f".pr-t-ready {{ fill: {tones['human'].accent}; }}",
    ]
    rules += [f".dot-{who} {{ fill: {tones[who].stroke}; }}" for who in ("human", "agent", "code")]
    return rules


def _style() -> str:
    light = "\n".join(_mode_css(False))
    dark = "\n".join(f"  {rule}" for rule in _mode_css(True))
    return f"{STATIC_CSS}{light}\n@media (prefers-color-scheme: dark) {{\n{dark}\n}}\n"


class _Figure(Diagram):
    """The kit's diagram with the commits, lanes and pull request bars drawn under its text."""

    def to_svg(self) -> str:
        svg = super().to_svg().replace("</style>", _style() + "</style>", 1)
        head, mark, rest = svg.partition('<rect class="bg"')
        end = rest.index("/>") + 2  # the bars and lines go on the canvas, under every text
        art = "\n".join([*_lines(), *(p for b in BANDS for p in _band(*b)), *_dots(), *_legend()])
        return f"{head}{mark}{rest[:end]}\n{art}{rest[end:]}"


# --- the figure -------------------------------------------------------------------------------


def _label(commit: Commit) -> Text:
    """A commit's label, beside its dot on the side given, centered on the dot's row."""
    x, y = _at(commit.key)
    gap = LABEL_GAP[commit.track]
    step = round(FONTS["tx"].size * 1.45)
    first = y + FONTS["tx"].size * 0.34 - step * (len(commit.label) - 1) / 2
    left = commit.side == "left"
    return Text(x - gap if left else x + gap, first, commit.label, align="end" if left else "start")


def build() -> Diagram:
    d = _Figure(
        width=WIDTH,
        height=HEIGHT,
        title="Branches: one trunk, a short branch per work item",
        subtitle="Time runs down. A story and a feature's acceptance each have a branch of their "
        "own and come back by a merge commit.",
        description="Three vertical lanes, time running down: the story's branch "
        "ticket/<file stem> on the left, the trunk main in the middle, and the feature "
        "acceptance's branch acceptance/<feature> on the right. Each commit is a dot colored by "
        "who makes it: the human amber, the coder blue, the factory's code green. On main the "
        "human commits the drafts and FEATURE.md, then promotes the story with git mv into "
        "ongoing/. The story's branch leaves main at that promotion. Its first commit is the "
        "factory's: intake starts, with a draft pull request. The factory then commits ready to "
        "tests and tests to doing. Meanwhile the human commits another draft on main, so the "
        "factory merges main into the story's branch, only when main moved. The coder commits "
        "its work, feat, and a refactor if any. The factory commits doing to review, review to "
        "docs, docs to demo, and demo to accept, which marks the pull request ready. A bar "
        "beside the lane shows the pull request: draft from the first commit to the last, then "
        "ready until the human merges. The human merges the branch into main with a merge "
        "commit, never a squash, and the factory commits accept to done on main: the story is "
        "archived into done/ and its branch deleted. Once the feature's last story is archived, "
        "the acceptance's branch leaves main. The factory commits acceptance starts with a draft "
        "pull request, then feature to accept, which marks it ready. The human merges the report "
        "and its proposed drafts into main with a merge commit, and the factory commits accept "
        "to done with outcome accepted on main and deletes the branch.",
        legend=None,
    )
    for track, text in HEADS:
        d.add(Text(LANE_X[track], HEAD_Y, text, style="bold", align="middle"))
    d.add(*(_label(commit) for commit in COMMITS))
    return d


if __name__ == "__main__":
    save(build(), __file__)
