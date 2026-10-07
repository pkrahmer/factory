.PHONY: check lint types dockerfile test book
.SILENT:

check: lint types dockerfile test
	echo "check: green"

lint:
	uv run ruff check --output-format=concise .
	uv run ruff format --check --quiet .
	echo "lint: green"

types:
	uv run mypy --no-error-summary --hide-error-context
	echo "types: green"

# The image is this repository's product; hadolint (a binary: `choco install hadolint`,
# `brew install hadolint`, or the release from github.com/hadolint/hadolint) lints its recipe.
dockerfile:
	hadolint Dockerfile
	echo "dockerfile: green"

test:
	uv run pytest --no-header --tb=short
	echo "test: green"

# The reference manual (docs/reference) as a printable book: pandoc and typst on the PATH.
# BOOK_FLAGS=--reader leaves out the planner boxes; --pages also writes page images.
book:
	uv run python docs/reference/_print/book.py $(BOOK_FLAGS)
