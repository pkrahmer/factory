# Data behind the reference

Raw data the book's numbers come from, kept because it exists nowhere else. Not part of the book (`_print/book.py` does not pick up this folder).

## `demo-dispatches.jsonl`

The cost records of the demonstration project `pkrahmer/factory-demo-todo` on 2026-10-05, copied on 2026-10-07 from `.git/factory-dispatches.jsonl` in the container's work volume, which the next demonstration run wipes. One JSON object per agent run, as `tick.record` writes it ([chapter 14](../14-runtime/README.md)):

| Key | Meaning |
| :- | :- |
| `time` | when the tick recorded it, after the agent run returned (UTC) |
| `line` | the event that started it, `run <agent> <path> <where>` (v1 calls an event a *line*) |
| `ok` | whether the agent run ended without an error |
| `seconds`, `turns`, `cost` | wall clock, model turns, dollars, summed over a budget resume |
| `input`, `cache_read`, `cache_write`, `output` | tokens |

79 records, $21.07 in all:
- **Run 4**, 16:49:07 to 19:36 UTC, generation 5: the first 59 records, $15.89. Eight stories and three acceptances.
- **After run 4**, on later commits: 20 records, $5.18. F0001-S0005 to S0007 and two more F0001 acceptances, partly on the image built at 20:59:48 UTC.

An agent run killed by a restart has no record, so the file holds what the bill held, not every agent run that started.
