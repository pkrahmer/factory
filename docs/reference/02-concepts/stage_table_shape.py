"""Figure 2-1. The shape of a stage table: v1's line, its rework arcs, questions and the discard.

Nine boxes do not fit one line at a readable size, so the line runs down one column, from the
draft to the archive. The four rework arcs nest on its right-hand side and climb back to the
coding stage; the question pill sits beside the first working stage, in the free space above
them. The discard leaves the line just before the gate and climbs the left-hand side to the draft.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import (  # noqa: E402
    FONTS,
    Diagram,
    Edge,
    Legend,
    Node,
    Text,
    route,
    save,
    text_width,
)

W = 352  # every stage box
X = 96  # the column's left edge
CX = X + W // 2  # the forward line
GUTTER = 40  # the x of the discard's climb to the drafts, left of the column
CLEAR = 24  # between a rework label's end and the arc's climb to its stage

type Box = tuple[int, int, str, str, str, tuple[str, ...]]  # y, h, kind, tag, title, body

BOXES: dict[str, Box] = {
    "drafts": (
        104,
        72,
        "human",
        "human · `drafts/`",
        "Draft",
        ("the human's text; not worked on",),
    ),
    "intake": (
        216,
        96,
        "agent",
        "intake · `ready`",
        "Vet the story",
        ("buildable? exact interface,", "testable criteria, failing sides"),
    ),
    "tests": (
        352,
        72,
        "agent",
        "tester · `tests`",
        "Write the tests",
        ("one test per criterion, red on purpose",),
    ),
    "doing": (
        472,
        72,
        "agent",
        "coder · `doing`",
        "Write the code",
        ("until the full check is green; refactor once",),
    ),
    "review": (
        584,
        72,
        "agent",
        "reviewer · `review`",
        "Review",
        ("the diff against the story and the architecture",),
    ),
    "docs": (
        696,
        72,
        "agent",
        "documenter · `docs`",
        "Document",
        ("what the reader must know; stale text fixed",),
    ),
    "demo": (
        808,
        72,
        "agent",
        "demo · `demo`",
        "Demonstrate",
        ("run the commands, compare with the expected output",),
    ),
    "gate": (944, 72, "human", "gate · `accept`", "Accept", ("the human merges, or sends back",)),
}

REWORK = {  # the arcs back to the coding stage, inner first: label, port on `doing`, x of the climb
    "review": ("findings · round + 1", 24, 648),
    "docs": ("code contradicts the story · round + 1", 8, 680),
    "demo": ("output wrong · round + 1", -8, 712),
    "gate": ("closed with a reason · round + 1", -24, 744),
}


def add_nodes(d: Diagram) -> dict[str, Node]:
    """The stage boxes in one column, the question pill beside the first working stage."""
    n = {
        key: d.add(Node(X, y, W, h, kind=kind, tag=tag, title=title, lines=body))
        for key, (y, h, kind, tag, title, body) in BOXES.items()
    }
    n["drafts"].shape = "document"
    intake = n["intake"]
    n["human"] = d.add(
        Node(544, intake.cy - 56, 256, 112, kind="ask", shape="pill", tag="question")
    )
    n["human"].title = "The human answers"
    n["human"].lines = (
        "from any working stage,",
        "on the pull request; the stage",
        "that asked runs again",
    )
    n["done"] = d.add(Node(CX - 56, 1056, 112, 64, kind="end", shape="pill", tag="`done`"))
    n["done"].title = "Archived"
    return n


def forward(d: Diagram, n: dict[str, Node]) -> None:
    """The forward line: straight down the column, from the draft to the archive."""
    labels = {
        ("drafts", "intake"): "promoted",
        ("intake", "tests"): "buildable",
        ("doing", "review"): "checks green (full)",
        ("review", "docs"): "no findings",
        ("docs", "demo"): "checks green (full)",
        ("demo", "gate"): "output as expected",
        ("gate", "done"): "merged",
    }
    for (a, b), label in labels.items():
        d.add(Edge(route(n[a].bottom, n[b].top, "v"), label=label))
    tests, doing = n["tests"], n["doing"]
    d.add(
        Edge(
            route(tests.port("bottom", -24), doing.port("top", -24), "v"),
            label="checks green (lint)",
            side="left",
        )
    )


def rework(d: Diagram, n: dict[str, Node]) -> None:
    """The moves back: four nested arcs on the right to the coding stage, one up to the tests."""
    doing = n["doing"]
    for key, (label, port, climb) in REWORK.items():
        path = route(n[key].right, doing.port("right", port), "hvh", via=climb)
        x = climb - CLEAR - text_width(label, FONTS["lb"]) / 2  # ends just before the climb
        d.add(Edge(path, kind="back", label=label, segment=0, pos=x))
    path = route(doing.port("top", 24), n["tests"].port("bottom", 24), "v")
    d.add(Edge(path, kind="back", label="approved test change · no round"))


def asides(d: Diagram, n: dict[str, Node]) -> None:
    """A question and its answer, for any working stage; the discard back to the drafts."""
    intake, human, drafts, demo, gate = n["intake"], n["human"], n["drafts"], n["demo"], n["gate"]
    up, down = intake.port("right", -16), intake.port("right", 16)
    start = (CX, (demo.y2 + gate.y) / 2)  # the discard leaves the line just before the gate
    label = "closed before the gate: discarded"
    middle = (
        CX - 16 - text_width(label, FONTS["lb"]) / 2
    )  # the label's middle, ends before the line
    d.add(
        Edge(route(up, human.port("left", -16), "h"), kind="ask", label="question"),
        Edge(route(human.port("left", 16), down, "h"), kind="ask", label="answer", side="below"),
        Edge(
            [start, (GUTTER, start[1]), (GUTTER, drafts.cy), drafts.left],
            kind="stall",
            label=label,
            segment=0,
            pos=middle,
        ),
        Text(
            middle,
            start[1] + 18,
            "any stage before the gate",
            style="note",
            kind="stall",
            align="middle",
        ),
    )


def build() -> Diagram:
    d = Diagram(
        width=850,
        height=1200,
        title="The shape of a stage table",
        subtitle="The general pattern, drawn with v1's line: forward to the human's gate, rework "
        "back to the code, questions to the human.",
        description="The general pattern of a stage table, drawn with v1's line. A story starts "
        "as the human's draft. Promoted, it passes the forward line, drawn as a column from top "
        "to bottom: check the story, write the tests, write the code, review, document, "
        "demonstrate, then the human's gate, and it is archived when merged. Review, "
        "documentation, demonstration and the human at the gate can send the story back to the "
        "coding stage, each at the cost of a round; the coding stage can return it to the tests "
        "stage after an approved test change, at no cost. Any working stage can ask the human a "
        "question, and the answer returns to the same stage. Closing the pull request before the "
        "gate discards the story back to the drafts. Each box names the stage, its role and "
        "v1's key for it.",
        legend=Legend(
            nodes={"agent": "agent", "human": "the human", "ask": "question", "end": "end"},
            edges={
                "flow": "forward",
                "back": "rework",
                "ask": "question, answer",
                "stall": "discard",
            },
        ),
    )
    nodes = add_nodes(d)
    forward(d, nodes)
    rework(d, nodes)
    asides(d, nodes)
    return d


if __name__ == "__main__":
    save(build(), __file__)
