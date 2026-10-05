# <Title>

<!-- A story: one branch, one pull request, one run through tests, code, review, docs and demo.
     File: factory/features/<F0001-slug>/drafts/F0001-S0003-short-slug.md while you write it;
     move it to ../ongoing/ to start it. No frontmatter needed: the pipeline writes its own
     state fields (stage, pr, blocked, comments_seen, claimed_at, round, attempts). -->

## Assignment (as of log entry 1)

What is to be built and why, in a paragraph. This is the current meaning of the story and is rewritten by a stage when a log entry changes it.

## Interface

Module paths, class and function names, signatures, error types. The tester writes tests against this section, so it must be exact. Every behaviour stated here in a comment needs a criterion below, or two coders will read it two ways and both will pass the tests.

## Acceptance criteria

1. Numbered, testable, one behaviour each. The tester names tests after the behaviour and lists the mapping in the log. Every rule in the Interface gets a criterion for its failing side too ("a blank title is rejected with `InvalidTitle`"), and a limit is stated with its number so the tester can test both sides of it; intake sends a story back that states only the happy path.
2. Say what must still hold, not what must not have changed: "the todo routes are still present" lets the tester check a subset; "the other routes are unchanged" invites a test that lists every route and breaks on the next story, which then has to ask before touching it.
3. `make check` stays green.
4. docs: what the reader must know after this story, in one or two sentences (for example: "the filter is explained in `docs/api.md` with an example; the README's usage section mentions it"), or `none` with the reason. The last criterion of every story. The reviewer checks that it still fits what was built; the documenter writes it and cross-reads the rest of the documentation for staleness. Docstrings in code are the coder's and are covered by `make check`.

## Demo

Commands the demo stage runs from the repository root, each followed by an `Expect:` line stating what the output must show. The demo stage pastes the output below each command and checks it against the expectation before the pull request is marked ready. They run in the container: Linux, nothing listening, no files beyond what they create.

```bash
uv run python -c "..."
```
Expect: one line per todo, done flag first.

## Log (append only)

1. 2026-01-01 human: created.
