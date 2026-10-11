# The Miro board

The factory's core concepts are worked out together on one Miro board, step by step, instead of in a book: [Factory – Kernkonzepte](https://miro.com/app/board/uXjVEb-tD-A=/). The board is in German; this file is the note a later session needs to continue it.

## The rules of the board

The earlier attempts (the reference book under `docs/reference/`, a second session extracting the essentials) grew past 500 pages, because every pass detailed the ideas of the one before. The board's rules exist to stop that:

1. At most seven core concepts. One comes in, one goes out.
2. One concept: one frame, one picture, at most five notes.
3. Details go to the parking lot (*Parkplatz*), not into the picture.
4. We go deeper only together, one concept per step.
5. Every step ends with a question to the humans, not with more content.

## What is on it

- *Spielregeln*: the five rules above.
- *1. Die Factory auf einen Blick*: the human, the repository, the pull request, tick, watcher, dispatcher and the stage agent as one Mermaid diagram (after figure 1-1 of the reference), and three statements.
- *2. Die 7 Kernkonzepte*: a table of the seven candidates with one sentence each, the existing diagram that shows it, and a status (*Kandidat*, *Verstanden*, *Justiert*, *Verworfen*).
- *Offene Fragen*: the questions the current step ends with.
- *Parkplatz*: what is deliberately not worked out now.
- *Bestand*: the ten diagrams of `docs/diagrams/`, loaded from `main`, as material to look things up in.

## How a step works

The humans change, move or comment on the board and then say „schau drauf“ in the chat. Claude reads the comments and the changed areas, answers in the comment threads, and does the next step: one concept gets its own frame, or the table changes. Nothing is added that the step did not ask for.

The Miro MCP allows a limited number of calls, so a step should batch its board changes into few calls: one `canvas_update_from_svg` per step where possible, images by public URL in the same call instead of uploading them one by one.
