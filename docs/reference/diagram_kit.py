"""Book-quality SVG figures for the reference manual, drawn from plain Python.

Every figure in ``docs/reference/<chapter>/`` comes as three side-car files:

- ``<name>.md``: what the figure shows, in words. It is the source of truth for the figure's
  content, and agents read it instead of the picture.
- ``<name>.py``: the script that draws the figure with this kit.
- ``<name>.svg``: the drawing, referenced from the chapter's README.md.

A figure script
---------------
``docs/reference/<chapter>/<name>.py`` (a snake_case name) puts the kit on the path, defines
``build() -> Diagram`` and, run as a script, writes ``<name>.svg`` beside itself and prints the
warnings of ``Diagram.check()``::

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from diagram_kit import Diagram, Edge, Node, route, save  # noqa: E402


    def build() -> Diagram:
        d = Diagram(
            width=560,
            height=264,
            title="One stage hands over to the next",
            subtitle="The coder ends with an outcome; the factory checks it.",
            description="The coder agent on the left hands its outcome to the factory's "
            "check on the right.",
        )
        coder = d.add(Node(40, 104, 176, 96, kind="agent", tag="coder", title="Write the code"))
        coder.lines = ("until the check", "is green")
        check = d.add(Node(344, 104, 176, 96, kind="code", tag="factory", title="Check"))
        check.lines = ("lane, outcome", "and form")
        d.add(Edge(route(coder.right, check.left, "h"), label="outcome"))
        return d


    if __name__ == "__main__":
        save(build(), __file__)

Colours carry meaning, in light and dark mode alike. Node kinds: ``agent`` (blue, where a model
runs), ``human`` (amber), ``code`` (green, the factory's own code), ``ask`` (purple, asking the
human), ``stall`` (red, a stall or failure), ``back`` (orange, going back, rework), ``quiet``
(grey, nothing happens), ``end`` (dashed outline, an end state), ``concept`` (slate, an abstract
concept), ``store`` (stone, stored state: a Git repository, a file, a pull request). Edge kinds:
``flow``, ``back``, ``ask`` (dashed), ``stall`` (dashed), ``plain`` (thin, a relation) and
``dashed`` (grey, optional or asynchronous). Node shapes: ``box``, ``pill``, ``diamond``,
``document`` (a folded corner, for files) and ``cylinder`` (for stores such as Git).

Layout rules
------------
- Put node positions and sizes on the 8 px grid; ``check()`` warns about nodes that are not.
- Canvas: 40 px margins. The title's baseline is at y = 48, the subtitle's at y = 72, so
  content starts at y = 104. Keep the bottom 56 px free for a one-row legend, plus 24 px for
  each further row. Prefer widths of 720 to 1120 px (1200 at most): GitHub shows a figure about
  900 px wide, and a wider canvas shrinks its text.
- Node heights: tag, title and two body lines 96 px; tag, title and one line 72 px; title and
  one line 56 px; a pill with a title 48 px. A cylinder needs 24 px more for its cap; a diamond
  holds one or two short words. Widths: 136 px holds about 16 body characters, 176 px about 22.
- Gaps: 64 px between nodes whose edge has a one-word label, 96 px for two or three words (or
  stack the label in two short lines). 64 px between rows leaves a channel for a labeled line.
- Spread several edges along one side with ``port(side, offset)``, 16 or 24 px apart.
- In any text, `backticks` set a span in the monospace font. Tags are set in capitals, except
  their code spans.

Edge labels
-----------
A label sits above a horizontal segment (5 px clear) or right of a vertical one (8 px clear), on
the longest segment unless ``segment`` picks another; ``side`` puts it below or to the left,
``t`` (0 to 1) or ``pos`` (an x or y) moves it along the segment, and ``at`` places it anywhere.
Its halo takes the color of the band beneath it (the canvas, a shaded lane, a group). To keep
labels clear: give each label its own stretch of line, away from bends and other lines; on a
vertical line that crosses a lane border, use ``pos`` to keep the label inside one band; put the
labels of two parallel lines on their outer sides (``side="left"`` on the left one).

What check() finds, and what it does not
----------------------------------------
It warns about nodes off the grid; anything outside the canvas; nodes, free text and the
headings overlapping; text likely too wide or too tall for its node; edges running through a
node; diagonal legs; legs too short for an arrowhead; labels covering a node, free text, a line,
a lane border, a group outline or another label; free text on a line; lane and column heads too
wide; and the legend overlapping anything. Its limits: widths are estimates from Helvetica's
metrics plus 4% (Segoe UI measures within 6% of them, Inter runs wider); every shape counts as
its bounding box, so an edge passing a diamond's corner can be reported; a leg is not checked
against the node it starts or ends on; edges that cross or run along each other are not
reported. Nothing replaces looking at both previews.

Command line
------------
``uv run python docs/reference/diagram_kit.py render [script ...]`` runs the given figure
scripts, or every ``docs/reference/<chapter>/*.py`` (chapter folders starting with ``_`` are
skipped). ``uv run python docs/reference/diagram_kit.py preview <svg> ... [--out DIR]`` writes a
light and a dark PNG of each SVG with headless Edge or Chrome (``BROWSER_BIN`` overrides the
browser) and prints their paths; ``--scale 2 --crop X,Y,W,H`` zooms into a detail.
"""

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from html import escape
from itertools import combinations, pairwise
from pathlib import Path
from typing import Literal

__all__ = [
    "EDGE_KINDS",
    "FONTS",
    "NODE_KINDS",
    "Column",
    "Diagram",
    "Edge",
    "Font",
    "Group",
    "Lane",
    "Legend",
    "Node",
    "Text",
    "cropped",
    "figure_scripts",
    "find_browser",
    "main",
    "preview",
    "render_scripts",
    "route",
    "save",
    "svg_size",
    "text_width",
    "themed",
]

type Point = tuple[float, float]
type Bounds = tuple[float, float, float, float]  # x0, y0, x1, y1
type Lines = str | Sequence[str]
type Side = Literal["top", "bottom", "left", "right"]
type Shape = Literal["box", "pill", "diamond", "document", "cylinder"]
type Arrow = Literal["end", "start", "both", "none"]
type Align = Literal["start", "middle", "end"]
type LabelSide = Literal["auto", "above", "below", "left", "right"]
type RouteShape = Literal["h", "v", "hv", "vh", "hvh", "vhv"]
type TextStyle = Literal["normal", "bold", "mono", "note", "small"]

SUMMARY = "Book-quality SVG figures for the reference manual, drawn from plain Python."
KIT = Path(__file__).resolve()
GRID = 8
MARGIN = 40
FONT = '"Inter", "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, "Liberation Mono", monospace'
DARK_QUERY = "@media (prefers-color-scheme: dark)"
EDGE_BROWSER = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

RADIUS = 8  # box corners
CORNER = 8  # edge bends
PAD_X = 12  # text inside a node, left and right
PAD_Y = 8  # text inside a node, top and bottom
TRIM = 3.0  # an arrowed line stops this far before its end; the head reaches the end
LABEL_GAP = 5.0  # between a horizontal line and its label block
LABEL_GAP_X = 8.0  # between a vertical line and its label
LABEL_LINE = 15.0
BASELINE = 0.34  # baseline below a row's middle, in em: centers capitals and lowercase alike
WIDTH_SAFETY = 1.04  # estimated widths run this much over Helvetica's, for wider fallbacks


# --- palette ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Tone:
    """One kind's colors in one mode: the fill, the outline and the accent for its text."""

    fill: str
    stroke: str
    accent: str


@dataclass(frozen=True)
class NodeKind:
    """What a node kind means (its default legend label) and its tones in light and dark."""

    label: str
    light: Tone
    dark: Tone


@dataclass(frozen=True)
class EdgeKind:
    """What an edge kind means and how it is drawn: colors in light and dark, width, dashes."""

    label: str
    light: str
    dark: str
    text_light: str
    text_dark: str
    width: float = 1.5
    dash: str = ""


@dataclass(frozen=True)
class Base:
    """The colors every figure shares in one mode."""

    bg: str
    ink: str  # titles
    body: str  # body text
    muted: str  # subtitles, notes, captions
    hair: str  # lane borders and rules
    lane: str  # the shaded lane
    group: str  # group outlines


BASE = (
    Base("#ffffff", "#1b1f24", "#363b43", "#5d6470", "#dde1e6", "#f5f7f9", "#b4bac3"),
    Base("#0f141a", "#e6edf3", "#c9d1d9", "#9da7b3", "#2a313b", "#151b22", "#3d4651"),
)

NODE_KINDS: dict[str, NodeKind] = {
    "agent": NodeKind(
        "agent: a model runs",
        Tone("#eaf2fc", "#2f6db5", "#2862a5"),
        Tone("#13263d", "#5b9be6", "#8dbdf4"),
    ),
    "human": NodeKind(
        "the human",
        Tone("#fff4df", "#c27400", "#965a00"),
        Tone("#33260f", "#e0a33a", "#f2bd63"),
    ),
    "code": NodeKind(
        "the factory's code",
        Tone("#e8f5ef", "#2a8a6e", "#1e6f58"),
        Tone("#0f2e26", "#3fb68f", "#72d3b0"),
    ),
    "ask": NodeKind(
        "asks the human",
        Tone("#f3eefb", "#7a4fb5", "#673e9f"),
        Tone("#251c38", "#a98be0", "#c4aef2"),
    ),
    "stall": NodeKind(
        "stall or failure",
        Tone("#fcecec", "#b53a3a", "#9f2d2d"),
        Tone("#371a1c", "#e06c6c", "#f29191"),
    ),
    "back": NodeKind(
        "goes back, rework",
        Tone("#fdf0e5", "#d0661a", "#a64e0e"),
        Tone("#372214", "#ef8a3c", "#f6a96d"),
    ),
    "quiet": NodeKind(
        "nothing happens",
        Tone("#f4f5f7", "#a3a8b2", "#646b76"),
        Tone("#1a2029", "#6b7380", "#a2abb7"),
    ),
    "end": NodeKind(
        "end state",
        Tone("#ffffff", "#8a8f99", "#5d6470"),
        Tone("#0f141a", "#8b939e", "#a2abb7"),
    ),
    "concept": NodeKind(
        "concept",
        Tone("#eef1f6", "#5d6f8c", "#4b5b76"),
        Tone("#1b2331", "#8a9bb8", "#afbdd5"),
    ),
    "store": NodeKind(
        "stored state",
        Tone("#f4f1ea", "#8a7a5c", "#6c5e44"),
        Tone("#27241d", "#b0a17f", "#cdbf9d"),
    ),
}

EDGE_KINDS: dict[str, EdgeKind] = {
    "flow": EdgeKind("moves on", "#4b515c", "#bcc4ce", "#2b3038", "#dfe6ee"),
    "back": EdgeKind("goes back", "#d0661a", "#ef8a3c", "#a64e0e", "#f6a96d"),
    "ask": EdgeKind("asks the human", "#7a4fb5", "#a98be0", "#673e9f", "#c4aef2", dash="6 4"),
    "stall": EdgeKind("stalls, fails", "#b53a3a", "#e06c6c", "#9f2d2d", "#f29191", dash="6 4"),
    "plain": EdgeKind("relates to", "#8f96a1", "#717a87", "#5d6470", "#9da7b3", width=1.1),
    "dashed": EdgeKind(
        "optional or asynchronous", "#6b7280", "#939ba6", "#5d6470", "#9da7b3", 1.4, "3 3"
    ),
}


# --- text ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Font:
    """A text style: size in px, weight, letter spacing in em, monospace or not."""

    size: float
    weight: int = 400
    spacing: float = 0.0
    mono: bool = False

    @property
    def bold(self) -> bool:
        return self.weight >= 600

    def css(self) -> str:
        parts = [f"font-size: {_num(self.size)}px", f"font-weight: {self.weight}"]
        if self.spacing:
            parts.append(f"letter-spacing: {_num(self.spacing)}em")
        if self.mono:
            parts.append(f"font-family: {MONO}")
        return "; ".join(parts)


FONTS: dict[str, Font] = {
    "ttl": Font(20, 600),
    "sub": Font(13.5),
    "tag": Font(10.5, 600, 0.09),
    "nt": Font(14.5, 700),
    "nb": Font(12.5),
    "lb": Font(12),
    "lane-h": Font(13, 700),
    "lane-n": Font(12),
    "col-h": Font(12.5, 700),
    "grp-c": Font(12, 600),
    "tx": Font(13),
    "tx-bold": Font(13, 700),
    "tx-mono": Font(12, mono=True),
    "tx-note": Font(12),
    "tx-small": Font(11),
    "lg": Font(12),
}
TEXT_CLASSES: dict[str, str] = {
    "normal": "tx",
    "bold": "tx-bold",
    "mono": "tx-mono",
    "note": "tx-note",
    "small": "tx-small",
}


def _widths(table: str) -> list[int]:
    return [int(width) for width in table.split()]


# Helvetica's advance widths (per 1000 em) for ASCII 32 to 126, regular and bold.
_REGULAR = _widths(
    "278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 556 556 556 556 556 556 "
    "556 556 556 556 278 278 584 584 584 556 1015 667 667 722 722 667 611 778 722 278 500 667 "
    "556 833 722 778 667 778 722 667 611 722 667 944 667 667 611 278 278 278 469 556 333 556 "
    "556 500 556 556 278 556 556 222 222 500 222 833 556 556 556 556 333 500 278 556 500 722 "
    "500 500 500 334 260 334 584"
)
_BOLD = _widths(
    "278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 556 556 556 556 556 556 "
    "556 556 556 556 333 333 584 584 584 611 975 722 722 722 722 667 611 778 722 278 556 722 "
    "611 833 722 778 667 778 722 667 611 722 667 944 667 667 611 333 278 333 584 556 333 556 "
    "611 556 611 556 333 611 611 278 278 556 278 889 611 611 611 611 389 556 333 611 556 778 "
    "556 556 500 389 280 389 584"
)
_OTHER = {"·": 278, "–": 556, "—": 1000, "…": 1000, "→": 1000, "←": 1000, "’": 222, "×": 584}
MONO_ADVANCE = 0.6  # em per character
CODE_SCALE = 0.92  # a `code` span's size relative to the text around it


def _segments(text: str) -> list[tuple[str, bool]]:
    """The line split at backticks: (text, is_code) pairs, empty ones dropped."""
    return [(part, i % 2 == 1) for i, part in enumerate(text.split("`")) if part]


def _char_width(char: str, bold: bool) -> float:
    code = ord(char)
    if 32 <= code <= 126:
        return (_BOLD if bold else _REGULAR)[code - 32]
    return _OTHER.get(char, 600)


def text_width(text: str, font: Font) -> float:
    """Estimated width in px of one line: Helvetica metrics, `code` spans in monospace."""
    total = 0.0
    for part, code in _segments(text):
        if code or font.mono:
            scale = CODE_SCALE if code and not font.mono else 1.0
            total += len(part) * MONO_ADVANCE * font.size * scale
        else:
            total += sum(_char_width(c, font.bold) for c in part) * font.size / 1000
    total += len(text.replace("`", "")) * font.spacing * font.size
    return total * WIDTH_SAFETY


def _lines(value: Lines) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    return tuple(value)


def _num(value: float) -> str:
    """A number for SVG: at most two decimals, no trailing zeros, never minus zero."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def _pt(point: Point) -> str:
    return f"{_num(point[0])} {_num(point[1])}"


def _esc(text: str) -> str:
    return escape(text, quote=False)


def _tspans(text: str) -> str:
    return "".join(
        f'<tspan class="code">{_esc(part)}</tspan>' if code else _esc(part)
        for part, code in _segments(text)
    )


def _upper(text: str) -> str:
    """Capitals, except inside `code` spans."""
    return "`".join(p if i % 2 else p.upper() for i, p in enumerate(text.split("`")))


def _text(at: Point, text: str, cls: str, anchor: Align = "start") -> str:
    return (
        f'<text class="{cls}" x="{_num(at[0])}" y="{_num(at[1])}" text-anchor="{anchor}">'
        f"{_tspans(text)}</text>"
    )


def _block_x(x: float, width: float, align: Align) -> float:
    """The left edge of a block of `width` anchored at x."""
    return {"start": x, "middle": x - width / 2, "end": x - width}[align]


# --- elements -----------------------------------------------------------------------------------


@dataclass
class Node:
    """A box on the canvas: its kind picks the colors, its shape the outline.

    The text is a block centered in the node: the tag (small capitals in the kind's accent), the
    title (bold) and the body lines.
    """

    x: float
    y: float
    w: float
    h: float
    kind: str = "concept"
    title: str = ""
    tag: str = ""
    lines: Lines = ()
    shape: Shape = "box"
    align: Align = "middle"

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def bounds(self) -> Bounds:
        return (self.x, self.y, self.x2, self.y2)

    @property
    def top(self) -> Point:
        return self.port("top")

    @property
    def bottom(self) -> Point:
        return self.port("bottom")

    @property
    def left(self) -> Point:
        return self.port("left")

    @property
    def right(self) -> Point:
        return self.port("right")

    def port(self, side: Side, offset: float = 0) -> Point:
        """A point on the outline of `side`, `offset` px from its middle (right or down > 0).

        Use several ports to spread edges along one side, 16 or 24 px apart.
        """
        x, y = {
            "top": (self.cx + offset, self.y),
            "bottom": (self.cx + offset, self.y2),
            "left": (self.x, self.cy + offset),
            "right": (self.x2, self.cy + offset),
        }[side]
        depth = _outline_depth(self, side, offset)
        dx, dy = {"top": (0, 1), "bottom": (0, -1), "left": (1, 0), "right": (-1, 0)}[side]
        return (x + dx * depth, y + dy * depth)


def _outline_depth(node: Node, side: Side, offset: float) -> float:
    """How far inside its bounding box the node's outline runs at `offset` along `side`."""
    across = side in ("top", "bottom")
    if node.shape == "diamond":
        half, depth = (node.w / 2, node.h / 2) if across else (node.h / 2, node.w / 2)
        return depth * min(abs(offset) / half, 1.0)
    if node.shape == "pill" and not across:
        return _arc_depth(node.h / 2, node.h / 2, offset)
    if node.shape == "cylinder" and across:
        return _arc_depth(node.w / 2, _cap(node), offset)
    return 0.0


def _arc_depth(along: float, across: float, offset: float) -> float:
    ratio = min(abs(offset) / along, 1.0)
    return across * (1 - math.sqrt(1 - ratio * ratio))


def _cap(node: Node) -> float:
    """The vertical radius of a cylinder's top and bottom ellipses."""
    return min(10.0, node.h / 6)


def _fold(node: Node) -> float:
    """The size of a document's folded corner."""
    return min(16.0, node.w / 4, node.h / 4)


@dataclass
class Edge:
    """An orthogonal line through `points`, with rounded bends and an arrowhead.

    The label goes on the longest segment (or `segment`, an index into the segments): above a
    horizontal one, right of a vertical one, unless `side` says otherwise. Along the segment it
    sits at its middle, at `t` (0 to 1), or at `pos` (the x on a horizontal segment, the y of the
    block's middle on a vertical one). `at` overrides all that: it is the label block's anchor,
    with x aligned by `align` and y the block's vertical middle.
    """

    points: Sequence[Point]
    kind: str = "flow"
    label: Lines = ()
    at: Point | None = None
    align: Align = "middle"
    side: LabelSide = "auto"
    t: float = 0.5
    pos: float | None = None
    segment: int | None = None
    arrow: Arrow = "end"


@dataclass
class Lane:
    """A horizontal swimlane band with its head on the left; lanes shade alternately."""

    y: float
    h: float
    label: str
    note: Lines = ()
    x: float = MARGIN
    w: float = 0  # 0: across the canvas, margin to margin
    head: float = 128


@dataclass
class Column:
    """A vertical column: a header with a rule under it; dotted dividers between columns.

    The header takes the top 40 px (56 with a note); start the column's content below that.
    """

    x: float
    y: float
    w: float
    h: float
    label: str
    note: str = ""

    @property
    def header(self) -> float:
        """The y of the rule under the header."""
        return self.y + (56 if self.note else 40)


@dataclass
class Group:
    """A rounded container with a caption at its top left; leave 32 px above its first node."""

    x: float
    y: float
    w: float
    h: float
    caption: str = ""
    kind: str = ""  # a node kind tints the outline and the caption
    dashed: bool = False

    @property
    def bounds(self) -> Bounds:
        return (self.x, self.y, self.x + self.w, self.y + self.h)


@dataclass
class Text:
    """Free text; y is the first line's baseline."""

    x: float
    y: float
    lines: Lines
    style: TextStyle = "normal"
    align: Align = "start"
    kind: str = ""  # a node kind colors the text with its accent


@dataclass
class Legend:
    """The key, built from the node and edge kinds a figure uses.

    `nodes` and `edges` override the default labels by kind; `hide` leaves entries out, as
    "node:<kind>" or "edge:<kind>". Without x and y it sits at the bottom left.
    """

    x: float | None = None
    y: float | None = None  # the first row's baseline
    nodes: dict[str, str] = field(default_factory=dict)
    edges: dict[str, str] = field(default_factory=dict)
    hide: Sequence[str] = ()


type Element = Node | Edge | Lane | Column | Group | Text


@dataclass
class Diagram:
    """A figure: a canvas with a title, elements in the order added, and a legend."""

    width: float
    height: float
    title: str
    subtitle: str = ""
    description: str = ""
    legend: Legend | None = field(default_factory=Legend)
    elements: list[Element] = field(default_factory=list)

    def add[E: Element](self, element: E, *more: Element) -> E:
        """Add elements; returns the first, so `a = d.add(Node(...))` keeps a handle."""
        self.elements.append(element)
        self.elements.extend(more)
        return element

    def of[T](self, cls: type[T]) -> list[T]:
        """The elements of one class, in the order added."""
        return [e for e in self.elements if isinstance(e, cls)]

    def to_svg(self) -> str:
        return _svg(self)

    def render(self, path: str | Path) -> Path:
        """Write the SVG (UTF-8, LF line endings) and return its path."""
        target = Path(path)
        target.write_text(self.to_svg(), encoding="utf-8", newline="\n")
        return target

    def check(self) -> list[str]:
        """Warnings about likely layout faults; see the module docstring for the limits."""
        return [warning for rule in _RULES for warning in rule(self)]


# --- geometry -----------------------------------------------------------------------------------


def route(
    start: Point, end: Point, shape: RouteShape = "hvh", via: float | None = None
) -> list[Point]:
    """Orthogonal points from start to end.

    `shape` names the legs: "h" or "v" is straight, "hv" and "vh" an L, "hvh" and "vhv" a Z
    whose middle leg sits at `via` (x for "hvh", y for "vhv"; default halfway).
    """
    (x0, y0), (x1, y1) = start, end
    if shape in ("h", "v"):
        return [start, end]
    if shape == "hv":
        return [start, (x1, y0), end]
    if shape == "vh":
        return [start, (x0, y1), end]
    if shape == "hvh":
        mid = (x0 + x1) / 2 if via is None else via
        return [start, (mid, y0), (mid, y1), end]
    if shape == "vhv":
        mid = (y0 + y1) / 2 if via is None else via
        return [start, (x0, mid), (x1, mid), end]
    raise ValueError(f"unknown route shape {shape!r}: use h, v, hv, vh, hvh or vhv")


def _dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _towards(a: Point, b: Point, length: float) -> Point:
    """The point `length` px from a towards b."""
    d = _dist(a, b) or 1.0
    return (a[0] + (b[0] - a[0]) * length / d, a[1] + (b[1] - a[1]) * length / d)


def _hits(a: Bounds, b: Bounds) -> bool:
    """Whether two boxes overlap with a positive area (or a segment crosses a box's inside)."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _shrink(box: Bounds, by: float) -> Bounds:
    return (box[0] + by, box[1] + by, box[2] - by, box[3] - by)


def _seg_bounds(a: Point, b: Point) -> Bounds:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def _inside(point: Point, box: Bounds) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


# --- node drawing -------------------------------------------------------------------------------


def _shape_box(node: Node) -> str:
    return _rect(node.bounds, RADIUS, "sh")


def _shape_pill(node: Node) -> str:
    return _rect(node.bounds, node.h / 2, "sh")


def _shape_diamond(node: Node) -> str:
    points = [(node.cx, node.y), (node.x2, node.cy), (node.cx, node.y2), (node.x, node.cy)]
    return f'<polygon class="sh" points="{" ".join(_pt(p).replace(" ", ",") for p in points)}"/>'


def _shape_document(node: Node) -> str:
    f, r = _fold(node), 4.0
    x0, y0, x1, y1 = node.bounds
    body = (
        f"M {_pt((x0 + r, y0))} H {_num(x1 - f)} L {_pt((x1, y0 + f))} V {_num(y1 - r)} "
        f"Q {_pt((x1, y1))} {_pt((x1 - r, y1))} H {_num(x0 + r)} Q {_pt((x0, y1))} "
        f"{_pt((x0, y1 - r))} V {_num(y0 + r)} Q {_pt((x0, y0))} {_pt((x0 + r, y0))} Z"
    )
    fold = f"M {_pt((x1 - f, y0))} V {_num(y0 + f - 2)} Q {_pt((x1 - f, y0 + f))} " + (
        f"{_pt((x1 - f + 2, y0 + f))} H {_num(x1)} Z"
    )
    return f'<path class="sh" d="{body}"/><path class="fold" d="{fold}"/>'


def _shape_cylinder(node: Node) -> str:
    ry, rx = _cap(node), node.w / 2
    x0, y0, x1, y1 = node.bounds
    arc = f"A {_num(rx)} {_num(ry)} 0 0 1"
    body = (
        f"M {_pt((x0, y0 + ry))} {arc} {_pt((x1, y0 + ry))} V {_num(y1 - ry)} "
        f"{arc} {_pt((x0, y1 - ry))} Z"
    )
    return (
        f'<path class="sh" d="{body}"/><ellipse class="fold" cx="{_num(node.cx)}" '
        f'cy="{_num(y0 + ry)}" rx="{_num(rx)}" ry="{_num(ry)}"/>'
    )


_SHAPES = {
    "box": _shape_box,
    "pill": _shape_pill,
    "diamond": _shape_diamond,
    "document": _shape_document,
    "cylinder": _shape_cylinder,
}


def _rect(box: Bounds, radius: float, cls: str) -> str:
    x0, y0, x1, y1 = box
    return (
        f'<rect class="{cls}" x="{_num(x0)}" y="{_num(y0)}" width="{_num(x1 - x0)}" '
        f'height="{_num(y1 - y0)}" rx="{_num(radius)}"/>'
    )


@dataclass(frozen=True)
class _Row:
    text: str
    cls: str
    height: float


def _rows(node: Node) -> list[_Row]:
    rows: list[_Row] = []
    if node.tag:
        rows.append(_Row(_upper(node.tag), "tag", 15))
    if node.title:
        rows.append(_Row(node.title, "nt", 20))
    body = _lines(node.lines)
    if body and rows:
        rows.append(_Row("", "gap", 4))
    rows.extend(_Row(line, "nb", 17) for line in body)
    return rows


def _text_area(node: Node) -> Bounds:
    """The part of the node the text block is centered in."""
    if node.shape == "cylinder":
        return (node.x, node.y + 2 * _cap(node), node.x2, node.y2)
    return node.bounds


def _layout(node: Node) -> list[tuple[_Row, float]]:
    """Each text row of the node with its baseline."""
    rows = _rows(node)
    _, y0, _, y1 = _text_area(node)
    top = (y0 + y1) / 2 - sum(r.height for r in rows) / 2
    placed = []
    for row in rows:
        if row.cls != "gap":
            placed.append((row, top + row.height / 2 + BASELINE * FONTS[row.cls].size))
        top += row.height
    return placed


def _node_svg(node: Node) -> str:
    if node.kind not in NODE_KINDS:
        raise ValueError(f"unknown node kind {node.kind!r}: use one of {', '.join(NODE_KINDS)}")
    if node.shape not in _SHAPES:
        raise ValueError(f"unknown shape {node.shape!r}: use one of {', '.join(_SHAPES)}")
    x = node.cx if node.align == "middle" else node.x + PAD_X
    parts = [f'<g class="n-{node.kind}">', _SHAPES[node.shape](node)]
    parts.extend(_text((x, base), row.text, row.cls, node.align) for row, base in _layout(node))
    parts.append("</g>")
    return "".join(parts)


# --- edge drawing -------------------------------------------------------------------------------


def _trimmed(edge: Edge) -> list[Point]:
    """The points with the arrowed ends pulled back, so the line ends inside the head."""
    points = list(edge.points)
    if edge.arrow in ("end", "both"):
        points[-1] = _towards(points[-1], points[-2], TRIM)
    if edge.arrow in ("start", "both"):
        points[0] = _towards(points[0], points[1], TRIM)
    return points


def _path(points: Sequence[Point]) -> str:
    """An SVG path through the points with rounded bends."""
    parts = [f"M {_pt(points[0])}"]
    for a, b, c in zip(points, points[1:], points[2:], strict=False):
        r = min(CORNER, _dist(a, b) / 2, _dist(b, c) / 2)
        parts.append(f"L {_pt(_towards(b, a, r))} Q {_pt(b)} {_pt(_towards(b, c, r))}")
    parts.append(f"L {_pt(points[-1])}")
    return " ".join(parts)


def _edge_svg(edge: Edge) -> str:
    if edge.kind not in EDGE_KINDS:
        raise ValueError(f"unknown edge kind {edge.kind!r}: use one of {', '.join(EDGE_KINDS)}")
    if len(edge.points) < 2:
        raise ValueError("an edge needs at least two points")
    marker = f"url(#ah-{edge.kind})"
    ends = {
        "end": f' marker-end="{marker}"',
        "start": f' marker-start="{marker}"',
        "both": f' marker-start="{marker}" marker-end="{marker}"',
        "none": "",
    }[edge.arrow]
    return f'<path class="e e-{edge.kind}" d="{_path(_trimmed(edge))}"{ends}/>'


def _marker(kind: str) -> str:
    size = 7.5 if kind == "plain" else 9.0
    ref = 10 - TRIM * 10 / size
    return (
        f'<marker id="ah-{kind}" viewBox="0 0 10 10" refX="{_num(ref)}" refY="5" '
        f'markerWidth="{_num(size)}" markerHeight="{_num(size)}" markerUnits="userSpaceOnUse" '
        f'orient="auto-start-reverse"><path class="ah-{kind}" d="M0.5 1 L10 5 L0.5 9 L2.6 5 Z"/>'
        "</marker>"
    )


def _label_segment(edge: Edge) -> tuple[Point, Point]:
    segments = list(pairwise(edge.points))
    if edge.segment is not None:
        return segments[edge.segment]
    return max(segments, key=lambda s: _dist(*s))


def _label_place(edge: Edge, height: float) -> tuple[float, float, Align]:
    """Where the label block goes: anchor x, block top, alignment."""
    if edge.at is not None:
        return (edge.at[0], edge.at[1] - height / 2, edge.align)
    a, b = _label_segment(edge)
    x, y = a[0] + (b[0] - a[0]) * edge.t, a[1] + (b[1] - a[1]) * edge.t
    horizontal = abs(a[1] - b[1]) < abs(a[0] - b[0])
    if edge.pos is not None:
        x, y = (edge.pos, y) if horizontal else (x, edge.pos)
    if horizontal:
        if edge.side == "below":
            return (x, y + LABEL_GAP, "middle")
        return (x, y - LABEL_GAP - height, "middle")
    if edge.side == "left":
        return (x - LABEL_GAP_X, y - height / 2, "end")
    return (x + LABEL_GAP_X, y - height / 2, "start")


def _label_bounds(edge: Edge) -> Bounds | None:
    """The ink box of the label, or None when the edge has none."""
    lines = _lines(edge.label)
    if not lines:
        return None
    height = LABEL_LINE * len(lines)
    x, top, align = _label_place(edge, height)
    width = max(text_width(line, FONTS["lb"]) for line in lines)
    x0 = _block_x(x, width, align)
    return (x0, top + 2, x0 + width, top + height - 1)


def _label_svg(edge: Edge, halo: str) -> str:
    lines = _lines(edge.label)
    if not lines:
        return ""
    x, top, align = _label_place(edge, LABEL_LINE * len(lines))
    first = top + LABEL_LINE / 2 + BASELINE * FONTS["lb"].size
    cls = f"lb lb-{edge.kind}{halo}"
    return "".join(
        _text((x, first + i * LABEL_LINE), line, cls, align) for i, line in enumerate(lines)
    )


def _halo(diagram: Diagram, edge: Edge) -> str:
    """The halo class for a label: it takes the color of the band the label sits on."""
    box = _label_bounds(edge)
    if box is None:
        return ""
    center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    if any(_inside(center, g.bounds) for g in diagram.of(Group)):
        return ""
    for index, lane in enumerate(diagram.of(Lane)):
        if _inside(center, _lane_bounds(lane, diagram)):
            return " on-lane" if index % 2 == 0 else ""
    return ""


# --- lanes, columns, groups, free text ----------------------------------------------------------


def _lane_bounds(lane: Lane, diagram: Diagram) -> Bounds:
    width = lane.w or diagram.width - lane.x - MARGIN
    return (lane.x, lane.y, lane.x + width, lane.y + lane.h)


def _lane_svg(lane: Lane, index: int, diagram: Diagram) -> str:
    box = _lane_bounds(lane, diagram)
    notes = _lines(lane.note)
    top = lane.y + lane.h / 2 - (20 + 16 * len(notes)) / 2
    divider = lane.x + lane.head
    parts = [
        _rect(box, 0, "lane-a" if index % 2 == 0 else "lane-b"),
        f'<path class="rule" d="M {_pt((divider, lane.y))} V {_num(lane.y + lane.h)}"/>',
        _text((lane.x + 16, top + 14.5), lane.label, "lane-h"),
    ]
    parts.extend(_text((lane.x + 16, top + 34 + 16 * i), n, "lane-n") for i, n in enumerate(notes))
    return "".join(parts)


def _column_svg(column: Column) -> str:
    center, rule = column.x + column.w / 2, f"M {_pt((column.x, column.header))} H "
    parts = [
        _text((center, column.y + 21), column.label, "col-h", "middle"),
        f'<path class="col-u" d="{rule}{_num(column.x + column.w)}"/>',
    ]
    if column.note:
        parts.insert(1, _text((center, column.y + 39), column.note, "lane-n", "middle"))
    return "".join(parts)


def _dividers(columns: Sequence[Column]) -> str:
    """Dotted rules halfway between neighbouring columns, from header to foot."""
    ordered = sorted(columns, key=lambda c: c.x)
    paths = [
        f"M {_pt(((a.x + a.w + b.x) / 2, min(a.y, b.y)))} V {_num(max(a.y + a.h, b.y + b.h))}"
        for a, b in pairwise(ordered)
    ]
    return f'<path class="rule col-r" d="{" ".join(paths)}"/>' if paths else ""


def _group_svg(group: Group) -> str:
    tint = f" g-{group.kind}" if group.kind else ""
    dash = " grp-d" if group.dashed else ""
    parts = [_rect(group.bounds, 12, f"grp{tint}{dash}")]
    if group.caption:
        accent = f" k-{group.kind}" if group.kind else ""
        parts.append(_text((group.x + 14, group.y + 21), group.caption, f"grp-c{accent}"))
    return "".join(parts)


def _text_cls(text: Text) -> str:
    accent = f" k-{text.kind}" if text.kind else ""
    return f"{TEXT_CLASSES[text.style]}{accent}"


def _text_step(text: Text) -> float:
    return round(FONTS[TEXT_CLASSES[text.style]].size * 1.45)


def _free_text_svg(text: Text) -> str:
    step, cls = _text_step(text), _text_cls(text)
    return "".join(
        _text((text.x, text.y + i * step), line, cls, text.align)
        for i, line in enumerate(_lines(text.lines))
    )


def _free_text_bounds(text: Text) -> Bounds:
    lines, font = _lines(text.lines), FONTS[TEXT_CLASSES[text.style]]
    width = max((text_width(line, font) for line in lines), default=0.0)
    x0 = _block_x(text.x, width, text.align)
    bottom = text.y + _text_step(text) * (len(lines) - 1) + font.size * 0.25
    return (x0, text.y - font.size * 0.75, x0 + width, bottom)


# --- legend -------------------------------------------------------------------------------------


LEGEND_ROW = 24.0
LEGEND_GAP = 28.0  # between entries
SWATCH = 26.0


@dataclass(frozen=True)
class _Entry:
    what: Literal["node", "edge"]
    kind: str
    label: str

    @property
    def width(self) -> float:
        return SWATCH + 8 + text_width(self.label, FONTS["lg"])


def _used_node_kinds(diagram: Diagram) -> list[str]:
    used = {n.kind for n in diagram.of(Node)}
    used |= {g.kind for g in diagram.of(Group)} | {t.kind for t in diagram.of(Text)}
    unknown = sorted(used - set(NODE_KINDS) - {""})
    if unknown:
        raise ValueError(f"unknown kind {unknown[0]!r}: use one of {', '.join(NODE_KINDS)}")
    return [kind for kind in NODE_KINDS if kind in used]


def _used_edge_kinds(diagram: Diagram) -> list[str]:
    used = {e.kind for e in diagram.of(Edge)}
    return [kind for kind in EDGE_KINDS if kind in used]


def _legend_entries(diagram: Diagram, legend: Legend) -> list[_Entry]:
    nodes = {n.kind for n in diagram.of(Node)}
    entries = [
        _Entry("node", k, legend.nodes.get(k, NODE_KINDS[k].label))
        for k in NODE_KINDS
        if k in nodes and f"node:{k}" not in legend.hide
    ]
    entries += [
        _Entry("edge", k, legend.edges.get(k, EDGE_KINDS[k].label))
        for k in _used_edge_kinds(diagram)
        if f"edge:{k}" not in legend.hide
    ]
    return entries


def _legend_rows(entries: list[_Entry], span: float) -> list[list[_Entry]]:
    """One row when all fit; otherwise node kinds and edge kinds on rows of their own."""
    if sum(e.width + LEGEND_GAP for e in entries) - LEGEND_GAP <= span:
        return [entries] if entries else []
    rows: list[list[_Entry]] = []
    for what in ("node", "edge"):
        rows.extend(_wrap([e for e in entries if e.what == what], span))
    return rows


def _wrap(entries: list[_Entry], span: float) -> list[list[_Entry]]:
    rows: list[list[_Entry]] = []
    used = span + 1
    for entry in entries:
        if used + entry.width > span:
            rows.append([])
            used = 0.0
        rows[-1].append(entry)
        used += entry.width + LEGEND_GAP
    return rows


def _legend_layout(diagram: Diagram) -> list[tuple[_Entry, Point]]:
    """Each legend entry with the left end of its swatch and its text baseline."""
    legend = diagram.legend
    if legend is None:
        return []
    x0 = MARGIN if legend.x is None else legend.x
    rows = _legend_rows(_legend_entries(diagram, legend), diagram.width - x0 - MARGIN)
    y0 = diagram.height - 24 - LEGEND_ROW * (len(rows) - 1) if legend.y is None else legend.y
    placed = []
    for i, row in enumerate(rows):
        x = x0
        for entry in row:
            placed.append((entry, (x, y0 + i * LEGEND_ROW)))
            x += entry.width + LEGEND_GAP
    return placed


def _legend_bounds(diagram: Diagram) -> Bounds | None:
    placed = _legend_layout(diagram)
    if not placed:
        return None
    x1 = max(x + e.width for e, (x, _) in placed)
    ys = [y for _, (_, y) in placed]
    return (placed[0][1][0], min(ys) - 12, x1, max(ys) + 4)


def _swatch(entry: _Entry, at: Point) -> str:
    x, y = at
    if entry.what == "node":
        box = (x, y - 10.5, x + SWATCH, y + 2.5)
        return f'<g class="n-{entry.kind}">{_rect(box, 3, "sh")}</g>'
    line = Edge([(x, y - 4), (x + SWATCH, y - 4)], kind=entry.kind)
    return _edge_svg(line)


def _legend_svg(diagram: Diagram) -> str:
    return "\n".join(
        _swatch(entry, (x, y)) + _text((x + SWATCH + 8, y), entry.label, "lg")
        for entry, (x, y) in _legend_layout(diagram)
    )


# --- the document -------------------------------------------------------------------------------


def _static_css(edges: Iterable[str]) -> list[str]:
    rules = [
        f"text {{ font-family: {FONT}; }}",
        f".code {{ font-family: {MONO}; font-size: {_num(CODE_SCALE)}em; }}",
        *(f".{cls} {{ {font.css()}; }}" for cls, font in FONTS.items()),
        ".sh, .fold { stroke-width: 1.5; stroke-linejoin: round; }",
        ".n-end .sh { stroke-dasharray: 5 3; }",
        ".e { fill: none; stroke-linejoin: round; }",
        ".lb { paint-order: stroke fill; stroke-width: 4px; stroke-linejoin: round; }",
        ".rule, .lane-a, .lane-b { stroke-width: 1; shape-rendering: crispEdges; }",
        ".rule, .col-u { fill: none; } .col-r { stroke-dasharray: 2 3; }",
        ".col-u { stroke-width: 1; shape-rendering: crispEdges; }",
        ".grp { stroke-width: 1; } .grp-d { stroke-dasharray: 5 4; }",
    ]
    for kind in edges:
        style = EDGE_KINDS[kind]
        dash = f" stroke-dasharray: {style.dash};" if style.dash else ""
        rules.append(f".e-{kind} {{ stroke-width: {_num(style.width)};{dash} }}")
    return rules


def _base_css(base: Base) -> list[str]:
    return [
        f".bg {{ fill: {base.bg}; }}",
        f".ttl, .nt, .lane-h, .col-h, .tx-bold {{ fill: {base.ink}; }}",
        f".sub, .lane-n, .grp-c, .tx-note, .tx-small {{ fill: {base.muted}; }}",
        f".nb, .tx, .tx-mono, .lg {{ fill: {base.body}; }}",
        f".lb {{ stroke: {base.bg}; }} .lb.on-lane {{ stroke: {base.lane}; }}",
        f".lane-a {{ fill: {base.lane}; stroke: {base.hair}; }}",
        f".lane-b {{ fill: {base.bg}; stroke: {base.hair}; }}",
        f".rule {{ stroke: {base.hair}; }}",
        f".grp {{ fill: {base.bg}; stroke: {base.group}; }} .col-u {{ stroke: {base.group}; }}",
    ]


def _node_css(kind: str, tone: Tone) -> list[str]:
    fold = _mix(tone.fill, tone.stroke, 0.2)
    return [
        f".n-{kind} .sh {{ fill: {tone.fill}; stroke: {tone.stroke}; }}",
        f".n-{kind} .fold {{ fill: {fold}; stroke: {tone.stroke}; }}",
        f".n-{kind} .tag, .k-{kind} {{ fill: {tone.accent}; }}",
        f".g-{kind} {{ stroke: {tone.stroke}; }}",
    ]


def _edge_css(kind: str, dark: bool) -> list[str]:
    style = EDGE_KINDS[kind]
    line, text = (style.dark, style.text_dark) if dark else (style.light, style.text_light)
    return [
        f".e-{kind} {{ stroke: {line}; }} .ah-{kind} {{ fill: {line}; }}",
        f".lb-{kind} {{ fill: {text}; }}",
    ]


def _mode_css(dark: bool, nodes: Iterable[str], edges: Iterable[str]) -> list[str]:
    rules = _base_css(BASE[dark])
    for kind in nodes:
        rules += _node_css(kind, NODE_KINDS[kind].dark if dark else NODE_KINDS[kind].light)
    for kind in edges:
        rules += _edge_css(kind, dark)
    return rules


def _mix(a: str, b: str, t: float) -> str:
    """The color t of the way from a to b (#rrggbb)."""
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb, strict=True))


def _style(diagram: Diagram) -> str:
    nodes = _used_node_kinds(diagram)
    edges = _used_edge_kinds(diagram)
    light = _static_css(edges) + _mode_css(False, nodes, edges)
    dark = "\n".join(f"  {rule}" for rule in _mode_css(True, nodes, edges))
    return "\n".join(light) + f"\n{DARK_QUERY} {{\n{dark}\n}}\n"


def _head(diagram: Diagram) -> list[str]:
    w, h = _num(diagram.width), _num(diagram.height)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{_esc(diagram.title)}</title>',
        f'<desc id="desc">{_esc(diagram.description or diagram.subtitle)}</desc>',
        f"<style>\n{_style(diagram)}</style>",
        "<defs>" + "".join(_marker(k) for k in _used_edge_kinds(diagram)) + "</defs>",
        f'<rect class="bg" width="{w}" height="{h}"/>',
        _text((MARGIN, 48), diagram.title, "ttl"),
    ]
    if diagram.subtitle:
        parts.append(_text((MARGIN, 72), diagram.subtitle, "sub"))
    return parts


def _body(diagram: Diagram) -> Iterator[str]:
    yield from (_lane_svg(lane, i, diagram) for i, lane in enumerate(diagram.of(Lane)))
    yield _dividers(diagram.of(Column))
    yield from (_column_svg(c) for c in diagram.of(Column))
    yield from (_group_svg(g) for g in diagram.of(Group))
    yield from (_edge_svg(e) for e in diagram.of(Edge))
    yield from (_node_svg(n) for n in diagram.of(Node))
    yield from (_free_text_svg(t) for t in diagram.of(Text))
    yield from (_label_svg(e, _halo(diagram, e)) for e in diagram.of(Edge))
    yield _legend_svg(diagram)


def _svg(diagram: Diagram) -> str:
    parts = [*_head(diagram), *_body(diagram), "</svg>"]
    return "\n".join(p for p in parts if p) + "\n"


# --- checks -------------------------------------------------------------------------------------


def _name(element: Node | Edge) -> str:
    if isinstance(element, Node):
        text = element.title or element.tag or next(iter(_lines(element.lines)), "")
        return f"node {text!r}" if text else f"{element.shape} at {_pt((element.x, element.y))}"
    label = " ".join(_lines(element.label))
    start = _pt(element.points[0]) if element.points else "?"
    return f"edge {label!r}" if label else f"{element.kind} edge from {start}"


def _text_name(text: Text) -> str:
    return f"text {next(iter(_lines(text.lines)), '')!r}"


def _headings(diagram: Diagram) -> list[tuple[str, Bounds]]:
    """The boxes of the figure's title and subtitle."""
    items = [
        ("the title", diagram.title, "ttl", 48.0),
        ("the subtitle", diagram.subtitle, "sub", 72.0),
    ]
    return [
        (name, (MARGIN, y - 15, MARGIN + text_width(text, FONTS[cls]), y + 4))
        for name, text, cls, y in items
        if text
    ]


def _check_grid(diagram: Diagram) -> list[str]:
    return [
        f"{_name(n)} is off the {GRID} px grid ({_pt((n.x, n.y))}, {_pt((n.w, n.h))})"
        for n in diagram.of(Node)
        if any(v % GRID for v in (n.x, n.y, n.w, n.h))
    ]


def _placed(diagram: Diagram) -> list[tuple[str, Bounds]]:
    """Everything with a box, by name: nodes, groups, lanes, labels, free text, the legend."""
    items = [(_name(n), n.bounds) for n in diagram.of(Node)]
    items += [(f"group {g.caption!r}", g.bounds) for g in diagram.of(Group)]
    items += [(f"lane {lane.label!r}", _lane_bounds(lane, diagram)) for lane in diagram.of(Lane)]
    items += [(f"label of {_name(e)}", b) for e in diagram.of(Edge) if (b := _label_bounds(e))]
    items += [(_text_name(t), _free_text_bounds(t)) for t in diagram.of(Text)]
    items += _headings(diagram)
    legend = _legend_bounds(diagram)
    return [*items, ("the legend", legend)] if legend else items


def _check_canvas(diagram: Diagram) -> list[str]:
    canvas = (0.0, 0.0, diagram.width, diagram.height)
    return [
        f"{name} reaches outside the canvas"
        for name, box in _placed(diagram)
        if not (_inside(box[:2], canvas) and _inside(box[2:], canvas))
    ]


def _check_overlaps(diagram: Diagram) -> list[str]:
    boxes = [(_name(n), n.bounds) for n in diagram.of(Node)]
    boxes += [(_text_name(t), _free_text_bounds(t)) for t in diagram.of(Text)]
    boxes += _headings(diagram)
    return [f"{a} overlaps {b}" for (a, ba), (b, bb) in combinations(boxes, 2) if _hits(ba, bb)]


def _check_legend(diagram: Diagram) -> list[str]:
    legend = _legend_bounds(diagram)
    if legend is None:
        return []
    return [
        f"the legend overlaps {name}"
        for name, box in _placed(diagram)
        if name != "the legend" and _hits(legend, box)
    ]


def _row_room(node: Node, row: _Row, baseline: float) -> float:
    """The width free for a row of text in the node at that baseline."""
    size = FONTS[row.cls].size
    dy = abs(baseline - BASELINE * size - node.cy) + size / 2
    if node.shape == "diamond":
        return node.w * (1 - 2 * dy / node.h) - 12
    if node.shape == "pill":
        return node.w - 2 * (PAD_X + _arc_depth(node.h / 2, node.h / 2, dy))
    return node.w - 2 * PAD_X


def _check_node_text(diagram: Diagram) -> list[str]:
    warnings = []
    for node in diagram.of(Node):
        for row, baseline in _layout(node):
            width, room = text_width(row.text, FONTS[row.cls]), _row_room(node, row, baseline)
            if width > room:
                warnings.append(
                    f"{_name(node)}: {row.text!r} is about {width:.0f} px wide, room {room:.0f} px"
                )
        _, y0, _, y1 = _text_area(node)
        if sum(r.height for r in _rows(node)) > y1 - y0 - 2 * PAD_Y:
            warnings.append(f"{_name(node)}: the text is taller than the node")
    return warnings


def _segments_of(edge: Edge) -> list[Bounds]:
    return [_seg_bounds(a, b) for a, b in pairwise(edge.points)]


def _crosses(edge: Edge, node: Node) -> bool:
    """Whether the edge runs through the node; legs that end on the node itself are let be."""
    legs = list(pairwise(edge.points))
    near = _shrink(node.bounds, -1)
    inner = _shrink(node.bounds, 2)
    for index, (a, b) in enumerate(legs):
        own = (index == 0 and _inside(a, near)) or (index == len(legs) - 1 and _inside(b, near))
        if not own and _hits(_seg_bounds(a, b), inner):
            return True
    return False


def _edge_faults(edge: Edge) -> list[str]:
    faults = []
    if any(a[0] != b[0] and a[1] != b[1] for a, b in pairwise(edge.points)):
        faults.append(f"{_name(edge)} has a diagonal leg")
    if edge.arrow in ("end", "both") and _dist(*edge.points[-2:]) < 2 * CORNER + 8:
        faults.append(f"{_name(edge)}: its last leg is too short for the arrowhead")
    if edge.arrow in ("start", "both") and _dist(*edge.points[:2]) < 2 * CORNER + 8:
        faults.append(f"{_name(edge)}: its first leg is too short for the arrowhead")
    return faults


def _check_edges(diagram: Diagram) -> list[str]:
    warnings = []
    nodes = diagram.of(Node)
    for edge in diagram.of(Edge):
        warnings += [f"{_name(edge)} runs through {_name(n)}" for n in nodes if _crosses(edge, n)]
        warnings += _edge_faults(edge)
    return warnings


def _outlines(diagram: Diagram) -> list[tuple[str, Bounds]]:
    """Lines that labels must not sit on: lane borders and group outlines."""
    lines = []
    for lane in diagram.of(Lane):
        x0, y0, x1, y1 = _lane_bounds(lane, diagram)
        lines += [(f"lane {lane.label!r}", (x0, y, x1, y)) for y in (y0, y1)]
    for group in diagram.of(Group):
        x0, y0, x1, y1 = group.bounds
        sides = [(x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)]
        lines += [(f"group {group.caption!r}", side) for side in sides]
    return lines


def _on_line(box: Bounds, edge: Edge) -> bool:
    return any(_hits(box, seg) for seg in _segments_of(edge))


def _label_clashes(diagram: Diagram, edge: Edge, box: Bounds) -> list[str]:
    own = _name(edge)
    covered = [(_name(n), n.bounds) for n in diagram.of(Node)]
    covered += [(_text_name(t), _free_text_bounds(t)) for t in diagram.of(Text)]
    clashes = [f"the label of {own} covers {name}" for name, b in covered if _hits(box, b)]
    clashes += [
        f"the label of {own} sits on the line of {_name(other)}"
        for other in diagram.of(Edge)
        if (other is not edge or edge.at is None) and _on_line(box, other)
    ]
    clashes += [
        f"the label of {own} sits on the outline of {name}"
        for name, line in _outlines(diagram)
        if _hits(box, line)
    ]
    return clashes


def _check_texts(diagram: Diagram) -> list[str]:
    return [
        f"{_text_name(text)} sits on the line of {_name(edge)}"
        for text in diagram.of(Text)
        for edge in diagram.of(Edge)
        if _on_line(_free_text_bounds(text), edge)
    ]


def _check_labels(diagram: Diagram) -> list[str]:
    placed = [(e, b) for e in diagram.of(Edge) if (b := _label_bounds(e))]
    warnings = [w for edge, box in placed for w in _label_clashes(diagram, edge, box)]
    warnings += [
        f"the labels of {_name(a)} and {_name(b)} overlap"
        for (a, ba), (b, bb) in combinations(placed, 2)
        if _hits(ba, bb)
    ]
    return warnings


def _check_heads(diagram: Diagram) -> list[str]:
    warnings = []
    for lane in diagram.of(Lane):
        texts = [(lane.label, FONTS["lane-h"]), *((n, FONTS["lane-n"]) for n in _lines(lane.note))]
        widest = max(text_width(text, font) for text, font in texts)
        if widest > lane.head - 24:
            warnings.append(f"lane {lane.label!r}: its head text needs {widest:.0f} px")
    for column in diagram.of(Column):
        widest = max(
            text_width(column.label, FONTS["col-h"]), text_width(column.note, FONTS["lane-n"])
        )
        if widest > column.w - 16:
            warnings.append(f"column {column.label!r}: its header needs {widest:.0f} px")
    return warnings


_RULES = (
    _check_grid,
    _check_canvas,
    _check_overlaps,
    _check_legend,
    _check_node_text,
    _check_edges,
    _check_labels,
    _check_texts,
    _check_heads,
)


# --- figure scripts -----------------------------------------------------------------------------


def save(diagram: Diagram, script: str | Path) -> Path:
    """Render `<script's stem>.svg` beside the figure script and print the check's warnings."""
    path = diagram.render(Path(script).resolve().with_suffix(".svg"))
    warnings = diagram.check()
    for warning in warnings:
        print(f"{path.name}: warning: {warning}")
    print(f"{path.name}: written, {len(warnings)} warning(s)")
    return path


def figure_scripts() -> list[Path]:
    """Every figure script: docs/reference/<chapter>/*.py, chapters starting with _ left out."""
    return sorted(
        path
        for path in KIT.parent.glob("*/*.py")
        if not path.parent.name.startswith(("_", ".")) and path.resolve() != KIT
    )


def render_scripts(scripts: Sequence[Path]) -> int:
    """Run each figure script (all of them when none are given); 1 if any failed."""
    scripts = list(scripts) or figure_scripts()
    if not scripts:
        print(f"no figure scripts in {KIT.parent}/<chapter>/")
    failed = []
    for script in scripts:
        result = subprocess.run([sys.executable, str(script)], check=False)
        if result.returncode:
            failed.append(script)
    for script in failed:
        print(f"failed: {script}", file=sys.stderr)
    return 1 if failed else 0


# --- previews -----------------------------------------------------------------------------------


def find_browser() -> str:
    """The headless browser: $BROWSER_BIN, Edge's usual place, or Edge or Chrome on the PATH."""
    if configured := os.environ.get("BROWSER_BIN"):
        return configured
    if EDGE_BROWSER.exists():
        return str(EDGE_BROWSER)
    for name in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        if found := shutil.which(name):
            return found
    raise SystemExit("no Edge or Chrome found; set BROWSER_BIN to the browser's executable")


def themed(svg: str, mode: Literal["light", "dark"]) -> str:
    """The SVG pinned to one mode: the dark block removed, or made unconditional."""
    if mode == "dark":
        return svg.replace(DARK_QUERY, "@media all")
    while (start := svg.find(DARK_QUERY)) >= 0:
        end = _closing(svg, svg.index("{", start))
        svg = svg[:start] + svg[end + 1 :]
    return svg


def _closing(text: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return index
    raise ValueError("unbalanced braces in the SVG's style")


def svg_size(svg: str) -> tuple[int, int]:
    """The SVG's width and height in px, from its root element."""
    root = re.search(r"<svg\b[^>]*>", svg)
    tag = root.group(0) if root else ""
    width = re.search(r'\swidth="([\d.]+)', tag)
    height = re.search(r'\sheight="([\d.]+)', tag)
    if width and height:
        return math.ceil(float(width.group(1))), math.ceil(float(height.group(1)))
    box = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', tag)
    if box:
        return math.ceil(float(box.group(1))), math.ceil(float(box.group(2)))
    raise ValueError("the SVG has neither width and height nor a viewBox")


def cropped(svg: str, box: Bounds) -> str:
    """The SVG cut down to the box (x, y, width, height), for a close look at a detail."""
    x, y, w, h = box
    root = re.search(r"<svg\b[^>]*>", svg)
    if root is None:
        raise ValueError("not an SVG")
    tag = re.sub(r'\s(?:width|height|viewBox)="[^"]*"', "", root.group(0))
    frame = f'<svg width="{_num(w)}" height="{_num(h)}" viewBox="{_pt((x, y))} {_pt((w, h))}"'
    return svg[: root.start()] + tag.replace("<svg", frame, 1) + svg[root.end() :]


@dataclass(frozen=True)
class _Camera:
    browser: str
    out: Path
    scratch: Path
    scale: float
    crop: Bounds | None


def _shoot(camera: _Camera, page: Path, png: Path, size: tuple[int, int]) -> bool:
    command = [
        camera.browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        f"--user-data-dir={camera.scratch / 'profile'}",
        f"--force-device-scale-factor={_num(camera.scale)}",
        f"--window-size={size[0]},{size[1]}",
        f"--screenshot={png}",
        page.as_uri(),
    ]
    png.unlink(missing_ok=True)
    result = subprocess.run(
        command, capture_output=True, text=True, errors="replace", timeout=180, check=False
    )
    if png.exists():
        return True
    print(f"{page.name}: no screenshot\n{result.stderr.strip()}", file=sys.stderr)
    return False


def _preview_one(camera: _Camera, svg: Path) -> int:
    """Shoot one SVG in both modes; the number of failed shots."""
    source = svg.read_text(encoding="utf-8")
    if camera.crop is not None:
        source = cropped(source, camera.crop)
    size = svg_size(source)
    failures = 0
    for mode in ("light", "dark"):
        page = camera.scratch / f"{svg.stem}-{mode}.svg"
        page.write_text(themed(source, mode), encoding="utf-8")
        png = camera.out / f"{svg.stem}-{mode}.png"
        if _shoot(camera, page, png, size):
            print(png)
        else:
            failures += 1
    return failures


def preview(svgs: Sequence[Path], out: Path, scale: float = 1.0, crop: Bounds | None = None) -> int:
    """Light and dark PNGs of each SVG in `out`, optionally of a cropped part; 1 on failure."""
    browser = find_browser()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="diagram-kit-") as scratch:
        camera = _Camera(browser, out, Path(scratch), scale, crop)
        failures = sum(_preview_one(camera, Path(svg).resolve()) for svg in svgs)
    return 1 if failures else 0


def _box(text: str) -> Bounds:
    values = [float(v) for v in text.split(",")]
    if len(values) != 4:
        raise argparse.ArgumentTypeError("expected X,Y,WIDTH,HEIGHT")
    return (values[0], values[1], values[2], values[3])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="diagram_kit", description=SUMMARY)
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="run figure scripts, writing their SVGs")
    render.add_argument("scripts", nargs="*", type=Path, help="default: every figure script")
    shots = commands.add_parser("preview", help="light and dark PNGs of SVGs, for review")
    shots.add_argument("svgs", nargs="+", type=Path)
    shots.add_argument(
        "--out",
        type=Path,
        default=Path(tempfile.gettempdir()),
        help="folder for <stem>-light.png and <stem>-dark.png (default: the temp folder)",
    )
    shots.add_argument("--scale", type=float, default=1.0, help="device pixels per px")
    shots.add_argument("--crop", type=_box, help="only the part X,Y,WIDTH,HEIGHT")
    args = parser.parse_args(argv)
    if args.command == "render":
        return render_scripts(args.scripts)
    return preview(args.svgs, args.out, args.scale, args.crop)


if __name__ == "__main__":
    sys.exit(main())
