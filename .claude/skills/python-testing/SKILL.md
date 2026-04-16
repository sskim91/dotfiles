---
name: python-testing
description: Use when writing tests, setting up pytest, implementing TDD, creating fixtures, or mocking dependencies. Do NOT use for general patterns (use python-patterns) or style config (use python-code-style).
paths: "**/*.py, **/pyproject.toml, **/pytest.ini, **/conftest.py"
---

# Python Testing Patterns

판단 기준과 규칙 중심. pytest API가 아닌, **올바른 테스트 전략** 선택을 안내.

## Quick Start

- **테스트 전략 선택?** --> [Test Strategy Decision](#test-strategy-decision) below
- **Fixture 스코프 선택?** --> [Fixture Scope Decision](#fixture-scope-decision) below
- **Mock vs Real 판단?** --> [Mock Decision](#mock-decision) below
- **pytest 설정?** --> [pytest Configuration](#pytest-configuration) below
- **Hypothesis, factory_boy, snapshot?** --> [references/advanced-testing.md](references/advanced-testing.md)
- **커버리지 갭 분석?** --> [Coverage Gap Analysis Template](#coverage-gap-analysis-template) below

## CRITICAL Rules

1. **Test behavior, not implementation** -- 내부 구현이 아닌 입출력/부수효과 검증
2. **One assertion concept per test** -- 하나의 테스트가 하나의 행위 검증
3. **No test interdependence** -- 테스트 순서 무관하게 독립 실행
4. **AAA pattern** -- Arrange-Act-Assert 구조 엄수
5. **Mock at boundaries only** -- 외부 시스템(DB, API, filesystem)만 mock, 내부 로직은 실제 실행
6. **NEVER** `@patch` where you use, not where you define -- `patch("myapp.service.requests.get")` NOT `patch("requests.get")`
7. **ALWAYS** `autospec=True` on mocks -- API 불일치 조기 발견
8. **ALWAYS** 80%+ coverage, critical paths 100% -- `pytest --cov --cov-fail-under=80`
9. **PREFER** `pytest.raises(match=...)` -- 예외 타입 + 메시지 함께 검증
10. **NEVER** test third-party code -- 라이브러리가 동작하는지 테스트하지 마라

## TDD Cycle

```
1. RED    -- Write failing test for desired behavior
2. GREEN  -- Write MINIMAL code to pass (no extras)
3. REFACTOR -- Clean up with tests green
4. REPEAT
```

**Rule:** GREEN에서 "미래에 필요할" 코드 금지. 테스트가 요구하는 것만.

## Test Strategy Decision

```
What are you testing?
+-- Pure logic (no dependencies) --> Unit test (no fixtures, no mocking)
+-- Service with dependencies --> Unit test + mock dependencies
+-- API endpoint --> Integration test (TestClient/httpx)
+-- Database operations --> Integration test + test DB (or Testcontainers)
+-- Full user workflow --> E2E test (sparingly)
+-- Data transformation --> Parametrized test
+-- Serialization/format --> Property-based test (Hypothesis) or Snapshot test
```

### Test Pyramid

| Layer | Ratio | Speed | Dependencies |
|-------|-------|-------|-------------|
| Unit | 70% | ms | None |
| Integration | 20% | seconds | DB, API |
| E2E | 10% | minutes | Full stack |

## Fixture Scope Decision

```
How expensive is setup?
+-- Cheap (in-memory object) --> function (default, safest)
+-- Medium (DB connection) --> module or session
+-- Expensive (Docker container) --> session
+-- Need isolation between tests? --> function (ALWAYS)
+-- Shared read-only data? --> module or session
```

### Key Fixture Patterns

```python
# Setup + Teardown (yield pattern)
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.rollback()
    session.close()

# Parameterized fixture (runs test N times)
@pytest.fixture(params=["sqlite", "postgres"])
def db(request):
    return create_db(request.param)

# Autouse (runs for every test in scope)
@pytest.fixture(autouse=True)
def reset_config():
    Config.reset()
    yield
    Config.cleanup()

# Conftest hierarchy: tests/conftest.py for shared fixtures
# tests/unit/conftest.py for unit-specific fixtures
```

**Rules:**
- `session` scope fixture에 mutable state 금지
- `autouse` 최소한으로 -- 암시적 의존성은 디버깅 어렵게 만듦
- `conftest.py`는 해당 디렉토리 하위에서만 유효

## Mock Decision

```
Should you mock it?
+-- External HTTP API --> YES (unreliable, slow)
+-- Database --> DEPENDS
|    +-- Unit test? --> YES (mock repository)
|    +-- Integration test? --> NO (use test DB)
+-- File system --> YES (use tmp_path fixture instead)
+-- Time/randomness --> YES (freezegun, deterministic seed)
+-- Internal class/function --> NO (test the real thing)
+-- Configuration --> DEPENDS (fixture > mock)
```

### Mock Patterns

```python
# GOOD: patch where imported, with autospec
@patch("myapp.service.payment_client.charge", autospec=True)
def test_process_payment(mock_charge):
    mock_charge.return_value = PaymentResult(success=True)
    result = process_order(order)
    mock_charge.assert_called_once_with(order.amount)

# GOOD: pytest-mock (mocker fixture, cleaner API)
def test_with_mocker(mocker):
    mock_api = mocker.patch("myapp.service.api.fetch", autospec=True)
    mock_api.return_value = {"status": "ok"}
    result = process()
    mock_api.assert_called_once()

# GOOD: Spy (call real impl but track calls)
def test_with_spy(mocker):
    spy = mocker.spy(myapp.utils, "validate")
    process(data)
    spy.assert_called_once_with(data)
```

### Mock Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Mock everything | 테스트가 구현에 종속 | 경계만 mock |
| `patch("requests.get")` | 정의 위치 mock하면 다른 모듈에서 안 잡힘 | 사용 위치 patch |
| `autospec=False` (default) | 존재하지 않는 메서드 호출해도 통과 | `autospec=True` |
| `mock.return_value = Mock()` | 타입 불일치 숨김 | 실제 객체나 dataclass 반환 |
| Mock in integration test | 실제 동작 검증 안 됨 | 실제 의존성 사용 |

## Parametrization

### When to Parametrize

```
Same logic, different inputs? --> @pytest.mark.parametrize
Same test, different backends? --> @pytest.fixture(params=...)
Edge cases + happy path? --> parametrize with ids
```

```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("@no-domain.com", False),
], ids=["valid-email", "missing-at", "missing-domain"])
def test_email_validation(input, expected):
    assert is_valid_email(input) is expected
```

**Rule:** 5개 이상 파라미터면 `ids` 필수 -- 실패 시 어떤 케이스인지 즉시 파악

## Async Testing

```python
# pytest-asyncio mode 설정 (pyproject.toml)
# mode = "auto" -- 모든 async test 자동 인식 (권장)
# mode = "strict" -- @pytest.mark.asyncio 명시 필요

@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("endpoint")
    assert result.status == "ok"

# Mock async function
@pytest.mark.asyncio
async def test_async_mock(mocker):
    mock = mocker.patch("myapp.client.fetch", autospec=True)
    mock.return_value = {"data": []}
    result = await process()
    mock.assert_awaited_once()
```

## Test Organization

```
tests/
+-- conftest.py              # Shared fixtures (DB, client, auth)
+-- unit/
|   +-- conftest.py          # Unit-specific fixtures
|   +-- test_services.py
|   +-- test_models.py
+-- integration/
|   +-- conftest.py          # DB session, test containers
|   +-- test_api.py
|   +-- test_repository.py
+-- e2e/
    +-- test_user_flow.py
```

### Naming Convention

```python
# test_{method}_{scenario}_{expected_result}
def test_create_user_valid_input_returns_user():
def test_create_user_duplicate_email_raises_conflict():
def test_get_user_not_found_returns_none():
```

## pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-x",              # Stop on first failure
    "--tb=short",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: integration tests",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]
```

### CLI Quick Reference

| Command | Use When |
|---------|----------|
| `pytest -x` | 첫 실패에서 멈춤 |
| `pytest --lf` | 마지막 실패한 테스트만 |
| `pytest -k "user"` | 이름 패턴 매칭 |
| `pytest -m "not slow"` | 느린 테스트 제외 |
| `pytest -n auto` | 병렬 실행 (pytest-xdist) |
| `pytest --pdb` | 실패 시 디버거 진입 |

## Coverage Gap Analysis Template

기존 코드의 테스트 커버리지를 분석할 때 사용하는 출력 형식.

```markdown
## Test Coverage Analysis

### Current Coverage
- Tests: [X] tests covering [Y] functions/modules
- Line coverage: [Z]%
- Coverage gaps: [list of uncovered areas]

### Recommended Tests
1. **[test_name]** — [What it verifies, why it matters]
2. **[test_name]** — [What it verifies, why it matters]

### Priority
- Critical: [Tests that catch data loss or security issues]
- High: [Tests for core business logic]
- Medium: [Tests for edge cases and error handling]
- Low: [Tests for utility functions and formatting]
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| 구현 테스트 | 리팩토링하면 테스트 깨짐 | 입출력/행위만 검증 |
| 테스트 간 공유 상태 | 순서 의존성, 간헐적 실패 | fixture로 격리 |
| `assert True` / `assert result` | 실패해도 원인 모름 | 구체적 값 비교 |
| `try/except` in test | 예외 삼킴 | `pytest.raises` 사용 |
| 테스트에 조건문 | 테스트 자체가 버그 가능 | 각 경로를 별도 테스트 |
| `print()` for debugging | 노이즈 | `pytest -s` 또는 `--pdb` |
| 느린 테스트 미분리 | CI 피드백 지연 | `@pytest.mark.slow` |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `patch('module.Class')`  (정의 위치) → `patch('consumer_module.Class')`  (사용 위치)
- ❌ `autospec=True` 누락 → 잘못된 시그니처 감지 불가
- ❌ fixture scope 불일치 (session fixture가 function fixture 의존) → scope 계층 준수
- ❌ `assert mock.called` → `mock.assert_called_once_with(expected)` 사용 (더 명시적)

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| `fixture not found` | conftest.py 위치 잘못 | 해당 디렉토리에 conftest.py 확인 |
| 간헐적 테스트 실패 | 테스트 간 상태 공유 | `pytest-randomly`로 순서 무작위화 후 원인 추적 |
| `patch` 안 먹힘 | 정의 위치가 아닌 사용 위치 patch 필요 | import 경로 확인 |
| async test 무시됨 | `pytest-asyncio` mode 설정 누락 | `mode = "auto"` in pyproject.toml |
| coverage 낮음 | 테스트 경로 불일치 | `[tool.coverage.run] source` 확인 |

## Cross-References

| Topic | Skill |
|-------|-------|
| Python 패턴, 타입 힌트, 동시성 | `python-patterns` |
| Ruff, mypy, formatting, naming | `python-code-style` |
| Hypothesis, factory_boy, snapshot, plugins | [references/advanced-testing.md](references/advanced-testing.md) |
| TDD methodology (general) | `test-driven-development` superpowers |
| pytest 실패 triage, flaky 테스트, git bisect | `debugging` |

## References

- [pytest docs](https://docs.pytest.org/) -- Official documentation
- [pytest-mock docs](https://pytest-mock.readthedocs.io/) -- Enhanced mocking
- [Hypothesis docs](https://hypothesis.readthedocs.io/) -- Property-based testing
- [Real Python: Testing](https://realpython.com/pytest-python-testing/) -- Comprehensive guide
- [Python Testing with pytest](https://pragprog.com/titles/bopytest2/) -- Brian Okken (Pragmatic)
