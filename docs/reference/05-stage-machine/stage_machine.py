"""Figure 5-1. v1's stage machine: every stage, the moves between them and who causes each.

A story runs down a vertical line from the drafts to `done`. The moves back to `doing` run up the
right-hand side, nested so they do not cross. The human's merge and close, and the moves out of
any stage before the gate, run down the left-hand side. The feature acceptance is a short line of
its own at the bottom right. Questions and stalls do not change the stage, so they are two notes
at the top right, not arrows.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, route, save  # noqa: E402

W = 176  # every stage box
X = 224  # the main column's left edge
BRACKET = 184  # the x of the bracket and of the discard and the merge, left of the column
GAP = 32  # between the stage boxes (40 between the tests and the coding stage)

type Box = tuple[int, int, str, str, str, tuple[str, ...]]  # y, h, kind, tag, title, body

STAGES: dict[str, Box] = {
    "drafts": (104, 72, "human", "human", "`drafts/`", ("the human's text",)),
    "ready": (
        208,
        112,
        "agent",
        "intake",
        "`ready`",
        ("the branch and", "draft pull request", "opened first"),
    ),
    "tests": (352, 72, "agent", "tester", "`tests`", ("checks: lint · reports: test",)),
    "doing": (464, 72, "agent", "coder", "`doing`", ("checks: check",)),
    "review": (568, 72, "agent", "reviewer", "`review`", ("max rounds 2",)),
    "docs": (672, 96, "agent", "documenter", "`docs`", ("checks: check", "max rounds 2")),
    "demo": (800, 72, "agent", "demo", "`demo`", ("max rounds 2",)),
    "accept": (
        904,
        96,
        "human",
        "gate",
        "`accept`",
        ("the pull request is", "ready for the human"),
    ),
}

REWORK = {  # the moves back to `doing`, inner first: label, port on `doing`, x of the climb
    "review": (("round + 1",), 24, 472),
    "docs": (("round + 1",), 8, 496),
    "demo": (("round + 1",), -8, 520),
    "accept": (("closed (the human)", "round + 1"), -24, 544),
}


def add_stages(d: Diagram) -> dict[str, Node]:
    """The column of stage boxes, the drafts first and the human's gate last."""
    n = {
        key: d.add(Node(X, y, W, h, kind=kind, tag=tag, title=title, lines=body))
        for key, (y, h, kind, tag, title, body) in STAGES.items()
    }
    n["drafts"].shape = "document"
    n["done"] = d.add(Node(X, 1032, W, 64, kind="end", shape="pill", title="`done`"))
    n["done"].lines = "moved to `done/`"
    return n


def add_notes(d: Diagram) -> None:
    """The two things that leave the stage as it is: no arrows, since every agent stage has them."""
    ask = d.add(Node(456, 208, 352, 96, kind="ask", tag="question", title="A question"))
    ask.lines = ("any agent stage: `blocked`, the stage stays;", "the answer runs it again")
    stall = d.add(Node(456, 320, 352, 96, kind="stall", tag="stall", title="A stall"))
    stall.lines = (
        "any agent stage: attempts + 1, the stage stays;",
        "at the cap the human is asked",
    )


def add_forward(d: Diagram, n: dict[str, Node]) -> None:
    """The line down the column, with the human's promotion and merge at its ends."""
    labels = {"drafts": "promoted (the human)", "demo": "hand-over", "accept": "merged (the human)"}
    keys = list(n)
    for a, b in zip(keys, keys[1:], strict=False):
        d.add(Edge(route(n[a].bottom, n[b].top, "v"), label=labels.get(a, "")))


def add_rework(d: Diagram, n: dict[str, Node]) -> None:
    """The four nested moves back to `doing`, and the short one back to the tests, at no cost."""
    doing = n["doing"]
    for key, (label, port, climb) in REWORK.items():
        path = route(n[key].right, doing.port("right", port), "hvh", via=climb)
        d.add(Edge(path, kind="back", label=label, segment=0))
    path = route(doing.port("top", 64), n["tests"].port("bottom", 64), "v")
    d.add(Edge(path, kind="back", label="approved test change · no round"))


def add_bracket(d: Diagram, n: dict[str, Node]) -> None:
    """A bracket beside `ready` to `demo`; from it the discard climbs and the merge descends."""
    top, bottom = n["ready"].y, n["demo"].y2
    d.add(
        Edge(
            [(BRACKET + 16, top), (BRACKET, top), (BRACKET, bottom), (BRACKET + 16, bottom)],
            kind="plain",
            arrow="none",
            label=("any stage", "before the gate"),
            segment=1,
            side="left",
        ),
        Edge(
            route((BRACKET, top), n["drafts"].left, "vh"),
            kind="stall",
            label=("closed before", "the gate: discarded"),
            segment=0,
            side="left",
        ),
        Edge(
            route((BRACKET, bottom), n["done"].left, "vh"),
            kind="dashed",
            label=("merged before", "the gate"),
            segment=0,
            side="left",
        ),
    )


def add_acceptance(d: Diagram) -> None:
    """The feature acceptance: due once per complete feature, with its own gate and its own end."""
    d.add(Group(560, 720, 250, 392, caption="once per complete feature", dashed=True))
    feature = d.add(Node(600, 752, 168, 96, kind="agent", tag="acceptor", title="`feature`"))
    feature.lines = ("due when the", "feature is complete")
    gate = d.add(Node(600, 888, 168, 96, kind="human", tag="gate", title="`accept`"))
    gate.lines = ("the report's", "pull request")
    booked = d.add(Node(568, 1032, 232, 64, kind="end", shape="pill"))
    booked.title, booked.lines = "`done` · accepted or refused", "the report on the main branch"
    d.add(
        Edge(route(feature.bottom, gate.top, "v"), label="report written"),
        Edge(
            route(gate.bottom, booked.top, "v"),
            label=("merged: accepted", "closed: refused"),
        ),
    )


def build() -> Diagram:
    d = Diagram(
        width=850,
        height=1160,
        title="v1's stage machine",
        subtitle="A story runs down the line; the human's merge and close, the rework and the "
        "discard are the other moves.",
        description="v1's stage table as a state machine. A story runs down a vertical line: the "
        "human's draft, promoted to ready, then tests, doing, review, docs and demo, then the "
        "human's gate, accept, and when the human merges, done. Review, docs, demo and the "
        "human's close at the gate send the story back to doing, each at the cost of a round; "
        "doing can return it to tests after an approved test change, at no cost. From any stage "
        "between ready and demo, closing the pull request discards the story back to the drafts, "
        "and merging it moves the story straight to done. A question or a stall does not change "
        "the stage. At the bottom right, once per complete feature, the acceptor writes a report "
        "whose pull request the human merges, accepted, or closes, refused.",
        legend=Legend(
            nodes={"agent": "agent stage", "human": "the human's gate", "end": "end"},
            edges={"flow": "forward", "back": "rework", "stall": "discard"},
            hide=("node:ask", "node:stall", "edge:plain", "edge:dashed"),
        ),
    )
    nodes = add_stages(d)
    add_notes(d)
    add_forward(d, nodes)
    add_rework(d, nodes)
    add_bracket(d, nodes)
    add_acceptance(d)
    return d


if __name__ == "__main__":
    save(build(), __file__)
