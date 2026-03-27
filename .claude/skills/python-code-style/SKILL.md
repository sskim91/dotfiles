---
name: python-code-style
description: Use when configuring ruff/mypy/pyright, setting up formatting, writing docstrings, or establishing coding standards. Do NOT use for general patterns (use python-patterns) or testing (use python-testing).
---

# Python Code Style & Tooling

판단 기준과 규칙 중심. ruff/mypy 설정과 네이밍 규칙의 **올바른 선택**을 안내.

## Quick Start

- **린터/포매터 설정?** --> [Ruff Config](#ruff-configuration) below
- **타입 체커 선택?** --> [Type Checker Decision](#type-checker-decision) below
- **네이밍 규칙?** --> [Naming Rules](#naming-rules) below
- **독스트링 작성?** --> [Docstring Rules](#docstring-rules) below
- **Ruff 룰 카테고리 상세?** --> [references/ruff-rules-guide.md](references/ruff-rules-guide.md)

## CRITICAL Rules

1. **ALWAYS** use `ruff` as single linter+formatter -- flake8+isort+black 조합 대체
2. **ALWAYS** enable strict `mypy` or `pyright` for production code
3. **ALWAYS** 120 char line length -- 현대 디스플레이 표준
4. **ALWAYS** absolute imports -- `from mypackage.utils import x` (relative imports 금지)
5. **NEVER** `from module import *` -- 명시적 import만
6. **ALWAYS** Google-style docstrings -- public API에 필수
7. **PREFER** `ruff check --fix` + `ruff format` -- 수동 포매팅 금지
8. **ALWAYS** configure `per-file-ignores` for tests -- S101(assert), ARG 허용
9. **PREFER** `pyproject.toml` 단일 설정 -- setup.cfg, .flake8 등 분산 금지

## Type Checker Decision

```
Need type checking?
+-- New project, full control? --> pyright (strict mode, faster, LSP 내장)
+-- Existing project, gradual adoption? --> mypy (strict=true, overrides로 점진적)
+-- Both available? --> pyright (개발 시) + mypy (CI용)
+-- Django/SQLAlchemy project? --> mypy + django-stubs/sqlalchemy-stubs
```

### mypy Config

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### pyright Config

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
```

## Ruff Configuration

### Strictness Levels

| Level | select | Use Case |
|-------|--------|----------|
| Minimal | `E, W, F, I, B, UP` | 레거시 프로젝트, 빠른 도입 |
| Standard | `+ C4, SIM, PT, RET, RUF, PERF` | 신규 프로젝트 권장 |
| Strict | `ALL` (with ignores) | 최대 안전성, 라이브러리 개발 |

### Standard Config (Recommended)

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "B", "C4",
    "UP", "SIM", "PT", "RET", "RUF", "PERF",
]
ignore = ["E501"]  # formatter handles line length

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "PT004"]
"__init__.py" = ["F401"]

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

## Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Module/file | `snake_case` | `user_repository.py` |
| Class | `PascalCase` | `UserRepository` |
| Function/variable | `snake_case` | `get_user_by_email` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Type variable | `PascalCase` or single letter | `T`, `KeyType` |
| Private | `_prefix` | `_internal_cache` |
| Acronym in class | Uppercase | `HTTPClientFactory` |

### Naming Anti-Patterns

```python
# BAD: Abbreviations
usr_repo.py, ord_proc.py, http_cli.py

# GOOD: Descriptive
user_repository.py, order_processing.py, http_client.py

# BAD: Generic names
data, info, result, temp, foo

# GOOD: Intent-revealing names
user_count, order_total, parsed_response
```

## Docstring Rules

### When to Write

| Target | Required? |
|--------|-----------|
| Public function/method | Yes -- 항상 |
| Public class | Yes -- `__init__` 포함 |
| Private with complex logic | Yes |
| Trivial getter/setter | No -- 타입 힌트로 충분 |
| Test function | No -- 함수명이 문서 |

### Format (Google Style)

```python
def process_batch(
    items: list[Item],
    max_workers: int = 4,
    on_progress: Callable[[int, int], None] | None = None,
) -> BatchResult:
    """Process items concurrently using a worker pool.

    Args:
        items: The items to process. Must not be empty.
        max_workers: Maximum concurrent workers. Defaults to 4.
        on_progress: Optional callback receiving (completed, total).

    Returns:
        BatchResult with succeeded items and failures.

    Raises:
        ValueError: If items is empty.
    """
```

**Rules:**
- 한 줄이면 `"""Retrieve a user by ID."""` (closing quotes 같은 줄)
- 복잡하면 summary line + blank line + details
- `Args`, `Returns`, `Raises` 순서 고정
- `Example:` 섹션은 doctest로 실행 가능하게

## Import Organization

```python
# 1. Standard library
import os
from collections.abc import Callable

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Local (absolute imports only)
from myproject.models import User
from myproject.services import UserService
```

ruff의 `I` rule이 자동 정렬. `known-first-party` 설정 필수.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `from module import *` | 네임스페이스 오염 | 명시적 import |
| `from ..utils import x` | 리팩토링 시 깨짐 | 절대 import |
| `print()` for debugging | 프로덕션에 남음 | `logging` 또는 ruff `T20` rule |
| Manual formatting | 일관성 깨짐, 시간 낭비 | `ruff format` 자동화 |
| setup.cfg + .flake8 + .isort.cfg | 설정 파일 분산 | `pyproject.toml` 단일 파일 |
| `# type: ignore` without code | 어떤 에러인지 불명확 | `# type: ignore[specific-error]` |
| `noqa` without code | 어떤 룰인지 불명확 | `# noqa: E501` 명시 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ ruff에서 `select = ["ALL"]` → 너무 공격적, `["E", "F", "W", "I"]`부터 시작
- ❌ mypy `strict` 모드 기존 프로젝트에 바로 적용 → 점진적 적용 필수
- ❌ docstring에 파라미터 타입 중복 기술 → type hints가 있으면 docstring에서 타입 생략

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| ruff format과 lint 충돌 | `COM812`, `ISC001` rule 활성 | ignore에 추가 |
| mypy "missing stubs" | 서드파티 타입 스텁 없음 | `pip install types-xxx` 또는 `[[tool.mypy.overrides]]` |
| CI에서만 lint 실패 | 로컬 ruff 버전 차이 | `pre-commit` 또는 CI에서 버전 고정 |
| isort 정렬 안 맞음 | `known-first-party` 미설정 | ruff.lint.isort에 패키지명 추가 |

## Cross-References

| Topic | Skill |
|-------|-------|
| Python 패턴, 타입 힌트, 동시성 | `python-patterns` |
| pytest, TDD, fixtures, mocking | `python-testing` |
| Ruff 룰 카테고리 전체, pre-commit 설정 | [references/ruff-rules-guide.md](references/ruff-rules-guide.md) |

## References

- [Ruff docs](https://docs.astral.sh/ruff/) -- Official documentation
- [Ruff rules](https://docs.astral.sh/ruff/rules/) -- Complete rule listing
- [mypy docs](https://mypy.readthedocs.io/) -- Type checker
- [pyright docs](https://github.com/microsoft/pyright) -- Microsoft type checker
- [PEP 8](https://peps.python.org/pep-0008/) -- Python style guide
- [PEP 257](https://peps.python.org/pep-0257/) -- Docstring conventions
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
