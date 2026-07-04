---
name: python-testing
description: Use when writing tests, setting up pytest, implementing TDD, creating fixtures, or mocking dependencies. Do NOT use for general patterns (use python-patterns) or style config (use python-code-style).
paths: "**/*.py, **/pyproject.toml, **/pytest.ini, **/conftest.py"
---

# Python Testing Patterns

실수 잦은 지점과 프로젝트 컨벤션만 담는다. pytest API 일반 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **Test behavior, not implementation** — 내부 구현이 아닌 입출력/부수효과 검증
2. **Mock at boundaries only** — 외부 시스템(DB, API, filesystem)만 mock, 내부 로직은 실제 실행
3. **Patch where you USE, not where you define** — `patch("myapp.service.requests.get")` NOT `patch("requests.get")`
4. **ALWAYS** `autospec=True` on mocks — API 불일치 조기 발견
5. **PREFER** `pytest.raises(match=...)` — 예외 타입 + 메시지 함께 검증
6. **NEVER** test third-party code — 라이브러리가 동작하는지 테스트하지 마라
7. 80%+ coverage, critical paths 100% — `pytest --cov --cov-fail-under=80`

## pytest Configuration (프로젝트 컨벤션)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--cov=src", "--cov-report=term-missing", "--cov-fail-under=80", "-x", "--tb=short"]
markers = ["slow: marks tests as slow", "integration: integration tests"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError", "@abstractmethod"]
```

테스트 네이밍: `test_{method}_{scenario}_{expected_result}` — 예: `test_create_user_duplicate_email_raises_conflict`

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `patch('module.Class')` (정의 위치) → `patch('consumer_module.Class')` (사용 위치)
- ❌ `autospec=True` 누락 → 존재하지 않는 메서드 호출해도 통과
- ❌ `assert mock.called` → `mock.assert_called_once_with(expected)` 사용
- ❌ session-scope fixture에 mutable state → 테스트 간 오염, 간헐적 실패
- ❌ async test가 조용히 skip됨 → pytest-asyncio `mode = "auto"` 설정 누락
- ❌ 간헐적 실패 원인 추적 → `pytest-randomly`로 순서 무작위화 후 재현

## Cross-References

| Topic | Skill |
|-------|-------|
| Python 패턴, 타입 힌트, 동시성 | `python-patterns` |
| Ruff, mypy, formatting, naming | `python-code-style` |
| TDD methodology (general) | `test-driven-development` superpowers |
