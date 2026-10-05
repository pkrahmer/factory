# Operations

<!-- Folder: factory/features/F0002-operations/. Stories go to drafts/ while they are written,
     ongoing/ when they may start, and the dispatcher moves them to done/ when merged.
     The feature is complete when drafts/ and ongoing/ are empty, which Git shows by their absence. -->

## Goal

What running the service needs beyond its features: a health endpoint a monitor can poll, a version command for support, and statistics for a glance at the data. Done when an operator can tell from outside whether the service is up, which version runs and with which storage, and how many todos are open and done.

## Scope

- `GET /health`: status, version, storage kind
- `python -m app --version`
- `GET /stats`: open, done, total

## Out of scope

- Metrics export, logging configuration, deployment
- Authentication of the operations endpoints (the service is single-user)

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Health endpoint
- S0002 — Version command
- S0003 — Todo statistics

## Decisions taken for the human

Product decisions taken while writing the stories or answering the pipeline's questions, for the human to review in one place. Each names where it was taken.

1. `/health` reports `status`, the package `version` and the `storage` kind (`memory` or `sqlite`), and never touches the repository, so it answers even when the database does not. (S0001, story text)
2. The version command prints `app <version>`; any other argument prints the usage line to stderr and exits 2. (S0002, story text)
3. Statistics are three counts, `open`, `done`, `total`; `total` is derived, never stored. (S0003, story text)
4. The reference's fourth story, a shared service dependency, is not needed: the dependency module exists since F0001-S0003. (feature text)
5. Only exactly `--version` prints the version; `--version` with anything after it is a usage error like any other argument. (S0002, story text)
