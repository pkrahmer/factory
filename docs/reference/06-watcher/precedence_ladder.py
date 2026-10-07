"""Figure 6-1. The order of events: the watcher's evaluation as a ladder of seven rungs.

Read from the top: each rung is a rule with the events it can return; the first rung that matches
returns its event and the evaluation stops. Four shaded bands group the rungs by what they protect;
the events stand in a column to the right of the rungs, and two notes at the far right say what the
tick hands on and what holds the ladder.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Lane, Legend, Node, Text, route, save  # noqa: E402

LANE_X, LANE_W, HEAD = 40, 608, 112  # the bands: left edge, width, width of the label head
RUNG_X, RUNG_W, RUNG_H = 160, 280, 56  # every rung
EVENT_X, EVENT_W = 488, 152  # the column of events, 48 px right of the rungs
NOTE_X, NOTE_W = 664, 144  # the notes at the far right
TOP, STRIDE = 128, 88  # the first rung's top; the distance from one rung's top to the next
GAP = STRIDE - RUNG_H  # the no-match arrows
PAD_ABOVE, PAD_BELOW = 12, 20  # a band's room above its first rung and below its last

type Rung = tuple[str, str, str, str, tuple[str, ...]]  # kind, tag, condition, band, events

RUNGS: tuple[Rung, ...] = (
    ("stall", "`_rejected`", "an illegal stage change in the last commit", "c", ("`reject`",)),
    ("stall", "`_duplicated`", "two work items with one identifier", "c", ("`duplicate`",)),
    (
        "human",
        "`_pull_requests`",
        "the first waiting work item's pull request",
        "h",
        ("`error pr-lookup`", "`merged` · `closed` · `pr`"),
    ),
    ("ask", "`_asking`", "a question to post, or a gate without `pr`", "h", ("`ask`",)),
    ("code", "`_leased`", "a run record exists", "a", ("`busy` · `expired`",)),
    (
        "agent",
        "`_runnable`",
        "the lowest identifier in a stage with an agent",
        "n",
        ("`ask` (attempts cap)", "`run`"),
    ),
    ("quiet", "", "nothing matched", "n", ("`idle`",)),
)
BANDS = (  # label, note, the rungs it holds (by index)
    ("Corrections", "and integrity", (0, 1)),
    ("The human's", "signals", (2, 3)),
    ("The agent", "at work", (4,)),
    ("New work", "", (5, 6)),
)


def build() -> Diagram:
    d = Diagram(
        width=848,
        height=812,
        title="The order of events",
        subtitle="The watcher tries seven rules from the top; the first that matches returns "
        "its event.",
        description="A ladder of seven rungs, read from the top. Each rung is a rule of the "
        "watcher with the events it can return, and the first rung that matches returns its event "
        "and ends the evaluation. Rungs one and two, corrections and integrity: an illegal stage "
        "change in the last commit returns reject, two work items with one identifier return "
        "duplicate. Rungs three and four, the human's signals: the pull request of the first "
        "waiting work item returns error pr-lookup, merged, closed or pr; a question recorded "
        "but not yet posted, or a gate without a pull request, returns ask. Rung five, "
        "the agent at work: a run record returns busy "
        "or expired. Rungs six and seven, new work: the lowest identifier in a stage with an "
        "agent returns ask when the attempts cap is reached, otherwise run; if nothing matched, "
        "the event is idle. The tick never handles busy, idle, and pr without new human "
        "comments. A waiting work item makes rung three match on every tick, so nothing below "
        "it runs.",
        legend=Legend(
            nodes={
                "stall": "a correction",
                "human": "the human",
                "ask": "asks the human",
                "code": "agent at work",
                "agent": "new work",
                "quiet": "nothing",
            },
            edges={"plain": "no match: the next rung", "flow": "match: the event"},
        ),
    )

    # the bands first, so the rungs stand on them; each ends part-way down the gap below it
    for label, note, held in BANDS:
        top = TOP + STRIDE * held[0] - PAD_ABOVE
        bottom = TOP + STRIDE * held[-1] + RUNG_H + PAD_BELOW
        if held[-1] == len(RUNGS) - 1:
            bottom = TOP + STRIDE * held[-1] + RUNG_H + PAD_ABOVE
        if held[0] == 0:
            top = TOP - PAD_ABOVE
        d.add(Lane(top, bottom - top, label, note=note, x=LANE_X, w=LANE_W, head=HEAD))

    d.add(
        Text(RUNG_X + RUNG_W / 2, TOP - 22, "the rule", style="bold", align="middle"),
        Text(EVENT_X + EVENT_W / 2, TOP - 22, "the event", style="bold", align="middle"),
    )

    rungs: list[Node] = []
    for i, (kind, tag, condition, _, events) in enumerate(RUNGS):
        y = TOP + STRIDE * i
        rung = d.add(Node(RUNG_X, y, RUNG_W, RUNG_H, kind=kind, tag=tag, lines=condition))
        event = d.add(Node(EVENT_X, y, EVENT_W, RUNG_H, kind=kind, lines=events))
        d.add(Edge(route(rung.right, event.left, "h")))
        if rungs:
            above = rungs[-1]
            d.add(
                Edge(
                    route(above.bottom, rung.top, "v"),
                    kind="plain",
                    label="no match",
                    pos=above.y2 + 10,
                )
            )
        rungs.append(rung)

    d.add(
        Node(
            NOTE_X,
            304,
            NOTE_W,
            104,
            kind="human",
            lines=(
                "a waiting work item",
                "makes rung 3 match",
                "on every tick, so",
                "nothing below it",
                "runs",
            ),
        ),
        Node(
            NOTE_X,
            536,
            NOTE_W,
            120,
            kind="quiet",
            lines=(
                "never handled by",
                "the tick: `busy`,",
                "`idle`, and `pr`",
                "without new",
                "human comments",
            ),
        ),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
