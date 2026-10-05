# Service layer with filtering

## Assignment (as of log entry 1)

Add the use-case layer on top of the domain: a `TodoService` that creates, reads, lists (all, or filtered by the done flag), renames, completes, reopens and deletes todos through the `TodoRepository` protocol. The service owns the clock, injectable for tests; the title rule stays in the domain and its errors pass through unchanged. No API yet.

## Interface

`src/app/service/todo_service.py`

```python
Clock = Callable[[], datetime]

def utc_now() -> datetime: ...

class TodoService:
    def __init__(self, repository: TodoRepository, clock: Clock = utc_now) -> None: ...
    def create(self, title: str) -> Todo: ...
    def get(self, todo_id: UUID) -> Todo: ...
    def list(self, *, done: bool | None = None) -> list[Todo]: ...
    def rename(self, todo_id: UUID, title: str) -> Todo: ...
    def complete(self, todo_id: UUID) -> Todo: ...
    def reopen(self, todo_id: UUID) -> Todo: ...
    def delete(self, todo_id: UUID) -> None: ...
```

- `create` stamps `created_at` with the clock; `list(done=None)` means no filter; every list is in the repository's order (creation order).
- Domain errors (`InvalidTitle`, `TodoNotFound`) propagate unchanged.
- `app.service` sees storage only through `TodoRepository`; import-linter (`make check`) already refuses an import of `app.repository` there. Tests use `InMemoryTodoRepository` as the concrete repository; a test may import it.

## Acceptance criteria

1. `create("  Buy milk ")` returns a todo titled `Buy milk`, not done, whose `created_at` is the value the injected clock returned; `get` with its id returns an equal todo.
2. `create` with a blank title raises `InvalidTitle`, and `list()` is still empty afterwards.
3. `get` with an unknown id raises `TodoNotFound` carrying that id.
4. `list()` returns every todo, in creation order (a clock that ticks makes the order observable).
5. `list(done=True)` returns only the completed todos, in creation order.
6. `list(done=False)` returns only the open todos, in creation order.
7. `rename` returns the todo with the new title, stripped, and the same id, done flag and `created_at`; `get` returns the renamed todo afterwards.
8. `rename` with a blank title raises `InvalidTitle`, and `get` still returns the todo with its old title.
9. `complete` returns the todo with `done` true, and `get` returns it completed afterwards.
10. `complete` on a completed todo returns it, still done, without an error.
11. `reopen` returns the todo with `done` false, and `get` returns it open afterwards.
12. `reopen` on an open todo returns it, still open, without an error.
13. `delete` removes the todo: `get` afterwards raises `TodoNotFound`.
14. `rename`, `complete`, `reopen` and `delete` with an unknown id each raise `TodoNotFound` carrying that id.
15. `utc_now()` returns a timezone-aware datetime with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
16. `make check` stays green.
17. docs: `docs/architecture.md` describes the service layer: what `TodoService` owns (the use cases, the clock, the done filter) and that it reaches storage only through the repository protocol.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import TodoService
svc = TodoService(InMemoryTodoRepository(), clock=lambda: datetime(2026, 10, 4, 12, 0, tzinfo=UTC))
a = svc.create('  Buy milk ')
b = svc.create('Write the next story')
svc.complete(a.id)
print([t.title for t in svc.list(done=True)])
print([t.title for t in svc.list(done=False)])
print(svc.rename(b.id, 'Write story S0003').title, svc.get(b.id).created_at.isoformat())
"
```
Expect: `['Buy milk']`, then `['Write the next story']`, then `Write story S0003 2026-10-04T12:00:00+00:00`.

```bash
uv run python -c "
from uuid import uuid4
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import TodoService
svc = TodoService(InMemoryTodoRepository())
for call in (lambda: svc.create('   '), lambda: svc.complete(uuid4())):
    try:
        call()
    except Exception as e:
        print(type(e).__name__)
print(svc.list())
"
```
Expect: `InvalidTitle`, then `TodoNotFound`, then `[]`.

## Log (append only)

1. 2026-10-04 human: created.
