"""Draw the flow diagrams in this folder as SVG: `uv run python docs/diagrams/draw.py`.

Every position is set by hand, so the layout stays left to right and no two edges cross;
a layout engine would decide that on its own. Each diagram is one function below.
"""

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

HERE = Path(__file__).parent

STYLE = """
.bg { fill: #ffffff; }
.title { font: 600 22px Helvetica, Arial, sans-serif; fill: #1d1f24; }
.subtitle { font: 14px Helvetica, Arial, sans-serif; fill: #5b606b; }
.node rect, .node polygon { stroke-width: 1.6; }
.node .t { font: 700 15px Helvetica, Arial, sans-serif; fill: #1d1f24; }
.node .s { font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 0.06em; }
.node .l { font: 12.5px Helvetica, Arial, sans-serif; fill: #30333a; }
.agent rect, .agent polygon, .agent circle { fill: #eaf2fb; stroke: #2f6db5; }
.agent .s { fill: #2f6db5; }
.human rect, .human polygon, .human circle { fill: #fff3dc; stroke: #c27400; }
.human .s { fill: #a86400; }
.disp rect, .disp polygon, .disp circle { fill: #f0f1f3; stroke: #6b6f7a; }
.disp .s { fill: #5b606b; }
.ask rect, .ask polygon, .ask circle { fill: #f3edfb; stroke: #7a4fb5; }
.ask .s { fill: #7a4fb5; }
.stall rect, .stall polygon, .stall circle { fill: #fcebeb; stroke: #b53a3a; }
.stall .s { fill: #b53a3a; }
.back rect, .back polygon, .back circle { fill: #fdf0e6; stroke: #d0661a; }
.back .s { fill: #b5560f; }
.end rect { fill: #ffffff; stroke: #8a8f99; stroke-dasharray: 5 3; }
.code rect, .code polygon, .code circle { fill: #e8f5f0; stroke: #2a8a6e; }
.code .s { fill: #22775e; }
.quiet rect { fill: #f7f8fa; stroke: #a3a8b2; } .quiet .s { fill: #6b6f7a; }
.lane { fill: #f7f8fa; stroke: #dfe2e7; }
.lane-alt { fill: #ffffff; stroke: #dfe2e7; }
.lane-head { font: 700 13.5px Helvetica, Arial, sans-serif; fill: #1d1f24; }
.lane-note { font: 12px Helvetica, Arial, sans-serif; fill: #5b606b; }
.e { fill: none; stroke-width: 1.8; }
.e-flow { stroke: #3a3d44; }
.e-back { stroke: #d0661a; }
.e-ask { stroke: #7a4fb5; stroke-dasharray: 6 4; }
.e-stall { stroke: #b53a3a; stroke-dasharray: 6 4; }
.lbl { font: 12px Helvetica, Arial, sans-serif; paint-order: stroke; stroke: #ffffff;
       stroke-width: 5px; stroke-linejoin: round; }
.lbl-flow { fill: #1d1f24; } .lbl-back { fill: #a84f0e; }
.lbl-ask { fill: #6a3fa5; } .lbl-stall { fill: #a32f2f; }
.note { font: 12.5px Helvetica, Arial, sans-serif; fill: #4a4e57; }
.note-b { font: 700 12.5px Helvetica, Arial, sans-serif; fill: #1d1f24; }
.mono { font-family: Menlo, Consolas, monospace; }
.trunk { stroke: #3a3d44; } .twig { stroke: #8a8f99; }
.pr-draft { fill: #f7f8fa; stroke: #a3a8b2; } .pr-ready { fill: #fff3dc; stroke: #c27400; }
.band-main { fill: #e7e9ed; } .band-ticket { fill: #dbe8f7; }
.m-flow { fill: #3a3d44; } .m-back { fill: #d0661a; } .m-ask { fill: #7a4fb5; }
.m-stall { fill: #b53a3a; }
@media (prefers-color-scheme: dark) {
  .bg { fill: #0f141a; }
  .title, .node .t, .lane-head, .note-b { fill: #e6edf3; }
  .subtitle, .lane-note { fill: #9da7b3; }
  .node .l, .note { fill: #c9d1d9; }
  .agent rect, .agent polygon, .agent circle { fill: #132a45; stroke: #5b9be6; }
  .agent .s { fill: #7fb2f0; }
  .human rect, .human polygon, .human circle { fill: #3a2a0e; stroke: #e0a33a; }
  .human .s { fill: #f0b85a; }
  .disp rect, .disp polygon, .disp circle { fill: #23282f; stroke: #8b939e; }
  .disp .s { fill: #a8b0bb; }
  .ask rect, .ask polygon, .ask circle { fill: #2a1f40; stroke: #a98be0; }
  .ask .s { fill: #c0a8f0; }
  .stall rect, .stall polygon, .stall circle { fill: #3d1a1c; stroke: #e06c6c; }
  .stall .s { fill: #f08a8a; }
  .back rect, .back polygon, .back circle { fill: #3d2414; stroke: #ef8a3c; }
  .back .s { fill: #f5a466; }
  .code rect, .code polygon, .code circle { fill: #10322a; stroke: #3fb68f; }
  .code .s { fill: #6fd0ad; }
  .quiet rect { fill: #181e26; stroke: #6b7380; } .quiet .s { fill: #9da7b3; }
  .end rect { fill: #0f141a; stroke: #8b939e; }
  .lane { fill: #151b23; stroke: #2a313b; } .lane-alt { fill: #0f141a; stroke: #2a313b; }
  .e-flow { stroke: #c9d1d9; } .e-back { stroke: #ef8a3c; }
  .e-ask { stroke: #a98be0; } .e-stall { stroke: #e06c6c; }
  .m-flow { fill: #c9d1d9; } .m-back { fill: #ef8a3c; } .m-ask { fill: #a98be0; }
  .m-stall { fill: #e06c6c; }
  .lbl { stroke: #0f141a; }
  .lbl-flow { fill: #e6edf3; } .lbl-back { fill: #f5a466; }
  .lbl-ask { fill: #c0a8f0; } .lbl-stall { fill: #f08a8a; }
  .trunk { stroke: #c9d1d9; } .twig { stroke: #6b7380; }
  .pr-draft { fill: #181e26; stroke: #6b7380; } .pr-ready { fill: #3a2a0e; stroke: #e0a33a; }
  .band-main { fill: #23282f; } .band-ticket { fill: #132a45; }
}
"""

EDGE_KINDS = ("flow", "back", "ask", "stall")  # each has .e-<kind>, .m-<kind> and .lbl-<kind>


@dataclass
class Node:
    """A box: kind picks the colour, title and tag head it, lines say what happens."""

    x: float
    y: float
    w: float
    h: float
    kind: str
    title: str
    tag: str = ""
    lines: tuple[str, ...] = ()
    shape: str = "box"  # box, pill or diamond

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


@dataclass
class Edge:
    """An orthogonal path through points; the label sits at `at`, centred unless `align`."""

    points: list[tuple[float, float]]
    kind: str = "flow"
    label: tuple[str, ...] = ()
    at: tuple[float, float] = (0, 0)
    align: str = "middle"


@dataclass
class Diagram:
    width: float
    height: float
    title: str
    subtitle: str
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)  # raw SVG drawn below the edges


def rounded(points: list[tuple[float, float]], radius: float = 10) -> str:
    """An SVG path through the points with rounded corners."""
    if len(points) < 3:
        return "M " + " L ".join(f"{x:g} {y:g}" for x, y in points)
    parts = [f"M {points[0][0]:g} {points[0][1]:g}"]
    for (ax, ay), (bx, by), (cx, cy) in zip(points, points[1:], points[2:], strict=False):
        r = min(radius, _dist(ax, ay, bx, by) / 2, _dist(bx, by, cx, cy) / 2)
        sx, sy = _towards(bx, by, ax, ay, r)
        ex, ey = _towards(bx, by, cx, cy, r)
        parts.append(f"L {sx:g} {sy:g} Q {bx:g} {by:g} {ex:g} {ey:g}")
    parts.append(f"L {points[-1][0]:g} {points[-1][1]:g}")
    return " ".join(parts)


def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return float(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5)


def _towards(fx: float, fy: float, tx: float, ty: float, r: float) -> tuple[float, float]:
    d = _dist(fx, fy, tx, ty) or 1
    return fx + (tx - fx) * r / d, fy + (ty - fy) * r / d


def text_block(x: float, y: float, lines: tuple[str, ...], cls: str, anchor: str = "middle") -> str:
    """Lines of text whose last baseline is at y, growing upwards."""
    step = 15
    top = y - step * (len(lines) - 1)
    spans = "".join(
        f'<tspan x="{x:g}" y="{top + i * step:g}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return f'<text class="{cls}" text-anchor="{anchor}">{spans}</text>'


def render_node(node: Node) -> str:
    out = [f'<g class="node {node.kind}">']
    if node.shape == "diamond":
        cx, cy = node.cx, node.cy
        pts = f"{cx},{node.y} {node.right},{cy} {cx},{node.bottom} {node.x},{cy}"
        out.append(f'<polygon points="{pts}"/>')
    else:
        radius = node.h / 2 if node.shape == "pill" else 10
        out.append(
            f'<rect x="{node.x:g}" y="{node.y:g}" width="{node.w:g}" height="{node.h:g}" '
            f'rx="{radius:g}"/>'
        )
    body = _node_text(node)
    out.extend(body)
    out.append("</g>")
    return "".join(out)


def _node_text(node: Node) -> list[str]:
    """Title, tag and lines, centred as a block in the node."""
    rows: list[tuple[str, str, float]] = []  # (class, text, height)
    if node.title:
        rows.append(("t", node.title, 19))
    if node.tag:
        rows.append(("s", node.tag.upper(), 17))
    if node.lines:
        rows.append(("gap", "", 5))
        rows.extend(("l", line, 16) for line in node.lines)
    total = sum(h for _, _, h in rows)
    y = node.cy - total / 2
    out = []
    for cls, value, h in rows:
        y += h
        if cls != "gap":
            out.append(
                f'<text class="{cls}" x="{node.cx:g}" y="{y - 4:g}" '
                f'text-anchor="middle">{escape(value)}</text>'
            )
    return out


def render_edge(edge: Edge) -> str:
    path = rounded(edge.points)
    return f'<path class="e e-{edge.kind}" d="{path}" marker-end="url(#a-{edge.kind})"/>'


def render_label(edge: Edge) -> str:
    if not edge.label:
        return ""
    x, y = edge.at
    return text_block(x, y, edge.label, f"lbl lbl-{edge.kind}", edge.align)


def markers() -> str:
    out = []
    for kind in EDGE_KINDS:
        out.append(
            f'<marker id="a-{kind}" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="9" '
            f'markerHeight="9" orient="auto-start-reverse"><path class="m-{kind}" '
            f'd="M0,0 L10,5 L0,10 z"/></marker>'
        )
    return "".join(out)


def render(diagram: Diagram) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{diagram.width:g}" '
        f'height="{diagram.height:g}" viewBox="0 0 {diagram.width:g} {diagram.height:g}" '
        f'font-family="Helvetica, Arial, sans-serif">',
        f"<title>{escape(diagram.title)}</title>",
        f"<style>{STYLE}</style><defs>{markers()}</defs>",
        f'<rect class="bg" width="{diagram.width:g}" height="{diagram.height:g}"/>',
        f'<text class="title" x="40" y="46">{escape(diagram.title)}</text>',
        f'<text class="subtitle" x="40" y="70">{escape(diagram.subtitle)}</text>',
    ]
    parts.extend(diagram.extra)
    parts.extend(render_edge(e) for e in diagram.edges)
    parts.extend(render_node(n) for n in diagram.nodes)
    parts.extend(render_label(e) for e in diagram.edges)
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def legend(x: float, y: float, items: list[tuple[str, str]]) -> list[str]:
    """Swatches for node kinds (`node:<kind>`) and edge kinds (`edge:<kind>`) in one row."""
    out = []
    for key, text in items:
        what, kind = key.split(":")
        if what == "node":
            out.append(
                f'<g class="node {kind}"><rect x="{x:g}" y="{y - 12:g}" width="26" height="16" '
                f'rx="4"/></g>'
            )
        else:
            out.append(
                f'<path class="e e-{kind}" d="M {x:g} {y - 4:g} L {x + 26:g} {y - 4:g}" '
                f'marker-end="url(#a-{kind})"/>'
            )
        out.append(f'<text class="note" x="{x + 34:g}" y="{y:g}">{escape(text)}</text>')
        x += 46 + 7 * len(text)
    return out


# --- edge helpers -----------------------------------------------------------------------------


def right(a: Node, b: Node, label: tuple[str, ...] = (), kind: str = "flow") -> Edge:
    """From a's right side to b's left side; one bend in the middle when their rows differ."""
    if abs(a.cy - b.cy) < 1:
        return Edge([(a.right, a.cy), (b.x, b.cy)], kind, label, ((a.right + b.x) / 2, a.cy - 9))
    vx = (a.right + b.x) / 2
    points = [(a.right, a.cy), (vx, a.cy), (vx, b.cy), (b.x, b.cy)]
    return Edge(points, kind, label, (vx, (a.cy + b.cy) / 2 + 4))


def down(a: Node, b: Node, label: tuple[str, ...] = (), kind: str = "flow") -> Edge:
    """From a's bottom straight down to b's top; the label sits right of the line."""
    return Edge(
        [(a.cx, a.bottom), (a.cx, b.y)], kind, label, (a.cx + 9, (a.bottom + b.y) / 2 + 4), "start"
    )


def up(a: Node, b: Node, label: tuple[str, ...] = (), kind: str = "flow") -> Edge:
    """From a's top straight up to b's bottom; the label sits right of the line."""
    return Edge(
        [(a.cx, a.y), (a.cx, b.bottom)], kind, label, (a.cx + 9, (a.y + b.bottom) / 2 + 4), "start"
    )


def into(a: Node, b: Node, y: float, label: tuple[str, ...] = (), kind: str = "flow") -> Edge:
    """From a's right side at height y straight into b's left side; for tall targets."""
    return Edge([(a.right, y), (b.x, y)], kind, label, ((a.right + b.x) / 2, y - 9))


def stub(a: Node, b: Node, bus: float, label: str) -> Edge:
    """From a's bottom down a bus at x = bus, then right into b: one of several outputs."""
    points = [(bus, a.bottom), (bus, b.cy), (b.x, b.cy)]
    return Edge(points, "flow", (label,), (bus + 10, b.cy - 8), "start")


def arrive(x: float, node: Node, label: tuple[str, ...]) -> Edge:
    """The trigger that starts a diagram, entering node from the left edge at x."""
    return Edge([(x, node.cy), (node.x, node.cy)], "flow", label, ((x + node.x) / 2, node.cy - 10))


def box(x: float, y: float, kind: str, text: tuple[str, str], lines: tuple[str, ...]) -> Node:
    """A 190 x 128 box: text is (title, tag)."""
    return Node(x, y, 190, 128, kind, text[0], text[1], lines)


def diamond(x: float, cy: float, lines: tuple[str, ...], kind: str = "code") -> Node:
    return Node(x, cy - 55, 140, 110, kind, "", "", lines, "diamond")


def outcome(x: float, cy: float, kind: str, title: str, lines: tuple[str, ...]) -> Node:
    """A small result box centred on cy."""
    return Node(x, cy - 36, 190, 72, kind, title, "", lines)


# --- 01: the stages of one story --------------------------------------------------------------


def stages() -> Diagram:
    bw, bh, gap, top = 176.0, 132.0, 116.0, 160.0
    d = Diagram(
        2540,
        640,
        "01 · One story through the stages",
        "Boxes: what happens in the stage. Arrows: what moves the story on. "
        "Every move is one edit of the stage field, committed and pushed.",
    )
    drafts = Node(
        40,
        top,
        140,
        bh,
        "human",
        "drafts/",
        "human",
        ("Story written", "from TICKET.md;", "the pipeline", "ignores it"),
    )
    spec = [
        (
            "ready",
            "intake",
            ("Opens the branch", "and a draft PR;", "checks the story", "is buildable"),
        ),
        ("tests", "tester", ("One test per", "acceptance", "criterion, red", "on purpose")),
        ("doing", "coder", ("Makes the tests", "pass, refactors", "once, make check", "green")),
        (
            "review",
            "reviewer",
            ("Reads the diff", "against criteria,", "architecture and", "security"),
        ),
        (
            "docs",
            "documenter",
            ("Writes what the", "reader needs into", "README and docs/;", "fixes stale prose"),
        ),
        (
            "demo",
            "demo",
            ("Runs the demo", "commands, judges", "the output, writes", "the PR body"),
        ),
        ("accept", "human", ("Reads the PR,", "wherever they are;", "then merges or", "closes it")),
    ]
    boxes: dict[str, Node] = {}
    x = drafts.right + gap
    for name, who, lines in spec:
        boxes[name] = Node(x, top, bw, bh, "human" if who == "human" else "agent", name, who, lines)
        x += bw + gap
    done = Node(
        x,
        top,
        150,
        bh,
        "disp",
        "done",
        "dispatcher",
        ("Story moved to", "done/ on main,", "branch deleted,", "cost logged"),
    )
    feature = Node(
        done.cx - 95, 372, 190, 64, "agent", "feature acceptance", "", ("acceptor, see 05",)
    )
    d.nodes = [drafts, *boxes.values(), done, feature]
    d.edges.append(down(done, feature, ("the feature's", "last story"), "flow"))
    forward = [
        (drafts, "ready", ("human moves it", "into ongoing/")),
        ("ready", "tests", ("story is", "complete")),
        ("tests", "doing", ("tests", "committed")),
        ("doing", "review", ("make check", "green")),
        ("review", "docs", ("verdict:", "pass")),
        ("docs", "demo", ("docs written,", "no findings")),
        ("demo", "accept", ("all as expected,", "PR marked ready")),
        ("accept", done, ("human merges", "the PR")),
    ]
    for a, b, label in forward:
        src = boxes[a] if isinstance(a, str) else a
        dst = boxes[b] if isinstance(b, str) else b
        d.edges.append(right(src, dst, label))

    doing = boxes["doing"]
    back = [
        ("review", 0.82, "verdict: rework"),
        ("docs", 0.62, "docs and code disagree"),
        ("demo", 0.42, "output differs from Expect"),
        ("accept", 0.22, "human closes the PR"),
    ]
    for depth, (name, at, label) in enumerate(back, start=1):
        src = boxes[name]
        level = top + bh + 22 + 44 * depth
        tx = doing.x + doing.w * at
        d.edges.append(
            Edge(
                [(src.cx, src.bottom), (src.cx, level), (tx, level), (tx, doing.bottom)],
                "back",
                (f"{label} · round + 1",),
                ((doing.right + src.cx) / 2, level - 7),
            )
        )
    tests = boxes["tests"]
    arc = top - 46
    d.edges.append(
        Edge(
            [
                (doing.x + 0.3 * bw, top),
                (doing.x + 0.3 * bw, arc),
                (tests.x + 0.7 * bw, arc),
                (tests.x + 0.7 * bw, top),
            ],
            "back",
            ("human approved a test change",),
            ((tests.right + doing.x) / 2, arc - 8),
        )
    )
    ready, demo = boxes["ready"], boxes["demo"]
    floor = top + bh + 22 + 44 * 5 + 6
    d.extra.append(
        f'<path d="M {ready.x:g} {floor - 12:g} L {ready.x:g} {floor:g} L {demo.right:g} '
        f'{floor:g} L {demo.right:g} {floor - 12:g}" class="e e-stall"/>'
    )
    d.edges.append(
        Edge(
            [(ready.x, floor), (drafts.cx, floor), (drafts.cx, drafts.bottom)],
            "stall",
            ("human closes the PR while ready … demo work on it: story discarded, branch deleted",),
            ((ready.x + demo.right) / 2, floor - 8),
        )
    )
    d.extra += legend(
        40,
        622,
        [
            ("node:agent", "agent stage"),
            ("node:human", "human"),
            ("node:disp", "dispatcher"),
            ("edge:flow", "moves on"),
            ("edge:back", "goes back"),
            ("edge:stall", "discarded"),
        ],
    )
    return d


# --- 02: lanes, who writes where -------------------------------------------------------------


def lanes() -> Diagram:
    head_w, row_h, bw, bh, gap = 250.0, 112.0, 164.0, 84.0, 112.0
    x0, y0 = 40.0, 110.0
    rows = [
        ("Human", "drafts/, merge or close", "lane-alt"),
        ("Pull request", "GitHub, written with gh", "lane"),
        ("tests/*", "tester", "lane-alt"),
        ("src/*, docs/openapi.json", "coder", "lane"),
        ("Story file", "ongoing/*.md: every agent", "lane-alt"),
        ("README.md, docs/*", "documenter", "lane"),
    ]
    cols = 9
    width = x0 + head_w + 30 + cols * bw + (cols - 1) * gap + 40
    d = Diagram(
        width,
        y0 + len(rows) * row_h + 110,
        "02 · Lanes: where each stage writes",
        "One row per lane from stages.yml; each stage sits in the row of what it produces. "
        "The guard hook refuses every write outside the agent's lane.",
    )
    for i, (name, who, cls) in enumerate(rows):
        y = y0 + i * row_h
        d.extra += [
            f'<rect class="{cls}" x="{x0:g}" y="{y:g}" width="{width - x0 - 40:g}" '
            f'height="{row_h:g}"/>',
            f'<text class="lane-head" x="{x0 + 16:g}" y="{y + row_h / 2 - 3:g}">'
            f"{escape(name)}</text>",
            f'<text class="lane-note" x="{x0 + 16:g}" y="{y + row_h / 2 + 15:g}">'
            f"{escape(who)}</text>",
        ]

    def at(cell: tuple[int, int], kind: str, title: str, tag: str, lines: tuple[str, ...]) -> Node:
        col, row = cell
        x = x0 + head_w + 30 + col * (bw + gap)
        y = y0 + row * row_h + (row_h - bh) / 2
        return Node(x, y, bw, bh, kind, title, tag, lines)

    steps = [
        at((0, 0), "human", "promote", "human", ("git mv drafts/", "→ ongoing/")),
        at((1, 1), "agent", "ready", "intake", ("branch, draft PR,", "frontmatter")),
        at((2, 2), "agent", "tests", "tester", ("one test per", "criterion")),
        at((3, 3), "agent", "doing", "coder", ("code that makes", "the tests pass")),
        at((4, 4), "agent", "review", "reviewer", ("findings and", "verdict in the log")),
        at((5, 5), "agent", "docs", "documenter", ("what the reader", "needs; stale fixed")),
        at((6, 1), "agent", "demo", "demo", ("PR body written,", "marked ready")),
        at((7, 0), "human", "accept", "human", ("merges the PR",)),
        at((8, 4), "disp", "done", "dispatcher", ("on main: story", "git mv to done/")),
    ]
    d.nodes = steps
    triggers = [
        "git mv",
        "complete",
        "committed",
        "green",
        "pass",
        "no findings",
        "PR ready",
        "merged",
    ]
    d.edges = [right(a, b, (t,)) for a, b, t in zip(steps, steps[1:], triggers, strict=False)]

    band_y = y0 + len(rows) * row_h + 26
    first, last = steps[1].cx, steps[7].cx
    d.extra += [
        f'<rect x="{x0 + head_w + 30:g}" y="{band_y:g}" width="{first - x0 - head_w - 30:g}" '
        f'height="26" rx="4" class="band-main"/>',
        f'<rect x="{first:g}" y="{band_y:g}" width="{last - first:g}" height="26" rx="4" '
        f'class="band-ticket"/>',
        f'<rect x="{last:g}" y="{band_y:g}" width="{steps[8].right - last:g}" height="26" '
        f'rx="4" class="band-main"/>',
        f'<text class="lane-head" x="{x0 + 16:g}" y="{band_y + 18:g}">Branch</text>',
        f'<text class="note" x="{x0 + head_w + 44:g}" y="{band_y + 18:g}">main</text>',
        f'<text class="note" x="{first + 14:g}" y="{band_y + 18:g}">ticket/&lt;stem&gt;, '
        "one per story: every stage commits code and story together and pushes; "
        "it comes back to main only through the merge</text>",
        f'<text class="note" x="{last + 14:g}" y="{band_y + 18:g}">main</text>',
        *legend(
            x0,
            band_y + 66,
            [
                ("node:agent", "agent stage"),
                ("node:human", "human"),
                ("node:disp", "dispatcher"),
                ("edge:flow", "moves on"),
            ],
        ),
    ]
    return d


# --- 03: inside one stage run ----------------------------------------------------------------


def stage_run() -> Diagram:
    d = Diagram(
        2420,
        790,
        "03 · Inside one stage run",
        "The same for every agent stage; what the agent reads and writes differs by stage. "
        "Each run starts from what is committed and carries nothing over.",
    )
    y, mid = 180.0, 244.0
    pr_open = diamond(110, mid, ("PR still", "open?"), "disp")
    gone = outcome(85, 450, "disp", "handled as closed", ("or as merged", "(01); no agent runs"))
    prep = box(
        330,
        y,
        "disp",
        ("check out", "dispatcher"),
        ("ticket branch, pull,", "merge main in; ready:", "main, or the branch", "after an answer"),
    )
    claim = box(
        600,
        y,
        "disp",
        ("run file", "dispatcher"),
        ("written before the", "agent, removed after;", "no commit"),
    )
    read = box(
        860,
        y,
        "agent",
        ("read", "agent"),
        ("the story and what", "the stage names:", "log, diff, CLAUDE.md"),
    )
    work = box(1120, y, "agent", ("work", "agent"), ("within its lane;", "commits as it goes"))
    judge = box(
        1380, y, "agent", ("check and judge", "agent"), ("make check, then", "against the criteria")
    )
    col_f, col_g, col_h = 1790.0, 2030.0, 2240.0
    adv = Node(col_f, mid - 40, 180, 80, "disp", "move on", "", ("checks green;", "commit, push"))
    rework = Node(col_f, 360, 180, 80, "back", "send back", "", ("findings in log,", "round + 1"))
    ask = Node(col_f, 510, 180, 80, "ask", "ask", "", ("question in log,", "blocked: question"))
    stall = Node(
        col_f,
        640,
        180,
        92,
        "stall",
        "stall",
        "dispatcher",
        ("attempts + 1, partial", "work committed"),
    )
    cap_rounds = Node(
        col_g - 10, 356, 140, 88, "back", "", "", ("round over", "max_rounds?"), "diamond"
    )
    waits = Node(col_g - 20, 510, 160, 80, "ask", "human", "see 04", ("answers on", "the PR"))
    cap_tries = Node(
        col_g - 10, 642, 140, 88, "stall", "", "", ("attempts at", "max_attempts?"), "diamond"
    )
    next_stage = Node(col_h, mid - 26, 150, 52, "end", "next stage", "", (), "pill")
    to_doing = Node(col_h, 374, 150, 52, "end", "doing", "", (), "pill")
    again = Node(col_h, 660, 150, 52, "end", "same stage", "", (), "pill")
    d.nodes = [
        pr_open,
        gone,
        prep,
        claim,
        read,
        work,
        judge,
        adv,
        rework,
        ask,
        stall,
        cap_rounds,
        waits,
        cap_tries,
        next_stage,
        to_doing,
        again,
    ]
    d.edges = [
        arrive(20, pr_open, ("watcher:", "run <agent>")),
        right(pr_open, prep, ("yes, or", "no PR yet")),
        down(pr_open, gone, ("closed or merged",), "stall"),
        right(prep, claim, ("on the", "branch")),
        right(claim, read),
        right(read, work),
        right(work, judge),
    ]
    bus = judge.right + 30
    d.edges += [
        Edge(
            [(judge.right, adv.cy), (adv.x, adv.cy)],
            "flow",
            ("green, criteria met",),
            (bus + 8, adv.cy - 9),
            "start",
        ),
        Edge(
            [
                (judge.right, judge.bottom - 24),
                (bus, judge.bottom - 24),
                (bus, rework.cy),
                (rework.x, rework.cy),
            ],
            "back",
            ("findings", "(review, docs, demo)"),
            (bus + 8, rework.cy - 9),
            "start",
        ),
        Edge(
            [(judge.right - 30, judge.bottom), (judge.right - 30, ask.cy), (ask.x, ask.cy)],
            "ask",
            ("unclear, contradictory,", "or a tool is missing"),
            (bus + 8, ask.cy - 9),
            "start",
        ),
        Edge(
            [(work.cx, work.bottom), (work.cx, stall.cy), (stall.x, stall.cy)],
            "stall",
            (
                "no new commit, an error, a denied tool; or its run is gone: lease over, machine "
                "restarted",
            ),
            (work.cx + 14, stall.cy - 9),
            "start",
        ),
        right(adv, next_stage, ("commit a → b, push",)),
        right(rework, cap_rounds, (), "back"),
        right(cap_rounds, to_doing, ("no",), "back"),
        down(cap_rounds, waits, ("yes",), "ask"),
        right(ask, waits, (), "ask"),
        right(stall, cap_tries, (), "stall"),
        up(cap_tries, waits, ("yes",), "ask"),
        right(cap_tries, again, ("no",), "stall"),
    ]
    loop = 765.0
    d.edges.append(
        Edge(
            [(again.cx, again.bottom), (again.cx, loop), (prep.cx, loop), (prep.cx, prep.bottom)],
            "stall",
            ("next tick: the stage runs again from the committed state",),
            ((prep.cx + again.cx) / 2, loop - 9),
        )
    )
    d.extra = legend(
        110,
        112,
        [
            ("node:agent", "agent"),
            ("node:disp", "dispatcher"),
            ("edge:flow", "moves on"),
            ("edge:back", "goes back"),
            ("edge:ask", "asks the human"),
            ("edge:stall", "stalls, ends"),
        ],
    )
    return d


# --- 04: asking the human --------------------------------------------------------------------


def asking() -> Diagram:
    d = Diagram(
        2100,
        640,
        "04 · Asking the human",
        "Questions travel only through the pull request; the answer comes back into the "
        "story log, so the next run of the stage can read it.",
    )
    src1 = Node(40, 150, 240, 64, "agent", "", "", ("agent cannot decide alone", "(R8)"), "pill")
    src2 = Node(40, 236, 240, 64, "back", "", "", ("rework cap: round over", "max_rounds"), "pill")
    src3 = Node(
        40, 380, 240, 64, "stall", "", "", ("stalled too often:", "attempts at max"), "pill"
    )
    src4 = Node(
        40, 466, 240, 64, "human", "", "", ("PR closed at accept", "without a comment"), "pill"
    )
    agent = Node(
        380,
        180,
        200,
        120,
        "ask",
        "question",
        "agent",
        ("log entry, blocked:", "question, claim", "cleared, commit"),
    )
    post = Node(
        680,
        180,
        220,
        370,
        "disp",
        "post",
        "dispatcher",
        ("the question on", "the PR, verbatim;", "blocked: asked,", "comments_seen = n"),
    )
    human = Node(
        1000, 180, 190, 370, "human", "the human", "human", ("reads the PR,", "wherever they are")
    )
    copy = Node(
        1320,
        150,
        220,
        112,
        "disp",
        "copy back",
        "dispatcher",
        ("new comments into the", "log, blocked: null", "(retry: attempts = 0)"),
    )
    rerun = Node(
        1650,
        150,
        210,
        112,
        "agent",
        "same stage",
        "agent",
        ("runs again and reads", "the answer in the log"),
    )
    discard = Node(
        1320,
        316,
        220,
        100,
        "disp",
        "discard",
        "dispatcher",
        ("on main: story back", "to drafts/; branch", "deleted"),
    )
    archive = Node(
        1320, 456, 220, 100, "disp", "archive", "dispatcher", ("as merged: story", "to done/ (01)")
    )
    end_ok = Node(1950, 180, 120, 52, "end", "moves on", "", (), "pill")
    end_draft = Node(1650, 340, 210, 52, "end", "the human's draft", "", (), "pill")
    end_done = Node(1650, 480, 210, 52, "end", "done", "", (), "pill")
    d.nodes = [
        src1,
        src2,
        src3,
        src4,
        agent,
        post,
        human,
        copy,
        rerun,
        discard,
        archive,
        end_ok,
        end_draft,
        end_done,
    ]
    bus = src1.right + 40
    d.edges = [
        Edge(
            [(src1.right, src1.cy), (bus, src1.cy), (bus, agent.cy - 14), (agent.x, agent.cy - 14)],
            "ask",
        ),
        Edge(
            [(src2.right, src2.cy), (bus, src2.cy), (bus, agent.cy + 14), (agent.x, agent.cy + 14)],
            "back",
        ),
        into(src3, post, src3.cy, ("last stall reason",), "stall"),
        into(src4, post, src4.cy, ("reopened as draft;", "stage: doing"), "back"),
        into(agent, post, agent.cy, ("watcher:", "ask"), "ask"),
        into(post, human, 300, ("watcher: pr", "OPEN n"), "ask"),
        into(human, copy, copy.cy, ("comments", "on the PR"), "ask"),
        into(human, discard, discard.cy, ("closes", "the PR"), "stall"),
        into(human, archive, archive.cy, ("marks ready,", "merges"), "flow"),
        right(copy, rerun, ("next", "tick")),
        right(rerun, end_ok, ("answered",)),
        right(discard, end_draft, ("commit",), "stall"),
        right(archive, end_done, ("commit",)),
    ]
    arc = 116.0
    d.edges.append(
        Edge(
            [(rerun.cx, rerun.y), (rerun.cx, arc), (agent.cx, arc), (agent.cx, agent.y)],
            "ask",
            ("still unclear: asks again",),
            ((agent.cx + rerun.cx) / 2, arc - 8),
        )
    )
    d.extra = legend(
        40,
        616,
        [
            ("node:agent", "agent"),
            ("node:disp", "dispatcher"),
            ("node:human", "human"),
            ("edge:ask", "question and answer"),
            ("edge:stall", "stalls, discards"),
        ],
    )
    return d


# --- 05: feature acceptance -------------------------------------------------------------------


def acceptance() -> Diagram:
    d = Diagram(
        2160,
        580,
        "05 · Feature acceptance",
        "Once per feature, after its last story is archived: the acceptor judges the whole "
        "against FEATURE.md and proposes stories; the human decides by merging or closing.",
    )
    top = 170.0
    due = diamond(110, top + 64, ("acceptance", "due?"))
    nothing = outcome(85, 440, "quiet", "nothing to do", ("for this feature",))
    claim = box(
        330,
        top,
        "agent",
        ("branch and claim", "acceptor"),
        ("acceptance/<feature>", "from main; report with", "stories: [ids];", "draft PR"),
    )
    checks = box(
        600,
        top,
        "agent",
        ("eight checks", "acceptor"),
        (
            "scope, feature demo,",
            "make mutants, noticed",
            "items, docs, decisions,",
            "slow checks, cost",
        ),
    )
    write = box(
        870,
        top,
        "agent",
        ("report and drafts", "acceptor"),
        ("verdict and eight", "sections; proposed", "stories into drafts/"),
    )
    human = Node(
        1160, top, 190, 270, "human", "accept", "human", ("reads the report", "and the drafts")
    )
    archive = Node(
        1470,
        136,
        230,
        128,
        "disp",
        "accepted",
        "dispatcher",
        ("on main: stage done,", "outcome: accepted;", "report and drafts stay,", "branch deleted"),
    )
    refusal = Node(
        1470,
        326,
        230,
        128,
        "disp",
        "refused",
        "dispatcher",
        (
            "on main: the report,",
            "outcome: refused, your",
            "comment under the verdict;",
            "drafts dropped",
        ),
    )
    quiet = Node(
        1800,
        256,
        210,
        92,
        "quiet",
        "feature status",
        "",
        ("accepted or refused,", "until another story", "is archived"),
    )
    d.nodes = [due, nothing, claim, checks, write, human, archive, refusal, quiet]
    d.edges = [
        arrive(20, due, ("watcher:", "a tick")),
        right(due, claim, ("yes",)),
        down(due, nothing, ("no",), "stall"),
        right(claim, checks, ("claim", "pushed")),
        right(checks, write),
        into(write, human, write.cy, ("PR ready;", "stage: accept")),
        into(human, archive, archive.cy, ("merges",)),
        into(human, refusal, refusal.cy, ("closes, with a", "comment: why"), "stall"),
        right(archive, quiet),
        right(refusal, quiet, (), "stall"),
        Edge(
            [(quiet.cx, quiet.y), (quiet.cx, 116), (due.cx, 116), (due.cx, due.y)],
            "back",
            ("another story archived: the report no longer covers the feature, due again",),
            ((due.cx + quiet.cx) / 2, 108),
        ),
    ]
    d.extra = legend(
        40,
        560,
        [
            ("node:agent", "agent"),
            ("node:human", "human"),
            ("node:disp", "dispatcher"),
            ("node:quiet", "nothing happens"),
            ("edge:flow", "moves on"),
            ("edge:back", "loops"),
        ],
    )
    return d


# --- 06: the container loop -------------------------------------------------------------------


def machine() -> Diagram:
    d = Diagram(
        2240,
        560,
        "06 · The machine: one container, repositories in turn",
        "entrypoint.sh owns a checkout of every repository in REPOS and ticks them one after "
        "another, round after round.",
    )
    top = 170.0
    setup = box(
        110,
        top,
        "code",
        ("set up", "entrypoint"),
        ("skills, agents, allow", "list into ~/.claude;", "git identity, gh auth"),
    )
    clean = box(
        380,
        top,
        "code",
        ("clear leftovers", "entrypoint"),
        ("tick and git index", "locks, the tick memo;", "start time noted"),
    )
    pick = box(
        670, top, "code", ("next repository", "entrypoint"), ("from REPOS, in", "the order given")
    )
    prep = box(
        940,
        top,
        "code",
        ("prepare", "entrypoint"),
        ("clone into /work if", "missing; follow main", "until it is set up"),
    )
    ready = diamond(1210, top + 64, ("ready?",))
    tick = box(
        1430, top, "code", ("factory-tick", "see 07"), ("one tick in this", "repository's checkout")
    )
    more = Node(1700, top + 9, 150, 110, "code", "", "", ("more", "repositories?"), "diamond")
    wait = Node(
        1940,
        top,
        250,
        128,
        "code",
        "wait",
        "entrypoint",
        ("2 s if a tick dispatched", "(exit 3), otherwise", "TICK_SECONDS (120 s)"),
    )
    waiting = Node(
        1180,
        350,
        200,
        96,
        "quiet",
        "skip it",
        "logged once",
        ("empty, no stages.yml", "yet, or uv sync failed"),
    )
    d.nodes = [setup, clean, pick, prep, ready, tick, more, wait, waiting]
    d.edges = [
        arrive(20, setup, ("compose", "up")),
        right(setup, clean),
        right(clean, pick, ("once per", "start")),
        right(pick, prep),
        right(prep, ready),
        right(ready, tick, ("yes",)),
        right(tick, more, ("exit 0, 1", "or 3")),
        right(more, wait, ("no: round", "done")),
        down(ready, waiting, ("no",), "stall"),
        Edge(
            [(waiting.right, waiting.cy), (more.cx, waiting.cy), (more.cx, more.bottom)],
            "stall",
            ("on to the next",),
            ((waiting.right + more.cx) / 2, waiting.cy - 9),
        ),
        Edge(
            [(more.cx, more.y), (more.cx, 118), (pick.cx, 118), (pick.cx, pick.y)],
            "back",
            ("yes: the next repository",),
            ((pick.cx + more.cx) / 2, 110),
        ),
        Edge(
            [(wait.cx, wait.bottom), (wait.cx, 490), (pick.cx, 490), (pick.cx, pick.bottom)],
            "back",
            ("next round",),
            ((pick.cx + wait.cx) / 2, 482),
        ),
    ]
    d.extra = legend(
        40,
        540,
        [
            ("node:code", "deterministic code, no model"),
            ("node:quiet", "nothing happens"),
            ("edge:flow", "moves on"),
            ("edge:back", "loops"),
        ],
    )
    return d


# --- 07: one tick -----------------------------------------------------------------------------


def one_tick() -> Diagram:
    d = Diagram(
        2930,
        690,
        "07 · One tick",
        "factory-tick decides whether this repository needs a hand right now and handles the "
        "line in code; a model runs only as a stage agent. Tokens are spent on events, "
        "not on time.",
    )
    top, h, row2, row3 = 140.0, 136.0, 360.0, 540.0
    mid = top + h / 2

    def step(x: float, kind: str, text: tuple[str, str], lines: tuple[str, ...]) -> Node:
        return Node(x, top, 220, h, kind, text[0], text[1], lines)

    lock = diamond(110, mid, ("lock", "free?"))
    pre = diamond(330, mid, ("preflight", "ok? (09)"))
    clean = diamond(550, mid, ("working tree", "clean?"))
    on_branch = diamond(550, row2 + 40, ("on a ticket or", "acceptance", "branch?"))
    fetch = step(
        770,
        "code",
        ("fetch", "tick"),
        ("git fetch --prune;", "on main: fast-forward", "to origin/main"),
    )
    watch = step(
        1060, "code", ("evaluate", "watcher, see 08"), ("one line: what", "should happen next")
    )
    restart = step(
        1350,
        "code",
        ("after a restart", "tick"),
        ("busy with a claim from", "before the machine", "started becomes", "expired"),
    )
    needs = step(
        1640,
        "code",
        ("needs a hand?", "tick"),
        (
            "not for idle or busy, nor",
            "pr whose new comments",
            "are all the factory's own,",
            "nor a line already",
            "handled at this HEAD",
        ),
    )
    disp = step(
        1930,
        "disp",
        ("dispatcher", "code"),
        ("handles that one line;", "a run line starts the", "agent; its cost recorded"),
    )
    ok = diamond(2230, mid, ("ok?",))
    keep = step(
        2430,
        "code",
        ("remember", "tick"),
        ("line and HEAD handled;", "story at the gate:", "cost table on the PR"),
    )
    again = Node(2730, mid - 34, 170, 68, "end", "exit 3", "", ("tick again in 2 s",))
    leftovers = Node(
        785, row2, 190, 80, "stall", "commit leftovers", "", ("of an interrupted", "run, push")
    )
    fails = Node(2210, row2, 180, 80, "stall", "failures + 1", "", ("for this line", "and HEAD"))
    three = diamond(2470, row2 + 40, ("third", "failure?"))
    give_up = Node(
        2440,
        row3 - 10,
        200,
        96,
        "stall",
        "give up",
        "",
        ("comment on the PR;", "tried again after", "a new commit"),
    )
    busy = outcome(85, row2 + 40, "quiet", "exit 0", ("another tick holds it",))
    failed = outcome(305, row2 + 40, "stall", "exit 1", ("logged; the next", "tick checks again"))
    dirty = outcome(525, row3 + 40, "stall", "exit 1", ("main is dirty:", "a human looks"))
    nothing = outcome(1655, row2 + 40, "quiet", "exit 0", ("nothing to do",))
    retry = outcome(2720, row2 + 40, "stall", "exit 1", ("tried again", "next round"))
    d.nodes = [
        lock,
        pre,
        clean,
        on_branch,
        fetch,
        watch,
        restart,
        needs,
        disp,
        ok,
        keep,
        again,
        leftovers,
        fails,
        three,
        give_up,
        busy,
        failed,
        dirty,
        nothing,
        retry,
    ]
    d.edges = [
        arrive(20, lock, ("entrypoint", "(06)")),
        right(lock, pre, ("yes",)),
        right(pre, clean, ("yes",)),
        right(clean, fetch, ("yes",)),
        right(fetch, watch),
        right(watch, restart, ("a line",)),
        right(restart, needs),
        right(needs, disp, ("yes",)),
        right(disp, ok, ("returns",)),
        right(ok, keep, ("yes",)),
        right(keep, again),
        down(lock, busy, ("no",), "stall"),
        down(pre, failed, ("no",), "stall"),
        down(clean, on_branch, ("no",), "stall"),
        right(on_branch, leftovers, ("yes",), "stall"),
        up(leftovers, fetch, ("then on",), "stall"),
        down(on_branch, dirty, ("no",), "stall"),
        down(needs, nothing, ("no",), "stall"),
        Edge(
            [(ok.cx, ok.bottom), (ok.cx, fails.y)],
            "stall",
            ("no: an error, or no commit", "for expired, merged,", "closed or reject"),
            (ok.cx + 9, fails.y - 20),
            "start",
        ),
        right(fails, three, (), "stall"),
        right(three, retry, ("no",), "stall"),
        down(three, give_up, ("yes",), "stall"),
    ]
    d.extra = legend(
        40,
        672,
        [
            ("node:code", "deterministic code"),
            ("node:disp", "model"),
            ("node:quiet", "nothing happens"),
            ("edge:flow", "moves on"),
            ("edge:stall", "stops or recovers"),
        ],
    )
    return d


# --- 08: the watcher's line -------------------------------------------------------------------


def watcher() -> Diagram:
    d = Diagram(
        2520,
        690,
        "08 · The watcher: one line, first match wins",
        "factory-watch reads, never writes. Each check looks at every ongoing story and due "
        "acceptance in id order; the first that matches decides the line.",
    )
    top, h, step = 130.0, 120.0, 320.0
    read = Node(
        60,
        top,
        240,
        h,
        "code",
        "read",
        "watcher",
        (
            "stages.yml; every ongoing",
            "story and due acceptance,",
            "from its branch, origin/main",
            "or the tree; the last commit",
        ),
    )
    checks = [
        ("illegal change?", ("last commit set a stage", "not under next")),
        ("duplicate id?", ("two ongoing files", "with one id")),
        ("waiting on the human?", ("gate stage or blocked:", "asked, and a pr:", "gh pr view")),
        ("question open?", ("blocked: question, or", "a gate stage", "without a pr")),
        ("story claimed?", ("claimed_at is set",)),
        (
            "stage with an agent?",
            ("lowest id first; a", "feature's acceptance", "after its stories"),
        ),
    ]
    nodes = [
        Node(400 + i * step, top, 210, h, "code", t, "", lines)
        for i, (t, lines) in enumerate(checks)
    ]
    idle = Node(400 + 6 * step - 20, top + 26, 130, 68, "quiet", "idle", "", ("nothing to do",))
    d.nodes = [read, *nodes, idle]
    d.edges = [right(read, nodes[0])]
    d.edges += [right(a, b, ("no",)) for a, b in zip(nodes, nodes[1:], strict=False)]
    d.edges.append(right(nodes[-1], idle, ("no",)))
    outputs = [
        [("stage not in next", "reject", ("moved back", "by the dispatcher"), "disp")],
        [("same id twice", "duplicate", ("logged, nothing", "else happens"), "disp")],
        [
            ("gh fails", "error pr-lookup", ("gh login missing?",), "disp"),
            ("MERGED", "merged", ("archived to done/",), "disp"),
            ("CLOSED", "closed", ("back to doing,", "or discarded"), "disp"),
            ("OPEN", "pr OPEN n", ("only new comments", "start the dispatcher"), "disp"),
        ],
        [("yes", "ask", ("question onto", "the PR (04)"), "disp")],
        [
            ("lease alive", "busy", ("nothing: one story", "at a time"), "quiet"),
            ("lease over", "expired", ("claim cleared,", "attempts + 1"), "disp"),
        ],
        [
            ("attempts at max", "ask", ("ask whether", "to retry"), "disp"),
            ("otherwise", "run <agent>", ("the stage agent", "starts (03)"), "disp"),
        ],
    ]
    for check, outs in zip(nodes, outputs, strict=False):
        for j, (label, title, lines, kind) in enumerate(outs):
            out = Node(check.x + 136, top + h + 50 + j * 92, 176, 72, kind, title, "", lines)
            d.nodes.append(out)
            d.edges.append(stub(check, out, check.x + 24, label))
    d.extra = legend(
        40,
        672,
        [
            ("node:code", "check"),
            ("node:disp", "line the dispatcher handles"),
            ("node:quiet", "line without a model"),
            ("edge:flow", "moves on"),
        ],
    )
    return d


# --- 09: the preflight ------------------------------------------------------------------------


def preflight() -> Diagram:
    d = Diagram(
        2720,
        520,
        "09 · The preflight: can this machine run the loop?",
        "Run by the tick before anything else. It checks the machine, not the code, and never "
        "installs anything itself.",
    )
    top, h = 130.0, 130.0
    mid = top + h / 2
    stamp = Node(
        110,
        top,
        210,
        h,
        "code",
        "stamp current?",
        "tick",
        ("written in the last 24 h", "for this factory version", "and this stages.yml"),
    )
    checks = [
        ("tools", ("git, gh, uv, make", "on the PATH", "fix: install them")),
        ("git identity", ("user.name and", "user.email set", "fix: git config")),
        ("gh auth", ("gh auth status", "succeeds", "fix: gh auth login")),
        ("venv", ("the project's", ".venv exists", "fix: uv sync")),
        ("shell tools", ("sh, grep, rm, touch", "for make's recipes", "fix: coreutils")),
        ("agents", ("every agent named", "in stages.yml installed", "fix: rebuild the image")),
    ]
    boxes = [
        Node(400 + i * 210, top, 180, h, "code", t, f"check {i + 1}", lines)
        for i, (t, lines) in enumerate(checks)
    ]
    all_ok = Node(1680, mid - 55, 130, 110, "code", "", "", ("all six", "ok?"), "diamond")
    lint = Node(
        1880,
        top,
        190,
        h,
        "code",
        "make lint",
        "check 7",
        ("make, its shell and", "uv run work together;", "a probe, not the gate"),
    )
    green = Node(2140, mid - 55, 120, 110, "code", "", "", ("green?",), "diamond")
    write = Node(
        2330, top, 180, h, "code", "write stamp", "tick", ("version and", "stages.yml hash")
    )
    go = Node(2570, mid - 30, 130, 60, "end", "tick goes on", "", (), "pill")
    skip = Node(125, 360, 180, 64, "quiet", "skip", "", ("the tick goes on",))
    failed = Node(
        2110,
        340,
        200,
        100,
        "stall",
        "preflight failed",
        "",
        ("every missing line with", "its fix in the tick log"),
    )
    retry = Node(
        2400, 356, 200, 68, "stall", "exit 1", "", ("next tick runs the", "preflight again")
    )
    d.nodes = [stamp, *boxes, all_ok, lint, green, write, go, skip, failed, retry]
    d.edges = [
        arrive(20, stamp, ("tick", "(07)")),
        right(stamp, boxes[0], ("no",)),
        *[right(a, b) for a, b in zip(boxes, boxes[1:], strict=False)],
        right(boxes[-1], all_ok),
        right(all_ok, lint, ("yes",)),
        right(lint, green),
        right(green, write, ("yes",)),
        right(write, go),
        down(stamp, skip, ("yes",)),
        Edge(
            [(all_ok.cx, all_ok.bottom), (all_ok.cx, failed.cy), (failed.x, failed.cy)],
            "stall",
            ("no: make lint is not run",),
            (all_ok.cx + 12, failed.cy - 9),
            "start",
        ),
        down(green, failed, ("no",), "stall"),
        right(failed, retry, (), "stall"),
    ]
    d.extra = legend(
        40,
        498,
        [
            ("node:code", "deterministic code"),
            ("node:quiet", "nothing to do"),
            ("edge:flow", "moves on"),
            ("edge:stall", "fails"),
        ],
    )
    return d


# --- 10: branches over time -------------------------------------------------------------------


def commit(x: float, y: float, kind: str, label: tuple[str, ...], above: bool) -> list[str]:
    """A commit dot by `kind` (who commits), its label above or below."""
    ly = y - 18 if above else y + 30 + 15 * (len(label) - 1)
    return [
        f'<g class="node {kind}"><circle cx="{x:g}" cy="{y:g}" r="9" stroke-width="2.2"/></g>',
        text_block(x, ly, label, "lbl lbl-flow"),
    ]


def band(x1: float, x2: float, y: float, text: str, ready: bool) -> list[str]:
    """The pull request's state over a stretch of the branch: draft, or ready for the human."""
    cls = "pr-ready" if ready else "pr-draft"
    return [
        f'<rect class="{cls}" x="{x1:g}" y="{y:g}" width="{x2 - x1:g}" height="24" rx="5" '
        'stroke-dasharray="5 3"/>',
        f'<text class="note" x="{x1 + 10:g}" y="{y + 16:g}">{escape(text)}</text>',
    ]


def branches() -> Diagram:
    d = Diagram(
        2100,
        640,
        "10 · Branches: one trunk, one short branch per ticket",
        "Time runs left to right. main is the trunk; every story and every feature acceptance "
        "lives on a branch of its own for as long as it runs, and comes back by a merge commit.",
    )
    ticket, trunk, accept = 230.0, 370.0, 510.0
    line = 'class="{c}" stroke-width="{w}" fill="none" stroke-linecap="round"'
    main_line = line.format(w=5, c="trunk")
    side_line = line.format(w=3.5, c="twig")
    d.extra += [
        f'<text class="lane-head" x="40" y="{ticket + 5:g}">ticket/&lt;stem&gt;</text>',
        f'<text class="lane-head" x="40" y="{trunk + 5:g}">main</text>',
        f'<text class="lane-head" x="40" y="{accept + 5:g}">acceptance/&lt;feature&gt;</text>',
        f'<path d="M 200 {trunk:g} L 2060 {trunk:g}" {main_line}/>',
        f'<path d="M 330 {trunk:g} L 390 {ticket:g} L 1290 {ticket:g} L 1390 {trunk:g}" '
        f"{side_line}/>",
        f'<path d="M 630 {trunk:g} L 710 {ticket:g}" {side_line}/>',
        f'<path d="M 1570 {trunk:g} L 1630 {accept:g} L 1750 {accept:g} L 1870 {trunk:g}" '
        f"{side_line}/>",
        *band(390, 1290, ticket - 92, "pull request: draft, opened by intake", False),
        *band(1290, 1390, ticket - 92, "ready", True),
        *band(1630, 1750, accept + 56, "draft", False),
        *band(1750, 1870, accept + 56, "ready", True),
        f'<text class="lane-note" x="1312" y="{ticket + 5:g}">branch deleted</text>',
        f'<text class="lane-note" x="1772" y="{accept + 5:g}">branch deleted</text>',
    ]
    commits = [
        (250, trunk, "human", ("drafts and", "FEATURE.md"), False),
        (330, trunk, "human", ("git mv into", "ongoing/"), False),
        (390, ticket, "agent", ("intake: claim,", "draft PR"), True),
        (490, ticket, "agent", ("ready", "→ tests"), True),
        (590, ticket, "agent", ("tests", "→ doing"), True),
        (630, trunk, "human", ("another", "draft"), False),
        (710, ticket, "disp", ("merge main in,", "every stage"), True),
        (810, ticket, "agent", ("feat:", "…"), True),
        (900, ticket, "agent", ("refactor:", "…"), True),
        (990, ticket, "agent", ("doing", "→ review"), True),
        (1090, ticket, "agent", ("review", "→ docs"), True),
        (1190, ticket, "agent", ("docs", "→ demo"), True),
        (1290, ticket, "agent", ("demo", "→ accept"), True),
        (1390, trunk, "human", ("human merges:", "a merge commit,", "never a squash"), False),
        (1490, trunk, "disp", ("archive: done/,", "branch deleted"), False),
        (1630, accept, "agent", ("acceptor: claim,", "draft PR"), False),
        (1750, accept, "agent", ("feature", "→ accept"), False),
        (1870, trunk, "human", ("human merges", "the report"), True),
        (1970, trunk, "disp", ("outcome:", "accepted"), True),
    ]
    for x, y, kind, label, above in commits:
        d.extra += commit(x, y, kind, label, above)
    d.extra += legend(
        40,
        620,
        [("node:human", "the human"), ("node:agent", "an agent"), ("node:disp", "the dispatcher")],
    )
    return d


def main() -> None:
    for name, build in [
        ("01-stages", stages),
        ("02-lanes", lanes),
        ("03-stage-run", stage_run),
        ("04-asking-the-human", asking),
        ("05-feature-acceptance", acceptance),
        ("06-machine", machine),
        ("07-tick", one_tick),
        ("08-watcher", watcher),
        ("09-preflight", preflight),
        ("10-branches", branches),
    ]:
        (HERE / f"{name}.svg").write_text(render(build()), encoding="utf-8")


if __name__ == "__main__":
    main()
