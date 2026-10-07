# Figure 14-1. The machine

Files: [`machine.svg`](machine.svg) (the figure), [`machine.py`](machine.py) (its generator), this description. Used in [chapter 14](README.md).

## What it shows

v1's machine: one container, its processes, and where everything it keeps lives. The processes form a chain: the entrypoint's loop ticks each repository in turn, and a tick starts at most one stage agent and runs the project's checks. Storage is in three places with different lifetimes: the image (the factory's code and the tools, replaced by a rebuild), the volume `claude-home` (the Claude login, the agents, skills and permissions), and the volume `work` (the checkouts, with the factory's state files under each `.git/`). Two services lie outside: GitHub, which the tick reaches through `git` and `gh`, and the model provider, which only the agent calls. The human configures the container once and otherwise acts on GitHub, except for the stops that reach only the machine's logs ([chapter 14](README.md)).

## Elements

| Id | Kind | Label (tag / title) | Body text | Meaning |
| :- | :- | :- | :- | :- |
| human | human | The human | `.env`: `REPOS`, `GH_TOKEN` · logs Claude in once | Configures the machine; afterward reads its logs and fixes what only reaches them |
| github | store (cylinder) | GitHub | repositories · pull requests | The remote and the human's channel |
| model | store (box) | Model provider | Claude, through Claude Code | Where the agent's model calls go |
| container | group | Container `factory` | (caption) | Encloses everything below except the external services and the human |
| entrypoint | code | PID 1 / Entrypoint loop | clones, prepares · ticks each repository in turn · paces 2 s, then 15 to 120 s | The scheduler |
| tick | code | `factory-tick` / Tick | one per repository and pass · lock, preflight, fetch, evaluate, handle | One wake-up |
| agent | agent | `claude -p` / Stage agent | at most one at a time · in the checkout | The only model |
| make | code | `make` / Commands | `check`, `lint`, `test` | The project's control surface |
| image | store (box) | Image | `/opt/factory`, the `factory` package, Claude Code, `uv`, `git`, `gh`, `make` · replaced by a rebuild | Code and tools |
| home | store (cylinder) | Volume `claude-home` | `~/.claude`: login · agents, skills, `settings.json` · Claude Code's transcripts | Survives a rebuild |
| work | store (cylinder) | Volume `work` | `/work/<repo>`: the checkout · `.git/factory-*`: lock, memo, stamp, run record, tick log, cost records | Survives a rebuild |

## Connections

| From | To | Kind | Label | Meaning |
| :- | :- | :- | :- | :- |
| human | container | dashed | `.env`, login | One-time configuration |
| human | github | flow | merges · comments | The human's only channel while the machine runs |
| entrypoint | tick | flow | each repository | `cd /work/<repo> && factory-tick`, one after another |
| tick | agent | flow | a `run` event | Starts the stage agent |
| tick | make | flow | checks, reports | After the agent |
| tick | work | plain | commits · state | Reads and writes the checkout and `.git/factory-*` |
| agent | work | plain | writes its lane | The agent works in the checkout |
| agent | home | plain | reads | Agent files, skills, settings, login |
| image | home | dashed | copied at start | The entrypoint copies agents, skills and `settings.json` into the volume |
| tick | github | flow | fetch · push · `gh` | Git over HTTPS with the token; pull requests through `gh` |
| agent | model | flow | model calls | The only traffic to the model provider |

## Layout

Canvas 850 × 904 px, top to bottom. The human sits top left, GitHub (a cylinder) beside it toward the middle, and the model provider at the top right. Below, the container is one group filling the width. Inside it, the processes form a column on the left: the entrypoint, the tick below it, and below the tick the commands (left) and the stage agent (right) side by side. The three stores form a column on the right: the image, `claude-home`, `work`, top to bottom, with the dashed "copied at start" line from the image down into `claude-home`. The tick's and the agent's lines to the stores run horizontally across the channel between the two columns; two of them cross once, at right angles. The tick's line to GitHub rises straight up, right of the entrypoint; the agent's line to the model provider rises through the channel, turns right above the group and enters the provider from below. The human's dashed configuration line enters the group from the top, and the human's line to GitHub runs right. Legend at the bottom: agent (a model runs), the human, the factory's code, stored state; flow, relation, and dashed ("once, at start").

## Reading

- One process chain, one agent at a time: the entrypoint ticks repositories one after another, and a tick waits for its agent.
- Everything the factory remembers lives in the `work` volume, under each checkout's `.git/`; deleting the volume deletes the bills of unfinished work items.
- The agent runs as the same user, in the same container, as everything else: it can reach every store in the picture ([chapter 15](../15-safety/README.md)).
