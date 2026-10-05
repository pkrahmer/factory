# Version command

## Assignment (as of log entry 1)

Let support ask a machine which version is installed without starting the server: `uv run python -m app --version` prints `app <version>` and exits 0. The module is a small command-line entry point that knows nothing of the layers below it.

## Interface

`src/app/__main__.py`

```python
def main(argv: list[str] | None = None) -> int: ...
# argv defaults to sys.argv[1:]
# ["--version"]: prints "app <version>" to stdout (importlib.metadata.version("app")), returns 0
# []: prints "usage: python -m app --version" to stderr, nothing to stdout, returns 2
# anything else: like [], returns 2

if __name__ == "__main__":
    sys.exit(main())
```

## Acceptance criteria

1. `main(["--version"])` writes exactly `app <version>` and a newline to stdout, where `<version>` is `importlib.metadata.version("app")`, and returns 0.
2. `main([])` returns 2, writes nothing to stdout, and writes `usage: python -m app --version` and a newline to stderr.
3. `main(["--help"])`, `main(["x"])` and `main(["--version", "x"])` each return 2, write nothing to stdout, and write the usage line to stderr.
4. `main()` without an argument reads `sys.argv[1:]`.
5. `app.__main__` imports nothing from `app.domain`, `app.service`, `app.repository` or `app.api`.
6. `make check` stays green.
7. docs: the README's *Getting started* shows `uv run python -m app --version` and what it prints.

## Demo

```bash
uv run python -m app --version; echo "exit $?"
```
Expect: `app 0.1.0`, then `exit 0`.

```bash
uv run python -m app; echo "exit $?"
```
Expect: `usage: python -m app --version`, then `exit 2`.

## Log (append only)

1. 2026-10-05 human: created.
