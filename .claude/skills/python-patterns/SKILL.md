---
name: python-patterns
description: Use when writing, reviewing, or refactoring Python code, designing data classes, implementing decorators, or choosing concurrency patterns. Do NOT use for linter/formatter config (use python-code-style) or testing (use python-testing).
---

# Python Development Patterns

판단 기준과 규칙 중심. 기본 문법이 아닌, Claude가 **올바른 선택**을 하도록 안내.

## Quick Start

- **타입 힌트 결정?** → [Type Hints](#type-hints) below
- **데이터 컨테이너 선택?** → [Data Containers](#data-containers) below
- **동시성 모델 선택?** → [Concurrency Decision](#concurrency-decision) below
- **코드 리뷰?** → [Code Review](#code-review) below
- **Python 3.10~3.14 신기능?** → [Modern Python Features](references/modern-python-features.md)
- **asyncio/threading 심화?** → [Concurrency Deep Dive](references/concurrency-deep-dive.md)

## When to Activate

- Python 코드 작성, 리뷰, 리팩토링
- 데이터 모델링 (dataclass vs NamedTuple vs TypedDict)
- 동시성 모델 선택
- 타입 힌트 전략 결정
- 코드 리뷰

## CRITICAL Rules

1. **NEVER** mutable default arguments — `def f(items=[])` 금지, `items=None` 사용
2. **NEVER** bare `except:` — 항상 specific exception 명시
3. **ALWAYS** chain exceptions — `raise NewError(...) from e`
4. **ALWAYS** context managers for resources — `with` 문 필수
5. **PREFER** EAFP over LBYL — `try/except` > `if exists` (race condition 방지)
6. **PREFER** modern type hints (3.10+) — `str | None` > `Optional[str]`
7. **NEVER** `from module import *` — 명시적 import만
8. **ALWAYS** `is None` / `is not None` — `== None` 금지
9. **PREFER** `isinstance()` over `type()` — 상속 체인 존중

## Type Hints

### Modern Syntax (Python 3.10+, Recommended)

```python
# Built-in types + | union syntax (PEP 604)
def process(user_id: str, data: dict[str, Any]) -> User | None:
    ...

# Python 3.12+ — type statement, generic syntax (PEP 695)
type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

def first[T](items: list[T]) -> T | None:
    return items[0] if items else None
```

### Protocol (Structural Typing)

```python
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...

# Any class with render() satisfies Renderable — no inheritance needed
def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)
```

### Type-Safe Decorator (ParamSpec)

```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec('P')
R = TypeVar('R')

def log_call(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

### When to Use What

| Type Feature | Use When |
|-------------|----------|
| `X \| None` | Optional value (3.10+) |
| `Protocol` | Duck typing interface (structural subtyping) |
| `@override` | Overriding parent method (3.12+) |
| `TypeIs` | Type narrowing in both branches (3.13+) |
| `ParamSpec` | Preserving decorator type signature |
| Legacy `Optional`, `Union` | Only for Python < 3.10 support |

## Data Containers

### Decision Tree

```
Need a data container?
├── Immutable? → NamedTuple or @dataclass(frozen=True)
│   ├── Lightweight, tuple-like? → NamedTuple
│   └── Methods, validation needed? → @dataclass(frozen=True)
├── Dict-like (JSON mapping)? → TypedDict
├── Need __post_init__ validation? → @dataclass
├── Memory-critical (millions)? → @dataclass(slots=True)
└── Simple grouping, no behavior? → @dataclass
```

### Comparison

| Feature | `@dataclass` | `NamedTuple` | `TypedDict` |
|---------|-------------|-------------|------------|
| Mutable | Yes (default) | No | Yes |
| Methods | Yes | Yes | No |
| `__post_init__` | Yes | No | No |
| `__slots__` | Yes (3.10+) | Automatic | N/A |
| JSON compatible | No | No | Yes |

```python
# dataclass with validation
@dataclass
class User:
    email: str
    age: int

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
        if not 0 <= self.age <= 150:
            raise ValueError(f"Invalid age: {self.age}")

# NamedTuple — immutable, lightweight
class Point(NamedTuple):
    x: float
    y: float

# Memory-efficient for high-volume objects
@dataclass(slots=True)
class Coordinate:
    x: float
    y: float
    z: float
```

## Error Handling

### Rules

```python
# ALWAYS chain exceptions — preserve traceback
try:
    parsed = json.loads(data)
except json.JSONDecodeError as e:
    raise ValueError(f"Failed to parse: {data}") from e
```

### Custom Exception Hierarchy

```python
class AppError(Exception): ...
class ValidationError(AppError): ...
class NotFoundError(AppError): ...

def get_user(user_id: str) -> User:
    user = db.find_user(user_id)
    if not user:
        raise NotFoundError(f"User not found: {user_id}")
    return user
```

### EAFP vs LBYL

```python
# GOOD: EAFP — try first, handle failure
def read_config(path: str) -> dict[str, Any]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# BAD: LBYL — race condition between check and open
def read_config(path: str) -> dict[str, Any]:
    if os.path.exists(path):  # File could be deleted here!
        with open(path) as f:
            return json.load(f)
    return {}
```

## Concurrency Decision

```
Need concurrent I/O?
├── Many connections (100+)? → asyncio (TaskGroup)
├── Few connections? → ThreadPoolExecutor
└── Simplest option? → concurrent.futures.ThreadPoolExecutor

Need parallel computation?
├── Pure Python math? → ProcessPoolExecutor
├── NumPy/pandas? → threading (already releases GIL)
└── Python 3.13+ experimental? → Free-threaded mode

Need both I/O + CPU?
└── asyncio + ProcessPoolExecutor via run_in_executor
```

See [Concurrency Deep Dive](references/concurrency-deep-dive.md) for TaskGroup, Semaphore, producer-consumer pipeline.

## Performance Tips

| Pattern | Good | Bad |
|---------|------|-----|
| String join | `"".join(parts)` | `result += s` in loop |
| Membership test | `x in set_data` O(1) | `x in list_data` O(n) |
| Large data sum | `sum(x*x for x in data)` | `sum([x*x for x in data])` |
| Memory efficiency | `@dataclass(slots=True)` | Regular class `__dict__` |
| Dict default | `d.get(k, default)` | `if k in d: d[k]` |
| Lazy iteration | `yield` / generator | Entire list in memory |

## Anti-Patterns

```python
# BAD: Mutable default — shared across all calls!
def append_to(item, items=[]):
    items.append(item)
    return items

# GOOD:
def append_to(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# BAD: Bare except — silences all errors including KeyboardInterrupt
try:
    risky()
except:
    pass

# GOOD:
try:
    risky()
except SpecificError as e:
    logger.error(f"Failed: {e}")

# BAD: type() comparison — ignores inheritance
if type(obj) == list: ...

# GOOD: isinstance — respects inheritance chain
if isinstance(obj, list): ...

# BAD: == None
if value == None: ...

# GOOD: is None
if value is None: ...
```

## Code Review

### Checklist

**Correctness (CRITICAL — address first)**
- [ ] No mutable default arguments
- [ ] Specific exception handling (no bare `except:`)
- [ ] Exception chaining (`from e`)
- [ ] Edge cases handled

**Type Safety (HIGH)**
- [ ] Type hints on all function signatures
- [ ] Modern syntax (3.10+: `X | None`, built-in generics)
- [ ] `Protocol` for duck typing interfaces

**Performance (HIGH)**
- [ ] Generators for large data (not list comprehensions)
- [ ] Context managers for all resources
- [ ] `__slots__` for high-volume dataclasses

**Style (MEDIUM)**
- [ ] PEP 8 compliant
- [ ] Meaningful variable names
- [ ] No `import *`

### Severity Levels

| Level | Examples | Action |
|-------|----------|--------|
| **CRITICAL** | Mutable defaults, bare except, resource leak | Fix immediately |
| **HIGH** | Missing types, no exception chaining | Fix before merge |
| **MEDIUM** | Style violations, missing docs | Fix or TODO |
| **LOW** | Minor formatting | Optional |

### Review Output Format

- **Summary**: Brief overview and main issues
- **Critical Issues**: File, Issue, Impact, Fix
- **High/Medium**: Same format
- **Recommendations**: General improvement suggestions

## Package Structure

```
myproject/
├── src/mypackage/
│   ├── __init__.py      # Exports: __all__
│   ├── main.py
│   ├── api/
│   ├── models/
│   └── utils/
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── pyproject.toml
└── README.md
```

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ mutable default argument (`def f(x=[])`) → `None` 기본값 + 내부 생성
- ❌ `type()` 비교 → `isinstance()` 사용
- ❌ bare `except:` → 최소 `except Exception:` 또는 구체적 예외
- ❌ `== None` 비교 → `is None` 사용
- ❌ `CancellationError` 삼키기 (asyncio) → 반드시 re-raise

## Cross-References

| Topic | Skill |
|-------|-------|
| Ruff, mypy, formatting, naming | `python-code-style` |
| pytest, TDD, fixtures, mocking | `python-testing` |
| Python 3.10~3.14 new features | [references/modern-python-features.md](references/modern-python-features.md) |
| asyncio/threading/multiprocessing deep dive | [references/concurrency-deep-dive.md](references/concurrency-deep-dive.md) |

## References

- [Python Official Docs](https://docs.python.org/3/) — Standard library reference
- [What's New in Python](https://docs.python.org/3/whatsnew/) — Release changelogs
- [PEP Index](https://peps.python.org/) — Python Enhancement Proposals
- [Real Python](https://realpython.com/) — Tutorials and best practices
- [Effective Python (Brett Slatkin)](https://effectivepython.com/) — 90 ways to write better Python
