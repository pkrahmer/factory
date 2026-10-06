"""Figure 1-2: the two questions that sort a step, and the three owners of the work.

Renders `three_kinds_of_work.svg` beside this script; `three_kinds_of_work.md` describes it.
"""

import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Node, Text, route, save  # noqa: E402

WIDTH, HEIGHT = 960, 624
COLS = (40, 344, 648)  # the left edges of the human, model and code columns
COL_W, GAP = 272, 32  # every column's width, and the space between two columns
COL_Y, COL_H = 288, 296  # the columns' top and height
INSET = 16  # the header box inside its column
HEAD_H = 56  # the header boxes: tag and title
LIST_Y = 392  # the first step's baseline
FOOT_Y = 544  # the footer's first baseline
BULLET, STEP = 24, 40  # x offsets in a column: the bullets and the step texts
TOP = 104  # the top of the decision row
DIA_W, DIA_H = 176, 112  # the question diamonds
MID = TOP + DIA_H // 2  # the decision row's middle line
VIA = 256  # the channel where two answers turn towards their columns
ITALIC_NOTES = ".tx-note { font-style: italic; }\n"


class Owner(NamedTuple):
    """One owner's column: its node kind, header tag and title, steps and footer lines."""

    kind: str
    tag: str
    title: str
    steps: tuple[str, ...]
    footer: tuple[str, ...]


OWNERS = (
    Owner(
        "human",
        "the human",
        "Intent and acceptance",
        ("start the story", "answer “(a)”", "merge"),
        ("Only the human holds the purpose", "and the accountability"),
    ),
    Owner(
        "agent",
        "a model",
        "Judgment and writing",
        (
            "is it buildable?",
            "which tests",
            "which code",
            "is it good?",
            "what must a reader know?",
            "does the output match?",
        ),
        ("Many acceptable results;", "choosing well takes understanding"),
    ),
    Owner(
        "code",
        "code",
        "Bookkeeping",
        ("branches", "state", "commits", "posts", "checks", "counts", "the bill"),
        ("One right result;", "it must be exact and cheap"),
    ),
)


class _Figure(Diagram):
    """A diagram whose notes are set in italics, for the footers; the kit has no italic style."""

    def to_svg(self) -> str:
        return super().to_svg().replace("<style>\n", "<style>\n" + ITALIC_NOTES, 1)


def _column(d: Diagram, x: int, owner: Owner) -> Node:
    """A column: the group, the header box, the steps and the footer; returns the header box."""
    d.add(Group(x, COL_Y, COL_W, COL_H, kind=owner.kind))
    head = d.add(Node(x + INSET, COL_Y + INSET, COL_W - 2 * INSET, HEAD_H, kind=owner.kind))
    head.tag, head.title = owner.tag, owner.title
    d.add(
        Text(x + BULLET, LIST_Y, ("•",) * len(owner.steps), style="bold", kind=owner.kind),
        Text(x + STEP, LIST_Y, owner.steps),
        Text(x + BULLET, FOOT_Y, owner.footer, style="note"),
    )
    return head


def build() -> Diagram:
    d = _Figure(
        width=WIDTH,
        height=HEIGHT,
        title="Three kinds of work",
        subtitle="Two questions sort every step to one of three owners; each column lists "
        "the steps that fell to it in chapter 1’s story.",
        description="A step in the work meets two questions. The first asks whether it decides "
        "what is wanted, or whether a result is accepted: if yes, it is intent and acceptance, "
        "and it belongs to the human. If not, the second asks whether there is exactly one right "
        "result that code can reach: if yes, it is bookkeeping, and it belongs to code; if no, it "
        "is judgment and writing, and it belongs to a model. Below the questions, three columns "
        "list the steps of chapter 1's health-endpoint story that fell to each owner. The human "
        "started the story, answered (a) and merged, because only the human holds the purpose "
        "and the accountability. A model judged whether the story was buildable, which tests "
        "and which code to write, whether it was good, what a reader must know and whether the "
        "output matched, because these have many acceptable results. Code kept the branches, "
        "the state, the commits, the posts, the checks, the counts and the bill, because each "
        "has one right result that must be exact and cheap.",
        legend=None,
    )
    step = d.add(Node(40, MID - 24, 168, 48, shape="pill", title="A step in the work"))
    # q1 stands over the gap between the human and model columns, q2 over the next one.
    q1 = d.add(Node(COLS[1] - GAP // 2 - DIA_W // 2, TOP, DIA_W, DIA_H, shape="diamond"))
    q1.lines = ("Decides", "what is wanted", "or accepted?")
    q2 = d.add(Node(COLS[2] - GAP // 2 - DIA_W // 2, TOP, DIA_W, DIA_H, shape="diamond"))
    q2.lines = ("One right", "result, reachable", "by code?")

    human, model, code = (_column(d, x, owner) for x, owner in zip(COLS, OWNERS, strict=True))

    d.add(
        Edge(route(step.right, q1.left, "h")),
        Edge(route(q1.right, q2.left, "h"), label="no"),
        Edge(route(q1.bottom, human.top, "vhv", via=VIA), label="yes", segment=0),
        Edge(route(q2.bottom, model.top, "vhv", via=VIA), label="no", segment=0),
        Edge(route(q2.right, code.top, "hv"), label="yes", segment=0),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
