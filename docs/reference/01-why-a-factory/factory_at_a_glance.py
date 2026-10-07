"""Figure 1-1: the factory at a glance; see factory_at_a_glance.md for what it shows."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, route, save  # noqa: E402

# Stacked, top to bottom: the human; the two places side by side; the factory's code in a row;
# the stage agent below the code, outside its group.
HUMAN_X, HUMAN_W, HUMAN_Y, HUMAN_H = 296, 256, 104, 88
PR_X, REPO_X, PLACE_W, PLACE_Y, PLACE_H = 40, 576, 240, 256, 120
GROUP_X, GROUP_Y, GROUP_W, GROUP_H = 40, 512, 770, 160
TICK_X, WATCHER_X, DISPATCHER_X = 64, 336, 608  # the code's row, left to right
CODE_Y, CODE_W, CODE_H = 544, 176, 112
AGENT_X, AGENT_Y, AGENT_W, AGENT_H = 248, 704, 240, 112
READS_Y, WRITES_Y, REPO_READS_Y = 480, 448, 416  # the legs of the lines up to the two places
LABELS_X = 560  # where the labels of the long legs sit


def _node(d: Diagram, node: Node, *lines: str) -> Node:
    node.lines = lines
    return d.add(node)


def _nodes(d: Diagram) -> dict[str, Node]:
    nodes = {
        "human": _node(
            d,
            Node(HUMAN_X, HUMAN_Y, HUMAN_W, HUMAN_H, "human", "The human"),
            "writes stories · decides what starts",
            "answers questions · merges or closes",
        ),
        "pr": _node(
            d,
            Node(PR_X, PLACE_Y, PLACE_W, PLACE_H, "store", "Pull request", shape="document"),
            "one per story",
            "questions and answers",
            "the result, waiting",
        ),
        "repo": _node(
            d,
            Node(REPO_X, PLACE_Y, PLACE_W, PLACE_H, "store", "Repository", shape="cylinder"),
            "features and stories",
            "code, tests, docs",
            "`main` and one branch per story",
        ),
    }
    d.add(Group(GROUP_X, GROUP_Y, GROUP_W, GROUP_H, caption="The factory's code", kind="code"))
    nodes["tick"] = _node(
        d,
        Node(TICK_X, CODE_Y, CODE_W, CODE_H, "code", "Tick"),
        "on a schedule:",
        "seconds after activity,",
        "up to 2 minutes if quiet;",
        "fetches, then evaluates",
    )
    nodes["watcher"] = _node(
        d,
        Node(WATCHER_X, CODE_Y, CODE_W, CODE_H, "code", "Watcher"),
        "repository and",
        "pull request state",
        "→ the one next event",
    )
    nodes["dispatcher"] = _node(
        d,
        Node(DISPATCHER_X, CODE_Y, CODE_W, CODE_H, "code", "Dispatcher"),
        "handles the event:",
        "branches, checks,",
        "commits, pushes, posts",
    )
    nodes["agent"] = _node(
        d,
        Node(AGENT_X, AGENT_Y, AGENT_W, AGENT_H, "agent", "Stage agent"),
        "one stage of one story",
        "reads the story",
        "writes its lane",
        "ends with an outcome",
    )
    return nodes


def _human_edges(d: Diagram, n: dict[str, Node]) -> None:
    human, pr, repo = n["human"], n["pr"], n["repo"]
    d.add(
        Edge(route(human.left, pr.top, "hv"), label=("answers ·", "merges · closes"), segment=1),
        Edge(
            route(human.right, repo.top, "hv"),
            label=("writes and", "starts stories"),
            segment=1,
        ),
        Edge(route(pr.right, repo.left, "h"), kind="dashed", label="a merge lands on `main`"),
    )


def _code_edges(d: Diagram, n: dict[str, Node]) -> None:
    pr, repo = n["pr"], n["repo"]
    tick, watcher, dispatcher, agent = n["tick"], n["watcher"], n["dispatcher"], n["agent"]
    d.add(
        # One tick, one event.
        Edge(route(tick.right, watcher.left, "h"), label="evaluate"),
        Edge(route(watcher.right, dispatcher.left, "h"), label=("one", "event")),
        # Reads and writes, up to the two places. Only the watcher's read of the repository
        # crosses the dispatcher's line to the pull request.
        Edge(
            route(watcher.port("top", -24), pr.port("bottom", -24), "vhv", via=READS_Y),
            kind="plain",
            label="reads",
            pos=270,
        ),
        Edge(
            route(dispatcher.port("top", -24), pr.port("bottom", 24), "vhv", via=WRITES_Y),
            label="opens · comments · marks ready",
            pos=LABELS_X,
        ),
        Edge(
            route(watcher.port("top", 24), repo.port("bottom", -64), "vhv", via=REPO_READS_Y),
            kind="plain",
            label="reads",
            pos=LABELS_X - 24,
        ),
        Edge(
            route(dispatcher.port("top", 24), repo.port("bottom", 24), "v"),
            label="commits, pushes",
            pos=448,
        ),
        # The stage agent: called by the code, outside it.
        Edge(
            route(dispatcher.port("bottom", -24), agent.port("right", -16), "vh"),
            label=("starts,", "with a task"),
            pos=LABELS_X,
        ),
        Edge(
            route(agent.port("right", 16), dispatcher.port("bottom", 24), "hv"),
            label=("outcome +", "log entry"),
            side="below",
            pos=LABELS_X,
        ),
    )


def build() -> Diagram:
    d = Diagram(
        width=850,
        height=912,
        title="The factory at a glance",
        subtitle="The human works only through two places; the factory's code reads both and "
        "starts a stage agent.",
        description="The human, at the top, works only through two places below: the "
        "repository, where they write and start stories, and the pull request, where they answer "
        "questions and merge or close. Below them, the factory's code runs on a schedule: a "
        "tick wakes it, the watcher reads both places and names the one next event, and the "
        "dispatcher handles that event, committing and pushing to the repository and opening, "
        "commenting on and marking ready the pull request. When a stage is due, the dispatcher "
        "starts a stage agent, the only place a model runs, which hands back an outcome and a log "
        "entry. A merge of the pull request lands on main. The human and the agents never talk "
        "directly.",
        legend=Legend(
            nodes={"human": "the human", "agent": "agent: a model runs"},
            edges={"flow": "acts or hands over", "plain": "reads", "dashed": "asynchronous"},
        ),
    )
    nodes = _nodes(d)
    _human_edges(d, nodes)
    _code_edges(d, nodes)
    return d


if __name__ == "__main__":
    save(build(), __file__)
