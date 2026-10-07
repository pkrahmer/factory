"""Figure 3-1: the parts of Figure 1-1, each tagged with the principles that govern it.

Renders `principles_map.svg` beside this script; `principles_map.md` describes it.
The figure is a narrow stack: the human between the pull request and the repository, the factory's
code as one row of three below them, the stage agent under the dispatcher, and the band for the
factory itself at the foot.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Lane, Legend, Node, Text, route, save  # noqa: E402

WIDTH, HEIGHT = 848, 912
TOP_CY = 208  # the middle line shared by the pull request, the human and the repository
PR_X, PR_W = 40, 224  # the pull request, left
HUMAN_X, HUMAN_W = 336, 176  # the human, between the two places
REPO_X, REPO_W = 584, 224  # the repository, right
BUS_Y = 312  # the channel under the places, for the dispatcher's write to the pull request
GROUP_X, GROUP_Y, GROUP_W, GROUP_H = 40, 344, 768, 168  # the factory's code, 24 px inside
CODE_X = (64, 320, 576)  # tick, watcher, dispatcher
CODE_W = 208  # every code node
CODE_Y, CODE_H = 376, 112  # the code row
AGENT_Y, AGENT_H = 560, 96  # the stage agent, under the dispatcher
LANE_Y, LANE_H = 696, 160  # the band for the factory itself
FOOT_X, FOOT_Y, FOOT_W = (208, 408, 608), 720, 176  # its row of three, bottoms aligned

BANNER = "P1 Sort every step: amber the human, blue a model, green code"
BANNER_SPANS = {
    "P1 Sort every step:": '<tspan class="tx-bold">P1 Sort every step:</tspan>',
    "amber the human": '<tspan class="k-human b">amber the human</tspan>',
    "blue a model": '<tspan class="k-agent b">blue a model</tspan>',
    "green code": '<tspan class="k-code b">green code</tspan>',
}
# The principle tags are this figure's content, so they are set larger than the kit's 10.5 px.
STYLE = "text.tag { font-size: 12px; letter-spacing: 0.06em; }\n.b { font-weight: 600; }"


class _Figure(Diagram):
    """The kit's diagram with larger tags and the P1 banner's color words in their colors."""

    def to_svg(self) -> str:
        styled = BANNER
        for plain, span in BANNER_SPANS.items():
            styled = styled.replace(plain, span)
        svg = super().to_svg().replace("<style>\n", f"<style>\n{STYLE}\n", 1)
        return svg.replace(f">{BANNER}<", f">{styled}<", 1)


def _upper(d: Diagram) -> dict[str, Node]:
    """The parts of Figure 1-1: the two places and the human, the factory's code, the agent."""
    nodes = {
        "pr": Node(PR_X, TOP_CY - 48, PR_W, 96, kind="store", tag="P4 · P9", shape="document"),
        "human": Node(HUMAN_X, TOP_CY - 56, HUMAN_W, 112, kind="human", tag="P3 · P4"),
        "repo": Node(REPO_X, TOP_CY - 72, REPO_W, 144, kind="store", tag="P2 · P6 · P8"),
        "tick": Node(CODE_X[0], CODE_Y, CODE_W, CODE_H, kind="code", tag="P13"),
        "watcher": Node(CODE_X[1], CODE_Y, CODE_W, CODE_H, kind="code", tag="P5"),
        "dispatcher": Node(
            CODE_X[2], CODE_Y, CODE_W, CODE_H, kind="code", tag="P10 · P11 · P12 · P14"
        ),
        "agent": Node(CODE_X[2], AGENT_Y, CODE_W, AGENT_H, kind="agent", tag="P7 · P9"),
    }
    nodes["repo"].shape = "cylinder"
    texts = {
        "pr": ("Pull request", ("the human's channel", "where questions go")),
        "human": ("The human", ("starts and accepts", "acts in two places")),
        "repo": (
            "Repository",
            ("the only truth", "the story is the memory", "specified down to", "the failing side"),
        ),
        "tick": ("Tick", ("spends on events,", "not on time")),
        "watcher": ("Watcher", ("lowest identifier first;", "work in flight bounded")),
        "dispatcher": ("Dispatcher", ("enforces · observes", "stops on the unknown", "recovers")),
        "agent": ("Stage agent", ("does not judge its own work", "asks instead of guessing")),
    }
    for name, (title, lines) in texts.items():
        nodes[name].title, nodes[name].lines = title, lines
    d.add(Group(GROUP_X, GROUP_Y, GROUP_W, GROUP_H, caption="The factory's code"))
    for node in nodes.values():
        d.add(node)
    return nodes


def _edges(d: Diagram, n: dict[str, Node]) -> None:
    """The connections of Figure 1-1, without labels: they only orient the reader."""
    human, pr, repo, dispatcher, agent = n["human"], n["pr"], n["repo"], n["dispatcher"], n["agent"]
    d.add(
        Edge(route(human.left, pr.right, "h")),
        Edge(route(human.right, repo.left, "h")),
        Edge(route(n["tick"].right, n["watcher"].left, "h")),
        Edge(route(n["watcher"].right, dispatcher.left, "h")),
        Edge(route(dispatcher.port("bottom", -16), agent.port("top", -16), "v")),
        Edge(route(agent.port("top", 16), dispatcher.port("bottom", 16), "v")),
        # The dispatcher's two writes: straight up to the repository, round under the human to
        # the pull request.
        Edge(route(dispatcher.port("top", 24), repo.port("bottom", 8), "v")),
        Edge(route(dispatcher.port("top", -24), pr.bottom, "vhv", via=BUS_Y)),
    )


def _factory_itself(d: Diagram) -> None:
    """The band below: what belongs to the factory as a whole, not to one part."""
    d.add(Lane(LANE_Y, LANE_H, "The factory itself", note="belongs to the whole", head=144))
    contract = Node(FOOT_X[0], FOOT_Y, FOOT_W, 96, kind="concept", tag="P15")
    contract.title = "Project contract"
    contract.lines = ("control surface ·", "lanes · project guide")
    # The cylinder rises 16 px above the others so that its text lines up with theirs.
    records = Node(FOOT_X[1], FOOT_Y - 16, FOOT_W, 112, kind="code", tag="P16", shape="cylinder")
    records.title, records.lines = "Cost records", "every agent run measured"
    decisions = Node(FOOT_X[2], FOOT_Y, FOOT_W, 96, kind="concept", tag="P17", shape="document")
    decisions.title, decisions.lines = "Decision log", ("why, and what", "was rejected")
    d.add(contract, records, decisions)


def build() -> Diagram:
    d = _Figure(
        width=WIDTH,
        height=HEIGHT,
        title="Where the principles act",
        subtitle="The parts of the factory from Figure 1-1, each tagged with its principles; "
        "below, what belongs to the whole.",
        description="The parts of the factory from Figure 1-1, each labeled with the "
        "principles that govern it. The human (P3, P4) starts and accepts, and acts in two "
        "places. The pull request (P4, P9) is the human's channel and where questions go. The "
        "repository (P2, P6, P8) is the only truth; the story in it is the memory and is "
        "specified down to the failing side. The factory's code is a group of three: the tick "
        "(P13) spends on events, not on time; the watcher (P5) takes the lowest identifier "
        "first and keeps the work in flight bounded; the dispatcher (P10, P11, P12, P14) "
        "enforces, observes, stops on the unknown and recovers. The stage agent below the "
        "dispatcher (P7, P9) does not judge its own work and asks instead of guessing. "
        "Unlabeled arrows orient the reader as in Figure 1-1: the human to the pull request and "
        "the repository, tick to watcher to dispatcher, dispatcher to agent and back, and the "
        "dispatcher to both places. A band below holds what belongs to the factory itself: the "
        "project contract (P15: control surface, lanes, project guide), the cost records (P16: "
        "every agent run measured) and the decision log (P17: why, and what was rejected). P1, "
        "sort every step, governs the whole picture: the boxes' colors are its three kinds of "
        "work, amber the human, blue a model, green code.",
        legend=Legend(
            nodes={
                "agent": "a model",
                "human": "the human",
                "code": "code",
                "concept": "concept",
                "store": "stored state",
            },
            hide=("edge:flow",),
        ),
    )
    d.add(Text(40, 104, BANNER))
    _edges(d, _upper(d))
    _factory_itself(d)
    return d


if __name__ == "__main__":
    save(build(), __file__)
