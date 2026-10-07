"""A test figure for diagram_kit: every node kind and shape, every edge kind, two lanes, a group.

Not part of the manual: the folder starts with `_`, so `diagram_kit.py render` skips it. Run it
with `uv run python docs/reference/_sample/sample.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Lane, Node, route, save  # noqa: E402

C1, C2, C3, C4, C5 = 192, 392, 592, 792, 992  # the five columns' left edges
W = 136  # every node's width
TOP, ROW, LOW = 128, 328, 488  # the tops of the human row and the factory's two rows
CROSSING = 248  # where labels sit on the lines between the lanes
CHANNEL = 456  # the rework lines between the factory's rows


def build() -> Diagram:
    d = Diagram(
        width=1200,
        height=704,
        title="Sample · One story through the factory",
        subtitle="A test figure for the kit: every node kind and shape, every edge kind, "
        "two lanes, a group and the legend.",
        description="The human writes TICKET.md, which moves into intake. Intake, the coder and "
        "the reviewer are agents in the factory's container; the factory's verdict either passes "
        "the story to the human, who accepts it, or sends it back to the coder for rework. The "
        "coder can ask the human a question and stall on a red check.",
    )
    d.add(Lane(104, 168, "Human", note=("writes, answers,", "merges"), head=120))
    d.add(Lane(272, 328, "Factory", note=("agents and", "its code"), head=120))
    d.add(Group(176, 288, 768, 296, caption="container"))

    ticket = d.add(Node(C1, TOP, W, 96, kind="human", shape="document", tag="human"))
    ticket.title, ticket.lines = "`TICKET.md`", ("the story and", "its criteria")
    question = d.add(Node(C2, TOP, W, 96, kind="ask", tag="question", title="On the PR"))
    question.lines = ("waits for", "an answer")
    accept = d.add(Node(C4, 152, W, 48, kind="human", shape="pill", title="Accept"))
    done = d.add(Node(C5, 152, W, 48, kind="end", shape="pill", title="Done"))

    intake = d.add(Node(C1, ROW, W, 96, kind="agent", tag="intake", title="Check"))
    intake.lines = ("is the story", "buildable?")
    coder = d.add(Node(C2, ROW, W, 96, kind="agent", tag="coder", title="Write the code"))
    coder.lines = ("until the check", "is green")
    reviewer = d.add(Node(C3, ROW, W, 96, kind="agent", tag="reviewer", title="Review"))
    reviewer.lines = ("the diff against", "the criteria")
    verdict = d.add(Node(C4, ROW, W, 96, kind="code", shape="diamond", title="Verdict?"))

    idle = d.add(Node(C1, LOW, W, 72, kind="quiet", title="Idle", lines="until the next tick"))
    stalled = d.add(Node(C2, LOW, W, 72, kind="stall", tag="factory", title="Stalled"))
    stalled.lines = "attempts + 1"
    rework = d.add(Node(C3, LOW, W, 72, kind="back", tag="factory", title="Send back"))
    rework.lines = "round + 1"
    rules = d.add(Node(C4, LOW, W, 72, kind="concept", tag="rule", title="`next`"))
    rules.lines = "allowed moves"
    git = d.add(Node(C5, 472, W, 104, kind="store", shape="cylinder", tag="git"))
    git.title, git.lines = "Repository", "`ticket/<stem>`"

    d.add(
        Edge(route(ticket.bottom, intake.top, "v"), label="git mv", pos=CROSSING),
        Edge(route(intake.right, coder.left, "h"), label="buildable"),
        Edge(route(coder.right, reviewer.left, "h"), label=("check", "green")),
        Edge(route(reviewer.right, verdict.left, "h")),
        Edge(route(verdict.top, accept.bottom, "v"), label="pass", pos=CROSSING),
        Edge(route(accept.right, done.left, "h"), label="merged"),
        Edge(
            route(coder.port("top", -16), question.port("bottom", -16), "v"),
            kind="ask",
            label="unclear",
            side="left",
            pos=CROSSING,
        ),
        Edge(
            route(question.port("bottom", 16), coder.port("top", 16), "v"),
            kind="dashed",
            label="answer",
            pos=CROSSING,
        ),
        Edge(
            route(coder.port("bottom", -16), stalled.port("top", -16), "v"),
            kind="stall",
            label="red check",
            side="left",
        ),
        Edge(route(stalled.left, idle.right, "h"), kind="stall", label="next tick"),
        Edge(
            route(verdict.port("bottom", -24), rework.port("top", 24), "vhv", via=CHANNEL),
            kind="back",
            label="rework",
        ),
        Edge(
            route(rework.port("top", -24), coder.port("bottom", 24), "vhv", via=CHANNEL),
            kind="back",
            label="round + 1",
        ),
        Edge(route(rules.top, verdict.bottom, "v"), kind="plain", label="decides"),
        Edge(route(verdict.right, git.top, "hv"), kind="dashed", label="pushed"),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
