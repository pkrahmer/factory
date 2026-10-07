"""Figure 4-1. The anatomy of a story file: its parts, their owners and who writes what.

One tall document on the left, cut into three bands (the factory's state, the human's
specification, the append-only log); the three writers stand on the right, level with what they
write. Solid arrows write, dashed ones write in narrow cases, purple ones speak in the log through
the factory.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, route, save  # noqa: E402

DOC_X, DOC_W = 40, 360  # the document outline
BAND_X, BAND_W = 48, 344  # the three bands inside it
PART_X, PART_W = 56, 328  # every part box
WRITER_X, WRITER_W = 560, 200  # the writers' column
RIGHT = BAND_X + BAND_W  # where the human's arrow meets the specification band
BAND_TOP = 144  # the first band's top: 40 px under the document's top


type Words = tuple[str, str | tuple[str, ...]]  # a part's title and body


def part(d: Diagram, y: float, h: float, kind: str, words: Words) -> Node:
    """One part of the document, its text set from the left like a file."""
    title, lines = words
    node = Node(PART_X, y, PART_W, h, kind=kind, title=title, lines=lines, align="start")
    return d.add(node)


def build() -> Diagram:
    d = Diagram(
        width=848,
        height=936,
        title="The anatomy of a story file",
        subtitle="Every part has one owner; agents write only inside the specification, and only "
        "in narrow cases.",
        description="A story file in production, drawn as one tall document with the writers on "
        "its right. From top to bottom: the frontmatter, which belongs to the factory; the "
        "specification, which belongs to the human, with the title, the assignment, the "
        "interface, the acceptance criteria and the demo; and the append-only log. The factory "
        "is the only writer of the frontmatter and appends every entry to the log. The human "
        "writes the draft of the specification and speaks in the log through pull request "
        "comments, which the factory copies. Stage agents rewrite the assignment when a log "
        "entry changes the meaning, and intake carries an answer into the acceptance criteria. "
        "The text of their log entries reaches the log through the outcome.",
        legend=Legend(
            nodes={"code": "the factory's", "human": "the human's", "agent": "stage agents"},
            edges={
                "flow": "writes",
                "dashed": "may write, in narrow cases",
                "ask": "speaks, through the factory",
            },
        ),
    )

    # the document: an outline, three bands, the parts
    d.add(
        Group(
            DOC_X, 104, DOC_W, 760, caption="`ONGOING/F0002-S0001-health-endpoint.md`", kind="store"
        )
    )
    d.add(
        Group(BAND_X, BAND_TOP, BAND_W, 128, caption="State · the factory's", kind="code"),
        Group(BAND_X, 280, BAND_W, 400, caption="Specification · the human's", kind="human"),
        Group(BAND_X, 688, BAND_W, 160, caption="Log · append-only", kind="code"),
    )
    front = part(
        d,
        176,
        80,
        "code",
        ("Frontmatter", ("`stage` `pr` `blocked`", "`comments_seen` `round` `attempts`")),
    )
    part(d, 312, 64, "human", ("`# Health endpoint`", "the title"))
    assign = part(
        d, 384, 64, "human", ("`## Assignment (as of log entry 1)`", "the current meaning")
    )
    part(d, 456, 64, "human", ("`## Interface`", "modules, signatures, errors"))
    crit = part(
        d,
        528,
        64,
        "human",
        ("`## Acceptance criteria`", "numbered; last two fixed: `make check` · `docs:`"),
    )
    part(d, 600, 64, "human", ("`## Demo`", "command blocks, each with `Expect:`"))
    log = part(
        d,
        720,
        112,
        "code",
        (
            "`## Log (append only)`",
            (
                "`1. … human: created.`",
                "`2. intake: …`",
                "`3. human (pull request comment, …): …`",
                "`… done (pull request merged); cost: …`",
            ),
        ),
    )

    # the writers, each level with what it writes
    factory = d.add(
        Node(WRITER_X, 160, WRITER_W, 112, kind="code", tag="code", title="The factory")
    )
    factory.lines = ("writes state and log;", "restores both after", "every agent run")
    human = d.add(Node(WRITER_X, 288, WRITER_W, 112, kind="human", tag="human", title="The human"))
    human.lines = ("writes the draft; speaks", "in the log through pull", "request comments")
    roles = d.add(Node(WRITER_X, 416, WRITER_W, 112, kind="agent", tag="model"))
    roles.title = "Stage agents"
    roles.lines = ("change the specification", "only to carry in an answer", "or a changed meaning")

    # who writes what: the specification and the frontmatter
    d.add(
        Edge(
            route(factory.port("left", front.cy - factory.cy), front.right, "h"),
            label="only writer",
        ),
        Edge(route(human.left, (RIGHT, human.cy), "h"), label="writes the draft", pos=480),
        Edge(
            route(roles.port("left", assign.cy + 20 - roles.cy), assign.port("right", 20), "h"),
            kind="dashed",
            label=("rewritten when a", "log entry changes", "the meaning"),
        ),
        Edge(
            route(roles.port("left", 36), crit.port("right", -16), "hvh", via=544),
            kind="dashed",
            label=("intake carries", "in an answer"),
        ),
    )

    # who speaks in the log: three arrows enter its right side at their own heights
    d.add(
        Edge(
            route(roles.port("bottom", -60), log.port("right", -32), "vh"),
            kind="ask",
            label="entry text, via the outcome",
            segment=1,
            pos=495,
        ),
        Edge(
            route(human.right, log.right, "hvh", via=784),
            kind="ask",
            label="comments, copied by the factory",
            segment=2,
            pos=600,
        ),
        Edge(
            route(factory.right, log.port("right", 32), "hvh", via=808),
            label="appends every entry",
            segment=2,
            pos=600,
        ),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
