"""Figure 14-1: the machine; see machine.md for what it shows."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, route, save  # noqa: E402

# Top row: the human, GitHub, the model provider. Below, the container: the processes in a column
# on the left, the three stores in a column on the right, a channel between them.
TOP_Y, TOP_H = 104, 96
HUMAN_X, HUMAN_W = 40, 168
GITHUB_X, GITHUB_W = 280, 144
MODEL_X, MODEL_W = 608, 200
GROUP_X, GROUP_Y, GROUP_W, GROUP_H = 40, 256, 770, 576
PROC_X = 64  # the left column
ENTRY_Y, ENTRY_W, ENTRY_H = 288, 256, 112
TICK_Y, TICK_W, TICK_H = 464, 320, 96
ROW_Y, ROW_H = 632, 112  # the checks and the agent, side by side
MAKE_X, MAKE_W = 64, 144
AGENT_X, AGENT_W = 224, 176
STORE_X, STORE_W = 568, 216  # the right column
IMAGE_Y, IMAGE_H = 288, 120
HOME_Y, HOME_H = 472, 136
WORK_Y, WORK_H = 672, 128
MODEL_LINE_X, HOME_LINE_X, WORK_LINE_X = 480, 512, 540  # the verticals in the channel
OVER_Y = 228  # where the line to the model provider turns, above the group


def _node(d: Diagram, node: Node, *lines: str) -> Node:
    node.lines = lines
    return d.add(node)


def _nodes(d: Diagram) -> dict[str, Node]:
    nodes = {
        "human": _node(
            d,
            Node(HUMAN_X, TOP_Y, HUMAN_W, TOP_H, "human", "The human"),
            "`.env`: `REPOS`,",
            "`GH_TOKEN`",
            "logs Claude in once",
        ),
        "github": _node(
            d,
            Node(GITHUB_X, TOP_Y, GITHUB_W, TOP_H, "store", "GitHub", shape="cylinder"),
            "repositories ·",
            "pull requests",
        ),
        "model": _node(
            d,
            Node(MODEL_X, TOP_Y, MODEL_W, TOP_H, "store", "Model provider"),
            "Claude, through",
            "Claude Code",
        ),
    }
    d.add(Group(GROUP_X, GROUP_Y, GROUP_W, GROUP_H, caption="Container `factory`"))
    nodes["entry"] = _node(
        d,
        Node(PROC_X, ENTRY_Y, ENTRY_W, ENTRY_H, "code", "Entrypoint loop", tag="PID 1"),
        "clones, prepares",
        "ticks each repository in turn",
        "paces 2 s, then 15 to 120 s",
    )
    nodes["tick"] = _node(
        d,
        Node(PROC_X, TICK_Y, TICK_W, TICK_H, "code", "Tick", tag="`factory-tick`"),
        "one per repository and pass",
        "lock, preflight, fetch, evaluate, handle",
    )
    nodes["make"] = _node(
        d,
        Node(MAKE_X, ROW_Y, MAKE_W, ROW_H, "code", "Commands", tag="`make`"),
        "`check`, `lint`,",
        "`test`",
    )
    nodes["agent"] = _node(
        d,
        Node(AGENT_X, ROW_Y, AGENT_W, ROW_H, "agent", "Stage agent", tag="`claude -p`"),
        "at most one at a time",
        "in the checkout",
    )
    nodes["image"] = _node(
        d,
        Node(STORE_X, IMAGE_Y, STORE_W, IMAGE_H, "store", "Image"),
        "`/opt/factory`, the",
        "`factory` package, Claude Code,",
        "`uv`, `git`, `gh`, `make`",
        "replaced by a rebuild",
    )
    nodes["home"] = _node(
        d,
        Node(STORE_X, HOME_Y, STORE_W, HOME_H, "store", "Volume `claude-home`", shape="cylinder"),
        "`~/.claude`: login",
        "agents, skills,",
        "`settings.json`",
        "Claude Code's transcripts",
    )
    nodes["work"] = _node(
        d,
        Node(STORE_X, WORK_Y, STORE_W, WORK_H, "store", "Volume `work`", shape="cylinder"),
        "`/work/<repo>`: the checkout",
        "`.git/factory-*`: lock, memo,",
        "stamp, run record, tick log,",
        "cost records",
    )
    return nodes


def _outer_edges(d: Diagram, n: dict[str, Node]) -> None:
    human, github, model = n["human"], n["github"], n["model"]
    tick, agent = n["tick"], n["agent"]
    github_x = tick.right[0] - 32  # the line from the tick to GitHub rises right of the entrypoint
    d.add(
        Edge(
            route(human.port("bottom", -40), (human.cx - 40, GROUP_Y), "v"),
            kind="dashed",
            label="`.env`, login",
        ),
        Edge(
            route(human.right, github.left, "h"),
            label=("merges ·", "comments"),
        ),
        Edge(
            route(
                tick.port("top", github_x - tick.cx),
                github.port("bottom", github_x - github.cx),
                "v",
            ),
            label="fetch · push · `gh`",
            side="left",
            pos=OVER_Y,
        ),
        Edge(
            [
                agent.port("right", -32),
                (MODEL_LINE_X, agent.cy - 32),
                (MODEL_LINE_X, OVER_Y),
                (model.cx - 72, OVER_Y),
                model.port("bottom", -72),
            ],
            label="model calls",
            segment=2,
        ),
    )


def _inner_edges(d: Diagram, n: dict[str, Node]) -> None:
    entry, tick, make, agent = n["entry"], n["tick"], n["make"], n["agent"]
    image, home, work = n["image"], n["home"], n["work"]
    d.add(
        Edge(
            route(entry.port("bottom", -64), tick.port("top", -96 + 0), "v"),
            label="each repository",
        ),
        Edge(
            route(tick.port("bottom", make.cx - tick.cx), make.top, "v"),
            label=("checks,", "reports"),
        ),
        Edge(
            route(tick.port("bottom", agent.cx - tick.cx), agent.top, "v"),
            label=("a `run`", "event"),
        ),
        # The stores.
        Edge(
            route(tick.port("right", 24), work.port("left", -32), "hvh", via=WORK_LINE_X),
            kind="plain",
            label=("commits ·", "state"),
            segment=0,
            pos=428,
        ),
        Edge(
            route(agent.port("right", 40), work.port("left", 40 + agent.cy - work.cy), "h"),
            kind="plain",
            label="writes its lane",
            side="below",
        ),
        Edge(
            route(agent.port("right", 0), home.port("left", 28), "hvh", via=HOME_LINE_X),
            kind="plain",
            label="reads",
            segment=0,
        ),
        Edge(
            route(image.bottom, home.top, "v"),
            kind="dashed",
            label="copied at start",
        ),
    )


def build() -> Diagram:
    d = Diagram(
        width=850,
        height=904,
        title="The machine",
        subtitle="One container, its processes, and where everything it keeps lives.",
        description="The human configures the container once, with a .env file and a one-time "
        "Claude login, and afterwards acts only on GitHub, by merging and commenting. Inside the "
        "container, the entrypoint loop ticks each repository in turn. Each tick, "
        "factory-tick, starts at most one stage agent, claude -p, and then runs the project's "
        "checks with make. The tick fetches from and pushes to GitHub with git and gh, and "
        "reads and writes the checkout and the factory's state files in the work volume. The "
        "agent works in the same checkout and reads its agents, skills, settings and login from "
        "the claude-home volume; its model calls are the only traffic to the model provider. "
        "The image holds the factory's code and the tools, and the entrypoint copies agents, "
        "skills and settings from it into the claude-home volume at start. The image is "
        "replaced by a rebuild; both volumes survive one.",
        legend=Legend(
            edges={"flow": "flow", "plain": "relation", "dashed": "once, at start"},
        ),
    )
    nodes = _nodes(d)
    _outer_edges(d, nodes)
    _inner_edges(d, nodes)
    return d


if __name__ == "__main__":
    save(build(), __file__)
