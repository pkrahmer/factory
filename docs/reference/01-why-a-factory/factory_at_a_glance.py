"""Figure 1-1: the factory at a glance; see factory_at_a_glance.md for what it shows."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, route, save  # noqa: E402

# Three columns: the human, the two places (pull request above, repository below), the code.
HUMAN_X, PLACE_X, GROUP_X = 40, 232, 440
TICK_X, WATCHER_X, DISPATCHER_X = 456, 696, 920  # the code's row, left to right
PLACE_W, CODE_W, WATCHER_W = 160, 176, 160
PR_Y, GROUP_Y, ROW_Y, REPO_Y, AGENT_Y = 104, 200, 232, 344, 424
ROW_H = 112
LABELS_X = TICK_X + CODE_W // 2  # the labels of the long reads and writes, above the tick
SPLIT_X = 888  # where the dispatcher's line to the repository turns down
AGENT_LABELS_Y = 392  # the agent's two labels, between the group's outline and the agent


def _node(d: Diagram, node: Node, *lines: str) -> Node:
    node.lines = lines
    return d.add(node)


def _nodes(d: Diagram) -> dict[str, Node]:
    nodes = {
        "pr": _node(
            d,
            Node(PLACE_X, PR_Y, PLACE_W, 96, "store", "Pull request", shape="document"),
            "one per story",
            "questions and answers",
            "the result, waiting",
        ),
        "repo": _node(
            d,
            Node(PLACE_X, REPO_Y, PLACE_W, 144, "store", "Repository", shape="cylinder"),
            "features and stories",
            "code, tests, docs",
            "`main` and one",
            "branch per story",
        ),
        "human": _node(
            d,
            Node(HUMAN_X, ROW_Y, 144, ROW_H, "human", "The human"),
            "writes stories",
            "decides what starts",
            "answers questions",
            "merges or closes",
        ),
    }
    d.add(Group(GROUP_X, GROUP_Y, 672, 160, caption="The factory's code", kind="code"))
    nodes["tick"] = _node(
        d,
        Node(TICK_X, ROW_Y, CODE_W, ROW_H, "code", "Tick"),
        "on a schedule:",
        "seconds after activity,",
        "up to 2 minutes if quiet;",
        "fetches, then evaluates",
    )
    nodes["watcher"] = _node(
        d,
        Node(WATCHER_X, ROW_Y, WATCHER_W, ROW_H, "code", "Watcher"),
        "repository and",
        "pull request state",
        "→ the one next event",
    )
    nodes["dispatcher"] = _node(
        d,
        Node(DISPATCHER_X, ROW_Y, CODE_W, ROW_H, "code", "Dispatcher"),
        "handles the event:",
        "branches, checks,",
        "commits, pushes, posts",
    )
    nodes["agent"] = _node(
        d,
        Node(DISPATCHER_X, AGENT_Y, CODE_W, ROW_H, "agent", "Stage agent"),
        "one stage of one story",
        "reads the story",
        "writes its lane",
        "ends with an outcome",
    )
    return nodes


def _human_edges(d: Diagram, n: dict[str, Node]) -> None:
    human, pr, repo = n["human"], n["pr"], n["repo"]
    d.add(
        Edge(route(human.top, pr.left, "vh"), label=("answers ·", "merges · closes"), segment=1),
        Edge(
            route(human.bottom, repo.left, "vh"),
            label=("writes and", "starts stories"),
            segment=1,
            side="below",
        ),
        Edge(route(pr.bottom, repo.top, "v"), kind="dashed", label=("a merge lands", "on `main`")),
    )


def _code_edges(d: Diagram, n: dict[str, Node]) -> None:
    pr, repo = n["pr"], n["repo"]
    tick, watcher, dispatcher, agent = n["tick"], n["watcher"], n["dispatcher"], n["agent"]
    to_repo = route(dispatcher.port("left", 32), repo.port("right", 24), "hvh", via=SPLIT_X)
    d.add(
        # One tick, one event.
        Edge(route(tick.right, watcher.left, "h"), label="evaluate"),
        Edge(route(watcher.right, dispatcher.left, "h"), label=("one", "event")),
        # Reads and writes, left to the two places, over and under the tick.
        Edge(
            route(dispatcher.top, pr.port("right", -24), "vh"),
            label="opens · comments · marks ready",
            pos=LABELS_X,
        ),
        Edge(
            route(watcher.top, pr.port("right", 24), "vh"),
            kind="plain",
            label="reads",
            pos=LABELS_X,
        ),
        Edge(
            route(watcher.bottom, repo.port("right", -24), "vh"),
            kind="plain",
            label="reads",
            pos=LABELS_X,
        ),
        Edge(to_repo, label="commits, pushes", pos=LABELS_X),
        # The stage agent: called by the code, outside it.
        Edge(
            route(dispatcher.port("bottom", -24), agent.port("top", -24), "v"),
            label=("starts,", "with a task"),
            side="left",
            pos=AGENT_LABELS_Y,
        ),
        Edge(
            route(agent.port("top", 24), dispatcher.port("bottom", 24), "v"),
            label=("outcome +", "log entry"),
            pos=AGENT_LABELS_Y,
        ),
    )


def build() -> Diagram:
    d = Diagram(
        width=1152,
        height=600,
        title="The factory at a glance",
        subtitle="The human works only through the repository and the pull request; the "
        "factory's code reads both, keeps the books and starts a stage agent.",
        description="The human, on the left, works only through two places in the middle: the "
        "repository, where they write and start stories, and the pull request, where they answer "
        "questions and merge or close. On the right, the factory's code runs on a schedule: a "
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
