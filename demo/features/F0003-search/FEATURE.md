# Search

<!-- Folder: factory/features/F0003-search/. Stories go to drafts/ while they are written,
     ongoing/ when they may start, and the dispatcher moves them to done/ when merged.
     The feature is complete when drafts/ and ongoing/ are empty, which Git shows by their absence. -->

## Goal

Find a todo without scrolling: a word from its title narrows the list. Done when `GET /todos?search=<text>` returns the todos whose title contains the text, ignoring case, and combines with the done filter.

## Scope

- Title search in the service and as a query parameter of `GET /todos`

## Out of scope

- Full-text search, ranking, fuzzy matching, search in anything but the title
- A search index or a repository method for it (the service filters what the repository lists)

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Title search

## Decisions taken for the human

Product decisions taken while writing the stories or answering the pipeline's questions, for the human to review in one place. Each names where it was taken.

1. Search is a case-insensitive substring match on the title (Unicode case folding, so `STRASSE` finds `Straße`); the text is stripped first, and an empty text means no filter. (S0001, story text)
2. A search text longer than a title can be (200 characters) is rejected with 422 rather than silently matching nothing. (S0001, story text)
