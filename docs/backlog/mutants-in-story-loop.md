# Mutation testing in the story loop

**Parked on 2026-10-05.** Nothing here is built. The idea: run `make mutants` inside each story, after the coder, instead of only at the feature acceptance, so that a test gap is closed while the story that caused it is still open.

## Why

Today only the feature acceptance runs `make mutants` (`role-acceptor`, check 3). Each survivor that points to a missing test becomes a draft story. In the demo run of 2026-10-05, F0001's acceptances proposed S0007 and then S0008 and S0009, all three test-only. Each such story goes through the whole loop: promotion, intake, six stages and a pull request the human reviews. Then it triggers a new acceptance, which can propose the next test-only drafts. The series does not end on its own. The acceptor raised the same thing as an open decision: "whether tests-only stories are fine".

The numbers from that run:

| | |
|:-|-:|
| `make mutants` on the demo project (299 mutants, `time` in the acceptor's session) | 5 s |
| S0007, a test-only story (6 runs, three of which only confirmed existing behaviour) | $0.47 |
| One feature acceptance | $1.60 |

At five seconds, mutation testing fits a stage. The Makefile comment that "it takes minutes, so no stage runs it" is too pessimistic for a project of this size.

## Not every survivor is a test to write

The acceptance's 10 survivors broke down like this:

- 3 equivalent: the mutant cannot change behaviour;
- 3 changed an error message that no document promises;
- 1 survived only because the container runs on UTC;
- 3 were real gaps (S0008, S0009).

An agent that kills every survivor writes tests that freeze behaviour nobody promised. Survivors need judgement, and inside a story there is a yardstick for it: the story's criteria.

## The shape

1. **The factory runs it.** After the coder, `make mutants` runs as a `records` entry of the `doing` stage in `stages.yml`, the same way `make test` is recorded after the tester. It is never a `check`: a survivor is something to judge, not a gate. The survivor list goes into the reviewer's task as a fact. A project without the target simply does not list it.
2. **The reviewer sorts each survivor in the story's code.**
   - A criterion covers the behaviour → a missing test, which is a finding for the tests.
   - No criterion asks for the behaviour → the code does more than the story asked, which is a finding for the coder (remove it, or ask).
   - Equivalent, or not observable → named in the entry, nothing to do.
3. **The tester writes the missing tests.** The coder must not touch tests: the tester writes them as the specification, before the code exists. A test that kills a mutant can only be written after the code exists, so a new edge is needed: review → `tests`, with the tester in a mode like the existing "a test change the human approved". That mode adds exactly the named tests and ends the stage. The round counts towards `max_rounds`.
4. **The acceptance stays the net.** It keeps running `make mutants` over the whole feature, for survivors in code that spans several stories.

Estimated cost per survivor round, from S0007's stage costs: tester $0.11, coder $0.07 (nothing to change), reviewer $0.10, so about $0.30. That compares with a test-only story's $0.47, its share of the next acceptance, and the human's review of one more pull request.

## Open questions

- **Survivors outside the story.** A full run also reports survivors in code that the story did not touch. There are three ways to filter them:
  - mutmut 3 takes mutant names (`mutmut run "app.api.errors*"`), but turning the diff's paths into module names depends on the project's layout;
  - the reviewer can filter by the diff, which costs a few lines of reading;
  - the factory can compare the run against `main`'s survivors, which costs a second run.
- **Who ends the tester's mode.** Should it go back to `doing`, as today's test-change mode does (one coder run with nothing to do), or straight to `review` (a new `next` entry for `tests`)?
- **Runtime growth.** The target deletes `mutants/` first, so every run starts from scratch. mutmut can reuse earlier results; a large project needs that, or a timeout on the record.
- **What the human sees.** The pull request would carry tests that the criteria did not name, and possibly a score line. That changes what the human reviews, so the human approves it before it is built.
- **Contract.** A new `next` entry and a new tester mode change `stages.yml` and the stage skills, and possibly `WATCH_CONTRACT.md`, if the review → tests edge needs a dispatch rule of its own.

The drafts F0001-S0008 and F0001-S0009 in `pkrahmer/factory-demo-todo` are exactly what this would replace. They stay in `drafts/` until this is decided.
