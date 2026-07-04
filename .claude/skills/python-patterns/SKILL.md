---
name: python-patterns
description: Use when writing, reviewing, or refactoring Python code, designing data classes, implementing decorators, or choosing concurrency patterns. Do NOT use for linter/formatter config (use python-code-style) or testing (use python-testing).
paths: "**/*.py, **/pyproject.toml"
---

# Python Development Patterns

버전 경계(3.10~3.14)와 실수 잦은 지점만 담는다. Python 일반 문법·패턴 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **NEVER** mutable default arguments — `def f(items=[])` 금지, `items=None` 사용
2. **NEVER** bare `except:` — 항상 specific exception 명시
3. **ALWAYS** chain exceptions — `raise NewError(...) from e`
4. **PREFER** EAFP over LBYL — `try/except` > `if exists` (race condition 방지)
5. **PREFER** modern type hints (3.10+) — `str | None` > `Optional[str]`
6. **ALWAYS** `is None` / `is not None` — `== None` 금지

## Version Boundaries (3.10+)

| Feature | Version | Note |
|---------|---------|------|
| `X \| None` union syntax | 3.10 | `Optional`/`Union`은 <3.10 지원 시에만 |
| `type` statement (PEP 695), `@override` | 3.12 | |
| `TypeIs` (양방향 type narrowing) | 3.13 | |
| Free-threaded mode | 3.13 experimental → 3.14 supported | NumPy/pandas는 이미 GIL 해제 — threading으로 충분한 경우 많음 |
| Deferred annotations 기본화 (PEP 649) | 3.14 | `from __future__ import annotations` 불필요 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ mutable default argument (`def f(x=[])`) → `None` 기본값 + 내부 생성
- ❌ `type()` 비교 → `isinstance()` 사용
- ❌ `== None` 비교 → `is None` 사용
- ❌ asyncio에서 `CancelledError` 삼키기 → 반드시 re-raise
- ❌ asyncio에 `gather()` 습관적 사용 → 3.11+는 `TaskGroup` (structured concurrency, 에러 전파 안전)
- ❌ CPU-bound에 threading → `ProcessPoolExecutor` (단, NumPy/pandas는 GIL 해제하므로 threading OK)

## Verification

```bash
ruff check . && ruff format --check .    # 린트 + 포맷
pytest -x -q                             # 테스트 (fail-fast)
mypy --strict src/                       # 타입 체크 (설정된 경우)
```

## Cross-References

| Topic | Skill |
|-------|-------|
| Ruff, mypy, formatting, naming | `python-code-style` |
| pytest, TDD, fixtures, mocking | `python-testing` |
