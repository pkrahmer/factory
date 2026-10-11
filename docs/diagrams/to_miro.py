"""Convert the diagrams of draw.py into Miro canvas-composer SVG: native shapes, connectors, text.

`python3 docs/diagrams/to_miro.py 01,02 > out.svg` prints the frames for the diagrams named; the
SVG goes to the Miro MCP's canvas_create_from_svg or canvas_update_from_svg. Coordinates are the
generator's, scaled by S, the frames stacked from LAYOUT_ORIGIN. See docs/miro.md.
"""

import re
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import draw  # noqa: E402

S = 2.0  # scale from the generator's pixels to board units
LAYOUT_ORIGIN = (4640, 1840)  # where the first frame sits on the board

KIND = {  # fill, stroke (light mode of draw.STYLE)
    "agent": ("#eaf2fb", "#2f6db5"),
    "human": ("#fff3dc", "#c27400"),
    "disp": ("#f0f1f3", "#6b6f7a"),
    "ask": ("#f3edfb", "#7a4fb5"),
    "stall": ("#fcebeb", "#b53a3a"),
    "back": ("#fdf0e6", "#d0661a"),
    "end": ("#ffffff", "#8a8f99"),
    "code": ("#e8f5f0", "#2a8a6e"),
    "quiet": ("#f7f8fa", "#a3a8b2"),
}
EDGE = {"flow": "#3a3d44", "back": "#d0661a", "ask": "#7a4fb5", "stall": "#b53a3a"}
RECT_CLS = {
    "lane": ("#f7f8fa", "#dfe2e7"),
    "lane-alt": ("#ffffff", "#dfe2e7"),
    "band-main": ("#e7e9ed", "none"),
    "band-ticket": ("#dbe8f7", "none"),
    "pr-draft": ("#f7f8fa", "#a3a8b2"),
    "pr-ready": ("#fff3dc", "#c27400"),
}
TEXT_CLS = {  # size, bold, color
    "title": (22, True, "#1d1f24"),
    "subtitle": (14, False, "#5b606b"),
    "lane-head": (13.5, True, "#1d1f24"),
    "lane-note": (12, False, "#5b606b"),
    "note": (12.5, False, "#4a4e57"),
    "note-b": (12.5, True, "#1d1f24"),
    "lbl-flow": (12, False, "#1d1f24"),
    "lbl-back": (12, False, "#a84f0e"),
    "lbl-ask": (12, False, "#6a3fa5"),
    "lbl-stall": (12, False, "#a32f2f"),
    "t": (15, True, "#1d1f24"),
    "l": (12.5, False, "#30333a"),
}


def n(v: float) -> str:
    return f"{v * S:g}"


class Builder:
    def __init__(self, prefix: str) -> None:
        self.p = prefix
        self.i = 0
        self.back: list[str] = []  # drawn first (lanes, bands, connectors)
        self.front: list[str] = []

    def nid(self) -> str:
        self.i += 1
        return f"{self.p}{self.i}"


def node_content(node: draw.Node) -> str:
    parts = []
    if node.title:
        parts.append(f"<b>{escape(node.title)}</b>")
    if node.tag:
        parts.append(f"<i>{escape(node.tag)}</i>")
    if node.lines:
        parts.append(escape(" ".join(node.lines)))
    return escape("<br>".join(parts))


def shape_for(node: draw.Node, nid: str) -> str:
    fill, stroke = KIND[node.kind]
    extra = ' stroke-dasharray="5,5"' if node.kind == "end" else ""
    common = (
        f'id="{nid}" x="{n(node.x)}" y="{n(node.y)}" width="{n(node.w)}" height="{n(node.h)}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"{extra} data-font-family="noto_sans" '
        f'data-font-size="22" data-text-color="#1d1f24" data-content="{node_content(node)}"'
    )
    if node.shape == "diamond":
        return f'<rect {common} data-shape="rhombus" />'
    rx = 62 if node.shape == "pill" else 16
    return f'<rect {common} rx="{rx}" />'


def side(node: draw.Node, p: tuple[float, float]) -> str:
    x, y = p
    d = {
        "left": abs(x - node.x),
        "right": abs(x - node.right),
        "top": abs(y - node.y),
        "bottom": abs(y - node.bottom),
    }
    if node.shape == "diamond":
        d = {
            "left": _d(p, (node.x, node.cy)),
            "right": _d(p, (node.right, node.cy)),
            "top": _d(p, (node.cx, node.y)),
            "bottom": _d(p, (node.cx, node.bottom)),
        }
    return min(d, key=d.get)


def _d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def find(nodes, p, tol=4):
    for i, nd in enumerate(nodes):
        if nd.x - tol <= p[0] <= nd.right + tol and nd.y - tol <= p[1] <= nd.bottom + tol:
            return i
    return None


def text_lines(el: ET.Element) -> list[tuple[float, float, str]]:
    spans = el.findall("tspan")
    if spans:
        return [(float(s.get("x")), float(s.get("y")), "".join(s.itertext())) for s in spans]
    return [(float(el.get("x")), float(el.get("y")), "".join(el.itertext()))]


def text_el(b: Builder, el: ET.Element) -> None:
    classes = el.get("class", "").split()
    key = next((c for c in reversed(classes) if c in TEXT_CLS), "note")
    size, bold, color = TEXT_CLS[key]
    mono = "mono" in classes
    anchor = el.get("text-anchor", "start")
    lines = text_lines(el)
    fs = size * S
    font = "plex_mono" if mono else "noto_sans"
    if len(lines) == 1:
        x, y, t = lines[0]
        w = ' font-weight="bold"' if bold else ""
        b.front.append(
            f'<text x="{n(x)}" y="{n(y)}" text-anchor="{anchor}" font-family="{font}" '
            f'font-size="{fs:g}" fill="{color}"{w}>{escape(t)}</text>'
        )
        return
    width = max(len(t) for _, _, t in lines) * size * 0.62 * S + 24
    x0 = lines[0][0] * S
    left = x0 - width / 2 if anchor == "middle" else (x0 - width if anchor == "end" else x0)
    top = lines[0][1] * S - fs * 1.05
    align = {"middle": "center", "end": "right"}.get(anchor, "left")
    body = "<br/>".join(escape(t) for _, _, t in lines)
    if bold:
        body = f"<b>{body}</b>"
    b.front.append(
        f'<textArea x="{left:g}" y="{top:g}" width="{width:g}" font-family="{font}" '
        f'font-size="{fs:g}" fill="{color}" text-align="{align}">{body}</textArea>'
    )


def path_segments(d: str) -> list[tuple[float, float]]:
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
    return list(zip(nums[0::2], nums[1::2], strict=False))


def _rect(b: Builder, el: ET.Element, kind: str | None) -> None:
    x, y = float(el.get("x", 0)), float(el.get("y", 0))
    w, h = float(el.get("width", 0)), float(el.get("height", 0))
    fill, stroke = KIND[kind] if kind else RECT_CLS.get(el.get("class", ""), ("#f7f8fa", "#dfe2e7"))
    dash = ' stroke-dasharray="5,5"' if el.get("stroke-dasharray") else ""
    rx = ' rx="8"' if el.get("rx") else ""
    st = f'stroke="{stroke}" stroke-width="2"' if stroke != "none" else 'stroke="none"'
    b.back.append(
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{rx} fill="{fill}" '
        f"{st}{dash} />"
    )


def _circle(b: Builder, el: ET.Element, kind: str | None) -> None:
    cx, cy, r = (float(el.get(k, 0)) for k in ("cx", "cy", "r"))
    fill, stroke = KIND[kind or "disp"]
    b.front.append(
        f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="3" />'
    )


def _path(b: Builder, el: ET.Element, _kind: str | None) -> None:
    """A free line (a bracket, a legend sample): one divider per segment, no arrowhead."""
    pts = path_segments(el.get("d", ""))
    m = re.search(r"e-(\w+)", el.get("class", ""))
    color = EDGE.get(m.group(1), "#3a3d44") if m else "#3a3d44"
    style = ' data-line-style="dashed"' if m and m.group(1) in ("ask", "stall") else ""
    for (ax, ay), (bx, by) in zip(pts, pts[1:], strict=False):
        b.back.append(
            f'<line data-type="divider" x1="{n(ax)}" y1="{n(ay)}" x2="{n(bx)}" '
            f'y2="{n(by)}" stroke="{color}" stroke-width="3"{style} />'
        )


def extra_el(b: Builder, el: ET.Element, kind: str | None = None) -> None:
    """One element of a diagram's raw SVG extras; a node group passes its kind to its children."""
    if el.tag == "g":
        group_kind = next((k for k in KIND if k in el.get("class", "").split()), None)
        for ch in el:
            extra_el(b, ch, group_kind)
    elif el.tag == "text":
        text_el(b, el)
    elif handler := {"rect": _rect, "circle": _circle, "path": _path}.get(el.tag):
        handler(b, el, kind)


def frame_head(d: draw.Diagram, prefix: str, fx: float, fy: float, title: str) -> str:
    return (
        f'<g id="{prefix}f" transform="translate({fx:g},{fy:g})" data-frame="{escape(title)}">\n'
        f'<rect data-type="frame" x="0" y="0" width="{n(d.width)}" height="{n(d.height)}" '
        f'fill="#ffffff" />\n'
        f'<text x="{n(40)}" y="{n(46)}" font-family="noto_sans" font-size="44" '
        f'font-weight="bold" fill="#1d1f24">{escape(d.title)}</text>\n'
        f'<text x="{n(40)}" y="{n(72)}" font-family="noto_sans" font-size="28" '
        f'fill="#5b606b">{escape(d.subtitle)}</text>'
    )


def extras(d: draw.Diagram) -> list[ET.Element]:
    """The raw SVG extras as elements; the input is draw.py's own output, not untrusted data."""
    out: list[ET.Element] = []
    for raw in d.extra:
        out.extend(ET.fromstring(f"<r>{unescape_entities(raw)}</r>"))  # noqa: S314
    return out


def convert(d: draw.Diagram, prefix: str, fx: float, fy: float, title: str) -> str:
    b = Builder(prefix)
    for el in extras(d):
        extra_el(b, el)
    ids = [b.nid() for _ in d.nodes]
    anchors: list[str] = []
    connectors: list[str] = []
    for e in d.edges:
        a, z = e.points[0], e.points[-1]
        si, ei = find(d.nodes, a), find(d.nodes, z)
        if si is None:
            aid = b.nid()
            anchors.append(
                f'<circle id="{aid}" cx="{n(a[0])}" cy="{n(a[1])}" r="8" fill="{EDGE[e.kind]}" '
                f'stroke="none" />'
            )
            sref, sside = aid, None
        else:
            sref, sside = ids[si], side(d.nodes[si], a)
        eref, eside = ids[ei], side(d.nodes[ei], z)
        attrs = [
            f'x1="{n(a[0])}" y1="{n(a[1])}" x2="{n(z[0])}" y2="{n(z[1])}"',
            f'stroke="{EDGE[e.kind]}" stroke-width="3" data-arrow="end" data-shape="elbowed"',
            f'data-start="{sref}" data-end="{eref}" data-end-side="{eside}"',
        ]
        if sside:
            attrs.append(f'data-start-side="{sside}"')
        if e.kind in ("ask", "stall"):
            attrs.append('stroke-dasharray="5,5"')
        if e.label:
            attrs.append(f'data-content="{escape(" ".join(e.label))}"')
        connectors.append(f"<line {' '.join(attrs)} />")
    shapes = [shape_for(nd, i) for nd, i in zip(d.nodes, ids, strict=True)]
    head = frame_head(d, prefix, fx, fy, title)
    body = b.back + connectors + anchors + shapes + b.front
    return head + "\n" + "\n".join(body) + "\n</g>"


def unescape_entities(raw: str) -> str:
    # keep XML entities valid for ElementTree; the generator only emits &lt; &gt; &amp; &#x27;
    return raw.replace("&#x27;", "'")


DIAGRAMS = [
    ("01", draw.stages),
    ("02", draw.lanes),
    ("03", draw.stage_run),
    ("04", draw.asking),
    ("05", draw.acceptance),
    ("06", draw.machine),
    ("07", draw.one_tick),
    ("08", draw.watcher),
    ("09", draw.preflight),
    ("10", draw.branches),
]


def layout(x0: float, y0: float, gap: float = 160):
    y = y0
    out = []
    for num, fn in DIAGRAMS:
        d = fn()
        out.append((num, x0, y, d))
        y += d.height * S + gap
    return out


def _branch_parts(d: draw.Diagram) -> tuple[list, list, list]:
    """Commits (x, y, kind), branch paths and everything else among 10's extras."""
    circles, paths, others = [], [], []
    for el in extras(d):
        c = el.find("circle") if el.tag == "g" else None
        if c is not None:
            kind = next(k for k in KIND if k in el.get("class", "").split())
            circles.append((float(c.get("cx", 0)), float(c.get("cy", 0)), kind))
        elif el.tag == "path":
            paths.append(el)
        else:
            others.append(el)
    return circles, paths, others


def _branch_lines(
    pts: list[tuple[float, float]], trunk: bool, points: dict[tuple[float, float], str]
) -> list[str]:
    """Connectors along one branch path, split at every commit that lies on a straight run."""
    color, width = ("#3a3d44", 4) if trunk else ("#8a8f99", 3)
    out = []
    for a, z in zip(pts, pts[1:], strict=False):
        lo, hi = min(a[0], z[0]), max(a[0], z[0])
        on = {p for p in points if a[1] == z[1] == p[1] and lo <= p[0] <= hi}
        chain = sorted(on | {a, z}, key=lambda p: p[0], reverse=a[0] > z[0])
        for p, q in zip(chain, chain[1:], strict=False):
            out.append(
                f'<line x1="{n(p[0])}" y1="{n(p[1])}" x2="{n(q[0])}" y2="{n(q[1])}" '
                f'stroke="{color}" stroke-width="{width}" data-shape="straight" '
                f'data-start="{points[p]}" data-end="{points[q]}" />'
            )
    return out


def convert_branches(d: draw.Diagram, prefix: str, fx: float, fy: float, title: str) -> str:
    """10 is drawn from raw SVG: commits become circles, branch lines connectors between them."""
    b = Builder(prefix)
    circles, paths, others = _branch_parts(d)
    for el in others:
        extra_el(b, el)
    points: dict[tuple[float, float], str] = {}  # (x, y) -> local id
    shapes, anchors = [], []
    for x, y, kind in circles:
        points[(x, y)] = cid = b.nid()
        fill, stroke = KIND[kind]
        shapes.append(
            f'<circle id="{cid}" cx="{n(x)}" cy="{n(y)}" r="{n(10)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="4" />'
        )
    segs = [(path_segments(el.get("d", "")), "trunk" in el.get("class", "")) for el in paths]
    for pts, _ in segs:
        for p in pts:
            if p not in points:  # a bend or an end without a commit: a small junction dot
                points[p] = aid = b.nid()
                anchors.append(
                    f'<circle id="{aid}" cx="{n(p[0])}" cy="{n(p[1])}" r="6" fill="#8a8f99" '
                    f'stroke="none" />'
                )
    conns = [line for pts, trunk in segs for line in _branch_lines(pts, trunk, points)]
    body = b.back + conns + anchors + shapes + b.front
    return frame_head(d, prefix, fx, fy, title) + "\n" + "\n".join(body) + "\n</g>"


def build(which: list[str]) -> str:
    parts = []
    for num, x, y, d in layout(*LAYOUT_ORIGIN):
        if num in which:
            conv = convert_branches if num == "10" else convert
            parts.append(conv(d, f"d{num}_", x, y, d.title.replace("·", "-")))
    return '<svg xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(parts) + "\n</svg>"


if __name__ == "__main__":
    print(build(sys.argv[1].split(",")))
