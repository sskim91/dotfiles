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

| Type Feature | Use When |
|-------------|----------|
| `X \| None` | Optional value (3.10+) |
| `Protocol` | Duck typing interface (structural subtyping) |
| `@override` | Overriding parent method (3.12+) |
| `TypeIs` | Type narrowing in both branches (3.13+) |
| `ParamSpec` | Preserving decorator type signature |
| `type` statement | Recursive/complex type aliases (3.12+, PEP 695) |
| Legacy `Optional`, `Union` | Only for Python < 3.10 support |

## Data Containers

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

## Error Handling

- Exception chaining 필수: `raise NewError(...) from e`
- Custom hierarchy: `AppError → ValidationError, NotFoundError`
- EAFP > LBYL (race condition 방지)
- CRITICAL Rules #2, #3, #5 참조

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

## Code Review Priorities

| Level | Examples | Action |
|-------|----------|--------|
| **CRITICAL** | Mutable defaults, bare except, resource leak | Fix immediately |
| **HIGH** | Missing types, no exception chaining | Fix before merge |
| **MEDIUM** | Style violations, missing docs | Fix or TODO |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ mutable default argument (`def f(x=[])`) → `None` 기본값 + 내부 생성
- ❌ `type()` 비교 → `isinstance()` 사용
- ❌ bare `except:` → 최소 `except Exception:` 또는 구체적 예외
- ❌ `== None` 비교 → `is None` 사용
- ❌ `CancellationError` 삼키기 (asyncio) → 반드시 re-raise

## Verification

코드 작성 후 반드시 실행:
```bash
ruff check .                     # 린트
ruff format --check .            # 포맷 확인
pytest -x -q                     # 테스트 (fail-fast)
mypy --strict src/               # 타입 체크 (설정된 경우)
```

## Cross-References

| Topic | Skill |
|-------|-------|
| Ruff, mypy, formatting, naming | `python-code-style` |
| pytest, TDD, fixtures, mocking | `python-testing` |
| Python 3.10~3.14 new features | [references/modern-python-features.md](references/modern-python-features.md) |
| asyncio/threading/multiprocessing deep dive | [references/concurrency-deep-dive.md](references/concurrency-deep-dive.md) |
