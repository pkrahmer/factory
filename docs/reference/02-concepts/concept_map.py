"""Figure 2-2: the factory's concepts in five clusters and the relations between them.

The description in concept_map.md is authoritative. Five clusters in three bands, left to right:
the work with the human's side below it, the line with the agent run below it, and the control
loop. Two relations are left out of the picture: the stage agent works on the story, and the
watcher reads the pull request.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagram_kit import Diagram, Edge, Group, Legend, Node, save  # noqa: E402

W, H = 1200, 992
NODE_H = 80

# Column left edges and widths: the work's side column, its main column, the line's two
# columns (the agent run below them), and the control loop.
C0, C0W = 56, 168
C1, C2, C3, CW = 296, 504, 744, 144
C4, C4W = 960, 160

# Row tops: the work and the line (R0-R3), the human's side and the agent run (R4-R5).
R0, R1, R2, R3, R4, R5 = 136, 264, 392, 520, 680, 808
LOOP = (R0, 320, 504, R4)  # tick, watcher, event, dispatcher
CHANNEL = 936  # the bottom channel of the line from the dispatcher to the pull request


def box(x: int, y: int, w: int, kind: str, title: str, *body: str) -> Node:
    """A node with a title and two body lines."""
    return Node(x, y, w, NODE_H, kind=kind, title=title, lines=body)


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
        "watcher, which reads the project and yields an event; the event is handled by the "
        "dispatcher, which starts the stage agent, records a run record, applies the outcome and "
        "opens, posts to and hands over the pull request. The human writes and promotes stories "
        "and merges, closes or comments on the pull request.",
        legend=Legend(
            nodes={
                "concept": "data: files in the project",
                "agent": "the model: the agent run",
                "code": "code: the control loop",
                "human": "the human",
                "store": "stored state",
            },
            edges={"flow": "an action", "plain": "a structural relation"},
        ),
    )
    d.add(
        Group(40, 104, 416, 512, caption="The work", kind="concept"),
        Group(40, 648, 416, 144, caption="The human's side", kind="human"),
        Group(488, 232, 416, 384, caption="The line", kind="concept"),
        Group(488, 648, 416, 256, caption="The agent run", kind="agent"),
        Group(944, 104, 216, 800, caption="The control loop", kind="code"),
    )

    # The work: the main column, with feature acceptance and the branch on the left.
    project = d.add(box(C1, R0, CW, "concept", "Project", "the repository", "being built"))
    feature = d.add(box(C1, R1, CW, "concept", "Feature", "goal, scope,", "out of scope"))
    story = d.add(box(C1, R2, CW, "concept", "Story", "specification ·", "state · memory"))
    log = d.add(box(C1, R3, CW, "concept", "Log", "append-only,", "numbered"))
    accept = d.add(
        box(C0, R1, C0W, "concept", "Feature acceptance", "judges a complete", "feature")
    )
    branch = d.add(box(C0, R2, C0W, "concept", "Branch", "one per work item,", "until the merge"))

    # The human's side, below the work.
    request = d.add(box(C0, R4, C0W, "store", "Pull request", "merge · close ·", "comment"))
    human = d.add(box(C1, R4, CW, "human", "The human", "intent and", "acceptance"))

    # The line.
    table = d.add(box(C2, R1, CW, "concept", "Stage table", "the factory's", "program"))
    stage = d.add(box(C2, R2, CW, "concept", "Stage", "role · next ·", "checks · caps"))
    check = d.add(box(C3, R2, CW, "concept", "Check", "a control-surface", "command"))
    role = d.add(box(C2, R3, CW, "concept", "Role", "instructions · model ·", "tools · budget"))
    lane = d.add(box(C3, R3, CW, "concept", "Lane", "the paths a role", "may write"))

    # The agent run, below the line.
    instructions = d.add(
        box(C2, R4, CW, "agent", "Instructions", "rules · role · stage ·", "project guide")
    )
    agent = d.add(box(C3, R4, CW, "agent", "Stage agent", "one role, one stage,", "one work item"))
    task = d.add(box(C2, R5, CW, "agent", "Task", "the facts", "of this run"))
    outcome = d.add(box(C3, R5, CW, "agent", "Outcome", "decision +", "log entry"))

    # The control loop.
    tick = d.add(box(C4, LOOP[0], C4W, "code", "Tick", "wakes on", "a schedule"))
    watcher = d.add(box(C4, LOOP[1], C4W, "code", "Watcher", "snapshot →", "one event"))
    event = d.add(box(C4, LOOP[2], C4W, "code", "Event", "first match", "wins"))
    dispatcher = d.add(box(C4, LOOP[3], C4W, "code", "Dispatcher", "a handler", "per event"))
    run = d.add(box(C4 + 32, R5, 128, "code", "Run record", "which work item,", "since when"))

    gap0 = (C0 + C0W + C1) / 2  # between the work's two columns
    gap1 = (C3 + CW + C4) / 2  # between the line and the control loop

    d.add(
        # The work.
        Edge([project.bottom, feature.top], kind="plain", label="contains"),
        Edge([feature.bottom, story.top], kind="plain", label="contains"),
        Edge([story.bottom, log.top], kind="plain", label="has"),
        Edge([feature.left, accept.right], kind="plain", label=("when", "complete")),
        Edge([story.port("left", -12), branch.port("right", -12)], kind="plain", label="lives on"),
        Edge(
            [branch.port("bottom", 40), request.port("top", 40)],
            kind="plain",
            label="proposed by",
            side="left",
            pos=500,
        ),
        # The human.
        Edge(
            [
                human.port("left", -16),
                (gap0, human.cy - 16),
                (gap0, story.cy + 12),
                story.port("left", 12),
            ],
            label=("writes ·", "promotes"),
            side="left",
            segment=1,
            pos=552,
        ),
        Edge(
            [human.port("left", 8), request.port("right", 8)],
            label=("merges ·", "closes ·", "comments"),
            side="below",
        ),
        # The work and the line.
        Edge(
            [project.port("right", 12), (table.cx, project.cy + 12), table.top],
            kind="plain",
            label="carries",
            segment=1,
            pos=210,
        ),
        Edge([story.right, stage.left], kind="plain", label="is in"),
        # The line.
        Edge([table.bottom, stage.top], kind="plain", label="defines"),
        Edge([stage.right, check.left], kind="plain", label=("moves forward", "only after")),
        Edge([stage.bottom, role.top], kind="plain", label="names"),
        Edge([role.port("right", -12), lane.port("left", -12)], kind="plain", label="may write"),
        Edge(
            [role.port("bottom", 32), instructions.port("top", 32)],
            kind="plain",
            label="defined by",
            pos=632,
        ),
        Edge(
            [
                agent.port("left", -12),
                (C3 - 32, agent.cy - 12),
                (C3 - 32, role.cy + 12),
                role.port("right", 12),
            ],
            kind="plain",
            label="plays",
            segment=2,
            side="below",
        ),
        # The agent run.
        Edge(
            [
                task.right,
                (C2 + CW + 32, task.cy),
                (C2 + CW + 32, agent.cy + 12),
                agent.port("left", 12),
            ],
            label="given to",
            segment=2,
            side="below",
        ),
        Edge([agent.bottom, outcome.top], label="ends with"),
        # The control loop.
        Edge([tick.bottom, watcher.top], label="runs"),
        Edge([watcher.bottom, event.top], label="yields"),
        Edge([event.bottom, dispatcher.top], label="handled by"),
        Edge([dispatcher.left, agent.right], label="starts"),
        Edge(
            [outcome.right, (dispatcher.x + 16, outcome.cy), dispatcher.port("bottom", -64)],
            label="applied by",
            segment=1,
            pos=784,
        ),
        Edge([dispatcher.port("bottom", 16), run.top], label="records"),
        Edge(
            [
                watcher.left,
                (gap1, watcher.cy),
                (gap1, project.cy - 12),
                project.port("right", -12),
            ],
            kind="plain",
            label="reads",
            segment=2,
            pos=760,
        ),
        Edge(
            [
                dispatcher.right,
                (dispatcher.x2 + 16, dispatcher.cy),
                (dispatcher.x2 + 16, CHANNEL),
                (request.cx, CHANNEL),
                request.bottom,
            ],
            label="opens · posts · hands over",
            segment=2,
            pos=600,
        ),
    )
    return d


if __name__ == "__main__":
    save(build(), __file__)
