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
- *1. Die Factory auf einen Blick*: the human, the repository, the pull request, tick, watcher, dispatcher and the stage agent (after figure 1-1 of the reference), and three statements.
- *2. Die 7 Kernkonzepte*: a table of the seven candidates with one sentence each, the existing diagram that shows it, and a status (*Kandidat*, *Verstanden*, *Justiert*, *Verworfen*).
- *Offene Fragen*: the questions the current step ends with.
- *Parkplatz*: what is deliberately not worked out now.
- *01* to *10*: the ten diagrams of `docs/diagrams/`, one frame each, in English as in the repository.
- *Bestand*: the same ten diagrams as images, from the first step.

Every diagram on the board is built from native Miro shapes, connectors and text, not from an image or a Mermaid widget, so the humans can move, rename, recolour and reconnect them and Claude reads exactly what changed. `docs/diagrams/to_miro.py` made the ten from `draw.py` (`python3 docs/diagrams/to_miro.py 01,02 > out.svg`, then the SVG to `canvas_create_from_svg`). It keeps the boxes, texts, colours and which side an arrow leaves and enters; Miro routes the arrows itself, so a crowded spot (the four ways back into `doing` in 01) may need tidying by hand. From here the board is where the diagrams change; a change worth keeping goes back into `draw.py` by hand, when the humans ask for it.

## How a step works

The humans change, move or comment on the board and then say „schau drauf“ in the chat. Claude reads the comments and the changed areas, answers in the comment threads, and does the next step: one concept gets its own frame, or the table changes. Nothing is added that the step did not ask for.

The Miro MCP allows 500 calls a day, so a step batches its board changes into few calls, three to five in all: read the comments, read only the area that changed, make one `canvas_update_from_svg` with every change in it, and pull in images by public URL in that same call instead of uploading them one by one. No preview, overview search or verifying read unless the step needs it.
