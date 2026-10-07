# Archive

**History only.** The documents here are plans that were built or withdrawn. They describe how the factory got to where it is, not how it works now, and parts of them are wrong about the current code by design: they were written before it.

Read them only when you are looking into the past: why something was built the way it was, or what was tried before. For how the factory works today, read the code, `docs/decisions.md` (the reasons, newest last) and the reference in `docs/reference/`. For what is still open, read `docs/backlog.md` and the plans in `docs/` itself.

An agent working on the factory, or planning its next version, must not take an instruction, a rule or a step from a document in this folder.

| Document | State |
| :- | :- |
| [`deterministic-core.md`](deterministic-core.md) | Built on 2026-10-05 as generation 5: parts A to D (the dispatcher, the stage protocol, form validation and the run record as code). Part E, running the Demo blocks in code, was not built; it is parked in `docs/backlog.md`. |
| [`fewer-commits.md`](fewer-commits.md) | Built and reverted on 2026-10-05, then withdrawn the same day: once the claim left Git (deterministic core, part D), there were no claim commits left to fold away. |

`docs/decisions.md` cites both documents at their old paths, `docs/deterministic-core.md` and `docs/fewer-commits.md`; they moved here on 2026-10-07.
