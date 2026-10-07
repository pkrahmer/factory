"""Figure 2-2: the factory's concepts in five clusters and the relations between them.

The description in concept_map.md is authoritative. Five clusters on a canvas 848 px wide: the
work and the human's side on the right, the line and the agent run on the left, and the control
loop as a strip along the bottom, read from right to left. One relation is left out of the
picture: the stage agent works on the story.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, save  # noqa: E402

W, H = 848, 1256

# Column left edges: the line's two columns, then the work's chain; the work's right column
# (feature acceptance, branch, pull request, watcher) is centered on X_D.
X_A, X_B, X_C = 56, 264, 440
X_D = 700  # center of the right column
LANE = 792  # the watcher's line up to the project runs here, right of every node

# Row centers: the work and the line (R0-R3), the agent run and the human's side (R4-R5),
# the control loop (R6-R7).
R0, R1, R2, R3, R4, R5, R6, R7 = 176, 296, 416, 536, 712, 832, 1000, 1120
CHANNEL = 916  # the dispatcher's line to the pull request, between the human's side and the loop


def box(x: int, cy: int, w: int, kind: str, title: str, *body: str) -> Node:
    """A node with a title and two or three body lines, centered on `cy`."""
    h = 80 if len(body) < 3 else 96
    return Node(x, cy - h // 2, w, h, kind=kind, title=title, lines=body)


def build() -> Diagram:
    d = Diagram(
        width=W,
        height=H,
        title="The concepts and how they relate",
        subtitle="The factory's vocabulary in five clusters: the work, the line, the agent run, "
        "the control loop and the human's side.",
        description="A map of the factory's concepts in five clusters. The work: a project "
        "contains features, a feature contains stories and has a feature acceptance when "
        "complete, a story has a log and lives on a branch, which is proposed by a pull request. "
        "The line: the project carries the stage table, which defines stages; a story is in a "
        "stage; a stage names a role and moves forward only after its checks; a role may write "
        "its lane and is defined by its instructions. The agent run: a task is given to the stage "
        "agent, which plays the role and ends with an outcome. The control loop: a tick runs the "
        "watcher, which reads the project and the pull request and yields an event; the event is "
        "handled by the dispatcher, which starts the stage agent, records a run record, applies "
        "the outcome and opens, posts to and hands over the pull request. The human writes and "
        "promotes stories and merges, closes or comments on the pull request.",
        legend=Legend(
            nodes={
                "concept": "data: project files",
                "agent": "the model: agent run",
                "code": "code: control loop",
                "human": "the human",
                "store": "stored state",
            },
            edges={"flow": "an action", "plain": "a structural relation"},
        ),
    )
    d.add(
        Group(424, 104, 384, 496, caption="The work", kind="concept"),
        Group(40, 232, 352, 368, caption="The line", kind="concept"),
        Group(40, 632, 352, 256, caption="The agent run", kind="agent"),
        Group(424, 760, 384, 128, caption="The human's side", kind="human"),
        Group(248, 928, 560, 248, caption="The control loop", kind="code"),
    )

    # The work: the chain in the middle column, feature acceptance and the branch on its right.
    project = d.add(box(X_C, R0, 112, "concept", "Project", "the repository", "being built"))
    feature = d.add(box(X_C + 8, R1, 96, "concept", "Feature", "goal, scope,", "out of scope"))
    story = d.add(box(X_C, R2, 112, "concept", "Story", "specification ·", "state · memory"))
    log = d.add(box(X_C, R3, 112, "concept", "Log", "append-only,", "numbered"))
    accept = d.add(
        box(608, R1, 168, "concept", "Feature acceptance", "judges a complete", "feature")
    )
    branch = d.add(
        box(X_D - 60, R2, 120, "concept", "Branch", "one per work", "item, until", "the merge")
    )

    # The line: the stage table, the stage and the role in one column, the rest to its left.
    table = d.add(box(X_B, R1, 112, "concept", "Stage table", "the factory's", "program"))
    stage = d.add(box(X_B, R2, 112, "concept", "Stage", "role · next ·", "checks · caps"))
    role = d.add(
        box(X_B, R3, 112, "concept", "Role", "instructions ·", "model · tools ·", "budget")
    )
    check = d.add(box(X_A, R2, 128, "concept", "Check", "a control-surface", "command"))
    lane = d.add(box(X_A, R3, 128, "concept", "Lane", "the paths a role", "may write"))

    # The agent run, below the line.
    task = d.add(box(X_A, R4, 128, "agent", "Task", "the facts", "of this run"))
    instructions = d.add(
        box(X_B, R4, 112, "agent", "Instructions", "rules · role ·", "stage · project", "guide")
    )
    agent = d.add(
        box(X_A, R5, 144, "agent", "Stage agent", "one role, one stage,", "one work item")
    )
    outcome = d.add(box(X_B, R5, 112, "agent", "Outcome", "decision +", "log entry"))

    # The human's side, below the work.
    human = d.add(box(X_C, R5, 112, "human", "The human", "intent and", "acceptance"))
    request = d.add(box(X_D - 60, R5, 120, "store", "Pull request", "merge · close ·", "comment"))

    # The control loop, from the watcher on the right to the dispatcher on the left.
    dispatcher = d.add(box(X_B, R6, 112, "code", "Dispatcher", "a handler", "per event"))
    event = d.add(box(456, R6, 112, "code", "Event", "first match", "wins"))
    watcher = d.add(box(X_D - 60, R6, 120, "code", "Watcher", "snapshot →", "one event"))
    run = d.add(box(X_B, R7, 128, "code", "Run record", "which work item,", "since when"))
    tick = d.add(box(X_D - 60, R7, 120, "code", "Tick", "wakes on", "a schedule"))

    d.add(
        # The work.
        Edge([project.bottom, feature.top], kind="plain", label="contains"),
        Edge([feature.bottom, story.top], kind="plain", label="contains"),
        Edge([story.bottom, log.top], kind="plain", label="has"),
        Edge([feature.right, accept.left], kind="plain", label=("when", "complete")),
        Edge([story.port("right", -12), branch.port("left", -12)], kind="plain", label="lives on"),
        Edge(
            [branch.bottom, request.top],
            kind="plain",
            label="proposed by",
            pos=696,
        ),
        # The work and the line.
        Edge(
            [project.left, (table.cx, project.cy), table.top],
            kind="plain",
            label="carries",
            segment=0,
        ),
        Edge([story.port("left", -12), stage.port("right", -12)], kind="plain", label="is in"),
        # The line.
        Edge([table.bottom, stage.top], kind="plain", label="defines"),
        Edge([stage.bottom, role.top], kind="plain", label="names"),
        Edge([stage.left, check.right], kind="plain", label=("moves", "forward", "only after")),
        Edge([role.port("left", -12), lane.port("right", -12)], kind="plain", label="may write"),
        Edge([role.bottom, instructions.top], kind="plain", label="defined by", pos=616),
        Edge(
            [
                agent.port("right", -16),
                (232, agent.cy - 16),
                (232, role.cy + 12),
                role.port("left", 12),
            ],
            kind="plain",
            label="plays",
            segment=1,
            pos=616,
        ),
        # The agent run.
        Edge([task.port("bottom", 8), agent.top], label="given to"),
        Edge([agent.port("right", 16), outcome.port("left", 16)], label="ends with"),
        # The human.
        Edge(
            [
                human.left,
                (408, human.cy),
                (408, story.cy + 12),
                story.port("left", 12),
            ],
            label=("writes ·", "promotes"),
            segment=1,
            pos=700,
        ),
        Edge([human.right, request.left], label=("merges ·", "closes ·", "comments")),
        # The control loop.
        Edge([tick.top, watcher.bottom], label="runs"),
        Edge([watcher.left, event.right], label="yields"),
        Edge([event.port("left", 16), dispatcher.port("right", 16)], label="handled by"),
        Edge([dispatcher.port("bottom", 8), run.top], label="records"),
        Edge(
            [dispatcher.left, (agent.cx, dispatcher.cy), agent.bottom],
            label="starts",
        ),
        Edge([outcome.bottom, dispatcher.top], label="applied by", pos=908),
        Edge(
            [
                dispatcher.port("right", -16),
                (400, dispatcher.cy - 16),
                (400, CHANNEL),
                (request.cx - 16, CHANNEL),
                request.port("bottom", -16),
            ],
            label="opens · posts · hands over",
            segment=2,
        ),
        Edge(
            [watcher.port("top", 16), request.port("bottom", 16)],
            kind="plain",
            label="reads",
        ),
        Edge(
            [
                watcher.right,
                (LANE, watcher.cy),
                (LANE, project.cy),
                project.right,
            ],
            kind="plain",
            label="reads",
            segment=2,
        ),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
