"""Figure 8-1. The stage protocol: the fourteen steps, the stores they touch and the exits.

The steps run down the middle, the factory's code in green and the agent, the only model step, in
blue. The stores sit on the left: the pull request and Git at the top, the run record between the
steps that write and remove it, and the failure beside the branch check. The commit and the
hand-over reach back to Git and the pull request along two thin lines in the left margin, so
nothing crosses. The other exits sit on the right: four stall lines join one rail into the stall,
and a question leaves the decision on its own. Two brackets on the far right mark the steps before
and after the agent, and the key stands at the bottom right.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Legend, Node, Text, route, save  # noqa: E402

X, W = 312, 248  # the main column
STORE_X, STORE_W = 80, 152  # the stores on the left
RAIL = 632  # the stall rail, right of the main column
SIDE_X, SIDE_W = 656, 160  # the stall and the question
BRACKET = 832  # the far right brackets (their ticks reach 8 px to the left)
GAP = 16  # between the steps

type Step = tuple[str, int, str, str, tuple[str, ...]]  # key, height, kind, title, body

STEPS: tuple[Step, ...] = (
    (
        "prep",
        96,
        "code",
        "Prepare the branch",
        (
            "first stage: create it, open a",
            "draft pull request",
            "else: fast-forward, merge `main`",
        ),
    ),
    ("form1", 48, "code", "Validate the form", ()),
    ("task", 48, "code", "Compose the task", ()),
    ("rec", 64, "code", "Write the run record", ("`.git/factory-run.json`",)),
    (
        "agent",
        88,
        "agent",
        "The agent run",
        ("`claude -p` · works in its lane", "ends with `{outcome, entry}`"),
    ),
    ("clear", 64, "code", "Remove the run record", ("whatever happened",)),
    ("verify", 64, "code", "Verify the branch", ("still on the work item's branch?",)),
    ("undo", 64, "code", "Undo outside the lane", ("paths changed since the start commit",)),
    ("restore", 48, "code", "Restore state and log", ()),
    ("outcome", 64, "code", "Read the outcome", ("allowed? `stuck`? an error?",)),
    ("form2", 64, "code", "Validate the form again", ("a new finding is a stall",)),
    ("decide", 64, "code", "Decide", ("question · rework · checks, then move",)),
    ("commit", 64, "code", "Commit and push", ("`<stage> → <next>`",)),
    (
        "hand",
        80,
        "code",
        "Hand over at a gate",
        ("the description from the story;", "ready for review"),
    ),
)
HEIGHT = 104 + sum(step[1] for step in STEPS) + GAP * (len(STEPS) - 1) + 40


def add_steps(d: Diagram) -> dict[str, Node]:
    """The column of steps, with the flow down it."""
    nodes: dict[str, Node] = {}
    y = 104
    for key, height, kind, title, body in STEPS:
        nodes[key] = d.add(Node(X, y, W, height, kind=kind, title=title, lines=body))
        y += height + GAP
    keys = list(nodes)
    for a, b in zip(keys, keys[1:], strict=False):
        # The line starts inside the box above (hidden under it), so the visible 16 px gap
        # still leaves a straight last leg long enough for the arrowhead.
        d.add(Edge([(nodes[a].cx, nodes[a].y2 - 8), nodes[b].top]))
    return nodes


def add_stores(d: Diagram, n: dict[str, Node]) -> None:
    """The pull request, Git, the run record and the failure, with the lines to them."""
    prep, rec, clear, commit, hand = n["prep"], n["rec"], n["clear"], n["commit"], n["hand"]
    gh = d.add(Node(STORE_X, 104, STORE_W, 64, kind="store", title="Pull request"))
    gh.lines = "draft, then ready"
    git = d.add(Node(STORE_X, 176, STORE_W, 80, kind="store", shape="cylinder", title="Git"))
    git.lines = "the branch, `origin`"
    runrec = d.add(Node(STORE_X, 440, STORE_W, 64, kind="store", shape="document"))
    runrec.title, runrec.lines = "Run record", "path, started"
    failure = d.add(Node(STORE_X, n["verify"].cy - 40, STORE_W, 80, kind="stall", shape="pill"))
    failure.title, failure.lines = "Failure", ("counted, retried;", "the factory's fault")
    d.add(
        Edge(
            route(prep.port("left", -16), gh.port("right", 0), "h"),
            kind="plain",
            label=("open the", "draft"),
            side="below",
        ),
        Edge(
            route(prep.port("left", 36), git.port("right", -28), "h"),
            kind="plain",
            label=("checkout,", "merge"),
            side="below",
        ),
        Edge(
            route(rec.left, runrec.port("right", -12), "hvh", via=268),
            kind="plain",
            label="write",
            segment=0,
        ),
        Edge(
            route(clear.left, runrec.port("right", 16), "hvh", via=268),
            kind="plain",
            label="remove",
            segment=0,
        ),
        Edge(
            route(n["verify"].left, failure.port("right", 0), "h"),
            kind="stall",
            label=("agent left", "the branch"),
        ),
    )
    # Two thin lines back up the left margin, the pull request's outside Git's, so none cross.
    git_rail, gh_rail = STORE_X - 24, STORE_X - 40
    d.add(
        Edge(
            [commit.left, (git_rail, commit.cy), (git_rail, git.cy), git.left],
            kind="plain",
            label="push",
            segment=0,
            pos=190,
        ),
        Edge(
            [hand.left, (gh_rail, hand.cy), (gh_rail, gh.cy), gh.left],
            kind="plain",
            label="description, ready",
            segment=0,
            pos=190,
        ),
    )


def add_exits(d: Diagram, n: dict[str, Node]) -> None:
    """The stall and the question on the right; the four stall lines merge on one rail."""
    prep, outcome, form2, decide = n["prep"], n["outcome"], n["form2"], n["decide"]
    stall = d.add(Node(SIDE_X, form2.cy - 48, SIDE_W, 96, kind="stall", title="Stall"))
    stall.lines = ("attempts + 1, partial", "work committed, a note", "on the pull request")
    question = d.add(
        Node(SIDE_X, decide.cy - 16, SIDE_W, 64, kind="ask", shape="pill", title="Question")
    )
    question.lines = "`blocked: question`"
    entry = form2.cy  # where the rail enters the stall
    into = stall.port("left", entry - stall.cy)
    d.add(
        Edge(
            [prep.right, (RAIL, prep.cy), (RAIL, entry)],
            kind="stall",
            label=("cannot fast-forward", "or merge"),
            segment=1,
            pos=208,
            arrow="none",
        ),
        Edge(
            route(outcome.right, (RAIL, outcome.cy), "h"),
            kind="stall",
            label="not kept",
            arrow="none",
        ),
        Edge(route(form2.right, into, "h"), kind="stall", label="form broke", pos=596),
        Edge(
            [decide.port("right", -12), (RAIL, decide.cy - 12), (RAIL, entry)],
            kind="stall",
            label="a check red",
            segment=0,
            arrow="none",
        ),
        Edge(
            route(decide.port("right", 16), question.left, "h"),
            kind="ask",
            label=("question,", "form findings,", "round cap"),
            side="below",
        ),
    )


def add_brackets(d: Diagram, n: dict[str, Node]) -> None:
    """Two brackets on the far right: the steps before the agent and the steps after it."""
    brackets = (
        (n["prep"].y, n["rec"].y2, ("before", "the agent"), 250),
        (n["clear"].y, n["hand"].y2, ("after", "the agent"), 700),
    )
    for top, bottom, label, pos in brackets:
        d.add(
            Edge(
                [(BRACKET - 8, top), (BRACKET, top), (BRACKET, bottom), (BRACKET - 8, bottom)],
                kind="plain",
                arrow="none",
                label=label,
                segment=1,
                side="left",
                pos=pos,
            )
        )
    agent = n["agent"]
    d.add(Text(SIDE_X, agent.cy - 4, ("the only step where", "a model runs"), style="note"))


def build() -> Diagram:
    d = Diagram(
        width=850,
        height=HEIGHT,
        title="The stage protocol",
        subtitle="The agent is one step; every other step is code with one right answer, and every "
        "exit is a stall, a question or a failure.",
        description="The steps of one stage run in v1, top to bottom: the factory's code prepares "
        "the branch (the first stage creates it and opens a draft pull request, a later one "
        "fast-forwards and merges main), validates the form, composes the task and writes the "
        "run record under .git. The agent, one box and the only model step, runs claude -p in "
        "its lane and ends with an outcome and an entry. The factory then removes the run record, "
        "verifies that the agent is still on the work item's branch (if not, a failure, counted "
        "and retried, the factory's fault), undoes every path changed outside the lane, restores "
        "the state and the log, reads the "
        "outcome, validates the form again and decides, then commits and pushes and hands over at "
        "a gate, all of it the factory's code. Git, the pull request and the run record sit on the "
        "left, written by the steps "
        "beside them. On the right, four lines end in a stall: the branch cannot be "
        "fast-forwarded or merged, the outcome is not kept, the form broke, a check is red. A "
        "question leaves the decision on its own.",
        legend=Legend(
            nodes={
                "code": "the factory's code",
                "agent": "the agent",
                "store": "store",
                "stall": "stall or failure",
                "ask": "question",
            },
            x=SIDE_X,
            y=HEIGHT - 40 - 24 * 5 - 4,
            hide=("edge:flow", "edge:plain", "edge:stall", "edge:ask"),
        ),
    )
    nodes = add_steps(d)
    add_stores(d, nodes)
    add_exits(d, nodes)
    add_brackets(d, nodes)
    return d


if __name__ == "__main__":
    save(build(), __file__)
