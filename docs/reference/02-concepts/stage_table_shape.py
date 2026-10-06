"""Figure 2-1. The shape of a stage table: v1's line, its rework arcs, questions and the discard.

Nine boxes do not fit one line at a readable size, so the line wraps once, after the tests: the
draft and the two stages before the code on the top row, the coding stage and the stages after
it on the bottom row, where the four rework arcs nest beneath it. The archive, the line's end,
sits above the gate, beside the question pill.
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

W, H = 160, 112  # every stage box
C1, C2, C3, C4, C5 = 64, 296, 520, 752, 976  # the five columns' left edges
TOP, LOW = 104, 336  # the tops of the two rows
GUTTER = 40  # the x of the discard's climb to the drafts, left of both rows
WRAP, TESTS_BACK = 256, 296  # the wrap from the tests to the code, and the way back
DISCARD = 616  # the discard along the bottom, below the rework arcs

type Box = tuple[int, int, str, str, str, tuple[str, ...]]  # x, y, kind, tag, title, body

BOXES: dict[str, Box] = {
    "drafts": (
        C1,
        TOP,
        "human",
        "human · `drafts/`",
        "Draft",
        ("the human's text;", "not worked on"),
    ),
    "intake": (
        C2,
        TOP,
        "agent",
        "intake · `ready`",
        "Vet the story",
        ("buildable? exact", "interface, testable", "criteria, failing sides"),
    ),
    "tests": (
        C3,
        TOP,
        "agent",
        "tester · `tests`",
        "Write the tests",
        ("one test per criterion,", "red on purpose"),
    ),
    "doing": (
        C1,
        LOW,
        "agent",
        "coder · `doing`",
        "Write the code",
        ("until the full check", "is green; refactor once"),
    ),
    "review": (
        C2,
        LOW,
        "agent",
        "reviewer · `review`",
        "Review",
        ("the diff against the", "story and the", "architecture"),
    ),
    "docs": (
        C3,
        LOW,
        "agent",
        "documenter · `docs`",
        "Document",
        ("what the reader must", "know; stale text fixed"),
    ),
    "demo": (
        C4,
        LOW,
        "agent",
        "demo · `demo`",
        "Demonstrate",
        ("run the commands,", "compare with the", "expected output"),
    ),
    "gate": (C5, LOW, "human", "gate · `accept`", "Accept", ("the human merges,", "or sends back")),
}

REWORK = {  # the arcs back to the coding stage, inner first: label, port on `doing`, level
    "review": ("findings · round + 1", 36, 480),
    "docs": ("code contradicts the story · round + 1", 12, 512),
    "demo": ("output wrong · round + 1", -12, 544),
    "gate": ("closed with a reason · round + 1", -36, 576),
}
CLEAR = 24  # between a rework label's end and the arc's climb to its stage


def add_nodes(d: Diagram) -> dict[str, Node]:
    """The stage boxes in two rows, the question pill and the archive above the gate."""
    n = {
        key: d.add(Node(x, y, W, H, kind=kind, tag=tag, title=title, lines=body))
        for key, (x, y, kind, tag, title, body) in BOXES.items()
    }
    n["drafts"].shape = "document"
    n["human"] = d.add(Node(712, TOP, 240, H, kind="ask", shape="pill", tag="question"))
    n["human"].title = "The human answers"
    n["human"].lines = (
        "from any working stage,",
        "on the pull request; the stage",
        "that asked runs again",
    )
    n["done"] = d.add(Node(1000, 128, 112, 64, kind="end", shape="pill", tag="`done`"))
    n["done"].title = "Archived"
    return n


def forward(d: Diagram, n: dict[str, Node]) -> None:
    """The forward line: along the top row, back to the start of the bottom row, on to the end."""
    tests, doing = n["tests"], n["doing"]
    d.add(
        Edge(route(n["drafts"].right, n["intake"].left, "h"), label="promoted"),
        Edge(route(n["intake"].right, tests.left, "h"), label="buildable"),
        Edge(
            route(tests.port("bottom", -24), doing.port("top", -24), "vhv", via=WRAP),
            label="checks green (lint)",
            pos=480,
        ),
        Edge(route(doing.right, n["review"].left, "h"), label=("checks", "green (full)")),
        Edge(route(n["review"].right, n["docs"].left, "h"), label=("no", "findings")),
        Edge(route(n["docs"].right, n["demo"].left, "h"), label=("checks", "green (full)")),
        Edge(route(n["demo"].right, n["gate"].left, "h"), label=("output as", "expected")),
        Edge(route(n["gate"].top, n["done"].bottom, "v"), label="merged"),
    )


def rework(d: Diagram, n: dict[str, Node]) -> None:
    """The moves back: four nested arcs below to the coding stage, one above to the tests."""
    doing = n["doing"]
    for key, (label, port, level) in REWORK.items():
        source = n[key].bottom
        path = route(source, doing.port("bottom", port), "vhv", via=level)
        x = source[0] - CLEAR - text_width(label, FONTS["lb"]) / 2  # ends just before the climb
        d.add(Edge(path, kind="back", label=label, pos=x))
    path = route(doing.port("top", 24), n["tests"].port("bottom", 24), "vhv", via=TESTS_BACK)
    d.add(Edge(path, kind="back", label="approved test change · no round", pos=400))


def asides(d: Diagram, n: dict[str, Node]) -> None:
    """A question and its answer, for any working stage; the discard back to the drafts."""
    demo, human, drafts = n["demo"], n["human"], n["drafts"]
    up, down = demo.port("top", -16), demo.port("top", 16)
    start = (demo.x2 + n["gate"].x) / 2  # the discard starts just before the gate
    label = "closed before the gate: discarded"
    d.add(
        Edge(route(up, (up[0], human.y2), "v"), kind="ask", label="question", side="left"),
        Edge(route((down[0], human.y2), down, "v"), kind="ask", label="answer"),
        Edge(
            [(start, DISCARD), (GUTTER, DISCARD), (GUTTER, drafts.cy), drafts.left],
            kind="stall",
            label=label,
            pos=start - CLEAR - text_width(label, FONTS["lb"]) / 2,
        ),
        Text(start + 12, DISCARD + 4, "any stage before the gate", style="note", kind="stall"),
    )


def build() -> Diagram:
    d = Diagram(
        width=1176,
        height=680,
        title="The shape of a stage table",
        subtitle="The general pattern, drawn with v1's line: forward to the human's gate, rework "
        "back to the code, questions to the human.",
        description="The general pattern of a stage table, drawn with v1's line. A story starts "
        "as the human's draft. Promoted, it passes the forward line: check the story, write the "
        "tests, write the code, review, document, demonstrate, then the human's gate, and it is "
        "archived when merged. The line wraps once, after the tests. Review, documentation, "
        "demonstration and the human at the gate can send the story back to the coding stage, "
        "each at the cost of a round; the coding stage can return it to the tests stage after an "
        "approved test change, at no cost. Any working stage can ask the human a question, and "
        "the answer returns to the same stage. Closing the pull request before the gate discards "
        "the story back to the drafts. Each box names the stage, its role and v1's key for it.",
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
