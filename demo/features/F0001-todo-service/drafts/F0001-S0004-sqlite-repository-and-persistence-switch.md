# SQLite repository and persistence switch

## Assignment (as of log entry 1)

Add the second `TodoRepository`, backed by a SQLite file through SQLAlchemy 2.0 Core, prove it equal to the in-memory one by running the existing repository contract suite against both, and let the composition root choose the repository from the environment: `TODO_DB=<path>` keeps the todos in that file across restarts, no `TODO_DB` keeps them in memory as today. Nothing above the repository layer changes except `src/app/api/main.py`.

## Interface

`src/app/repository/sqlite.py`

```python
class SqliteTodoRepository:   # satisfies TodoRepository structurally, no inheritance
    def __init__(self, engine: Engine) -> None: ...
    @classmethod
    def from_path(cls, path: str | Path) -> "SqliteTodoRepository": ...
```

- `__init__` creates the table `todos` when it is missing and leaves an existing one and its rows alone.
- `from_path` opens the SQLite file at `path` (`sqlite:///<path>`), creating the file when it does not exist.
- The table is a `sqlalchemy.Table` (Core, no ORM models): `id` TEXT primary key (the UUID's hyphenated form), `title` TEXT NOT NULL, `done` BOOLEAN NOT NULL, `created_at` TEXT NOT NULL (ISO 8601, UTC). Every statement is built from Core constructs on that table; no SQL in strings.

`src/app/api/main.py`

```python
def build_repository(environ: Mapping[str, str]) -> TodoRepository: ...
app = create_app(TodoService(build_repository(os.environ)))
```

- `TODO_DB` missing or empty: `InMemoryTodoRepository()`. Otherwise `SqliteTodoRepository.from_path(environ["TODO_DB"])`.
- `app.api.main` stays the only `app.api` module that imports `app.repository`.

Tests: the tester adds `SqliteTodoRepository` on a file under `tmp_path` to the list of repository factories in `tests/repository/test_contract.py`, so the whole contract suite runs against both repositories. That one addition to an existing test file is part of this story; nothing else in that file changes.

## Acceptance criteria

1. Every test of the repository contract suite passes for `SqliteTodoRepository` on a file under `tmp_path`, as it does for `InMemoryTodoRepository`.
2. `from_path` on a path whose file does not exist creates the file, and the new repository's `list_all()` returns `[]`.
3. A todo added through one `SqliteTodoRepository` is returned by `get` and by `list_all` of a second instance opened on the same path.
4. A second `SqliteTodoRepository` built on the same engine does not fail, and the todos stored through the first are still there.
5. `created_at` survives the round trip: a todo created at `datetime(2026, 10, 4, 12, 0, 0, 123456, tzinfo=UTC)` is read back equal, timezone-aware, with a zero UTC offset.
6. A title containing quotes and SQL, `Robert'); DROP TABLE todos;--`, is stored and read back verbatim, and every other todo is still listed.
7. `build_repository({})` and `build_repository({"TODO_DB": ""})` each return an `InMemoryTodoRepository`.
8. `build_repository({"TODO_DB": <a path under tmp_path>})` returns a `SqliteTodoRepository`, and the file exists afterwards.
9. A todo created through `create_app(TodoService(build_repository({"TODO_DB": p})))` is listed by a second app built the same way on the same `p`.
10. An app built with `build_repository({})` writes no file: after creating a todo through it, the current directory (a `tmp_path` the test changes into) is still empty.
11. `make check` stays green.
12. docs: `docs/api.md` explains storage in a short section: with `TODO_DB=<path>` the todos live in that SQLite file, created on first start; without it they live in memory and are gone on restart. The README's *Getting started* shows starting the server with `TODO_DB`.

## Demo

```bash
rm -f /tmp/demo-todo.db
TODO_DB=/tmp/demo-todo.db uv run uvicorn app.api.main:app --port 8765 >/tmp/uvicorn.log 2>&1 & pid=$!
for i in $(seq 40); do curl -s -o /dev/null localhost:8765/todos && break; sleep 0.5; done
curl -s -X POST localhost:8765/todos -H 'content-type: application/json' -d '{"title":"Survive a restart"}'; echo
kill $pid; wait $pid 2>/dev/null
TODO_DB=/tmp/demo-todo.db uv run uvicorn app.api.main:app --port 8765 >/tmp/uvicorn.log 2>&1 & pid=$!
for i in $(seq 40); do curl -s -o /dev/null localhost:8765/todos && break; sleep 0.5; done
curl -s localhost:8765/todos; echo
kill $pid; wait $pid 2>/dev/null
ls -l /tmp/demo-todo.db | cut -d' ' -f1
```
Expect: the created todo as JSON; then a list holding exactly that todo, with the same id, after the restart; then a permissions string starting with `-rw`, showing the file exists.

## Log (append only)

1. 2026-10-04 human: created.
