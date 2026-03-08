# Advanced Python Testing Patterns

Beyond the basics: property-based testing, factory patterns, snapshot testing, and essential pytest plugins.

## Property-Based Testing with Hypothesis

Instead of writing individual test cases, describe properties that should always hold true. Hypothesis generates test data automatically.

### Setup

```bash
pip install hypothesis
```

### Basic Usage

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_is_commutative(a: int, b: int):
    """Addition should be commutative for all integers."""
    assert a + b == b + a

@given(st.lists(st.integers()))
def test_sorted_list_is_ordered(lst: list[int]):
    """Sorted list should have every element <= the next."""
    result = sorted(lst)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]

@given(st.text())
def test_encode_decode_roundtrip(s: str):
    """Encoding and decoding should return the original string."""
    assert s.encode("utf-8").decode("utf-8") == s
```

### Common Strategies

```python
from hypothesis import strategies as st

# Primitives
st.integers()                           # Any integer
st.integers(min_value=0, max_value=100) # Bounded integer
st.floats(allow_nan=False)              # Floats without NaN
st.text(min_size=1, max_size=50)        # Non-empty strings
st.booleans()                           # True/False

# Collections
st.lists(st.integers(), min_size=1)     # Non-empty list of ints
st.dictionaries(st.text(), st.integers()) # dict[str, int]
st.tuples(st.integers(), st.text())     # tuple[int, str]
st.sets(st.integers(), max_size=10)     # set of ints

# Composite strategies
st.one_of(st.integers(), st.text())     # int | str
st.none() | st.integers()              # int | None

# Dates and times
from hypothesis.strategies import datetimes, dates, times
st.datetimes()
st.dates()
```

### Custom Strategies (Composite)

```python
from hypothesis import strategies as st
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int

@st.composite
def users(draw):
    """Generate random valid User objects."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L",))))
    domain = draw(st.sampled_from(["example.com", "test.org", "mail.net"]))
    email = f"{name.lower().replace(' ', '.')}@{domain}"
    age = draw(st.integers(min_value=0, max_value=150))
    return User(name=name, email=email, age=age)

@given(users())
def test_user_has_valid_email(user: User):
    """User email should always contain @ and the domain."""
    assert "@" in user.email
    assert user.email.endswith((".com", ".org", ".net"))
```

### Hypothesis Settings

```python
from hypothesis import given, settings, HealthCheck

@settings(
    max_examples=500,           # Run more examples (default: 100)
    deadline=1000,              # 1 second deadline per example
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.lists(st.integers()))
def test_expensive_operation(data):
    result = expensive_sort(data)
    assert len(result) == len(data)
```

### Property Testing Strategy Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Round-trip** | encode/decode is identity | `decode(encode(x)) == x` |
| **Commutativity** | Order doesn't matter | `a + b == b + a` |
| **Invariant** | Property preserved after operation | `len(sorted(lst)) == len(lst)` |
| **Oracle** | Compare with simple reference impl | `my_sort(x) == sorted(x)` |
| **Idempotency** | Repeated application = single | `clean(clean(x)) == clean(x)` |

### Stateful Testing (RuleBasedStateMachine)

Test stateful systems by generating random sequences of operations.

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from hypothesis import strategies as st

class StackMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.model = []  # Simple reference implementation

    @rule(value=st.integers())
    def push(self, value):
        self.stack.append(value)
        self.model.append(value)

    @rule()
    def pop(self):
        if self.model:
            expected = self.model.pop()
            actual = self.stack.pop()
            assert actual == expected

    @invariant()
    def lengths_match(self):
        assert len(self.stack) == len(self.model)

TestStack = StackMachine.TestCase
```

### When to Use Hypothesis

| Scenario | Use Hypothesis? | Why |
|----------|:-:|------|
| Serialization roundtrip | ✅ | Property: encode(decode(x)) == x |
| Sorting algorithms | ✅ | Properties: ordered, same length, same elements |
| Math operations | ✅ | Properties: commutativity, associativity |
| Parser/validator | ✅ | Property: valid input accepted, invalid rejected |
| Stateful systems | ✅ | Random operation sequences find edge cases |
| UI interaction | ❌ | Better with integration/e2e tests |
| External API calls | ❌ | Use mocking instead |

## Factory Patterns for Test Data

### factory_boy — Django/SQLAlchemy Compatible

```bash
pip install factory-boy
```

```python
import factory
from myapp.models import User, Post

class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name")
    email = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '.')}@example.com")
    age = factory.Faker("random_int", min=18, max=80)
    is_active = True

class PostFactory(factory.Factory):
    class Meta:
        model = Post

    title = factory.Faker("sentence")
    content = factory.Faker("paragraph")
    author = factory.SubFactory(UserFactory)

# Usage in tests
def test_user_creation():
    user = UserFactory()
    assert user.name
    assert "@" in user.email

def test_post_with_author():
    post = PostFactory()
    assert post.author.name  # Author auto-created

def test_inactive_user():
    user = UserFactory(is_active=False)  # Override defaults
    assert not user.is_active

# Batch creation
def test_multiple_users():
    users = UserFactory.create_batch(10)
    assert len(users) == 10
```

### polyfactory — Framework Agnostic (Pydantic/dataclass)

```bash
pip install polyfactory
```

```python
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

class UserModel(BaseModel):
    name: str
    email: str
    age: int
    is_active: bool = True

class UserFactory(ModelFactory):
    __model__ = UserModel

# Auto-generates valid data based on type annotations
def test_user():
    user = UserFactory.build()
    assert isinstance(user.name, str)
    assert isinstance(user.age, int)

# Works with dataclasses too
from polyfactory.factories.dataclass_factory import DataclassFactory
from dataclasses import dataclass

@dataclass
class Config:
    host: str
    port: int
    debug: bool = False

class ConfigFactory(DataclassFactory):
    __model__ = Config

def test_config():
    config = ConfigFactory.build()
    assert config.host
    assert isinstance(config.port, int)
```

## Snapshot Testing with syrupy

Capture expected output and automatically detect regressions.

```bash
pip install syrupy
```

```python
# test_snapshots.py
def test_api_response(snapshot):
    """Snapshot test for API response structure."""
    response = get_user_response(user_id=1)
    assert response == snapshot

def test_html_rendering(snapshot):
    """Snapshot test for rendered HTML."""
    html = render_template("user.html", name="Alice")
    assert html == snapshot

def test_complex_data(snapshot):
    """Snapshot test for complex data structures."""
    result = process_data(input_data)
    assert result == snapshot
```

```bash
# First run: creates snapshot files
pytest --snapshot-update

# Subsequent runs: compares against snapshots
pytest

# Update snapshots when behavior intentionally changes
pytest --snapshot-update
```

### When to Use Snapshots

| Scenario | Use Snapshot? | Why |
|----------|:-:|------|
| API response format | ✅ | Detect unintended format changes |
| HTML/template rendering | ✅ | Catch visual regressions |
| Serialization output | ✅ | Ensure consistent format |
| Business logic results | ❌ | Use explicit assertions |
| Random/time-dependent output | ❌ | Snapshots will always differ |

## Essential pytest Plugins

| Plugin | Purpose | Install |
|--------|---------|---------|
| `pytest-cov` | Code coverage | `pip install pytest-cov` |
| `pytest-xdist` | Parallel test execution | `pip install pytest-xdist` |
| `pytest-asyncio` | Async test support | `pip install pytest-asyncio` |
| `pytest-mock` | Enhanced mocking | `pip install pytest-mock` |
| `pytest-randomly` | Randomize test order | `pip install pytest-randomly` |
| `pytest-timeout` | Test timeouts | `pip install pytest-timeout` |
| `pytest-freezegun` | Freeze time in tests | `pip install pytest-freezegun` |
| `hypothesis` | Property-based testing | `pip install hypothesis` |
| `syrupy` | Snapshot testing | `pip install syrupy` |
| `factory-boy` | Test data factories | `pip install factory-boy` |

### pytest-xdist: Parallel Test Execution

```bash
# Run tests on 4 CPU cores
pytest -n 4

# Auto-detect number of cores
pytest -n auto

# Distribute by file
pytest -n 4 --dist loadfile
```

### pytest-mock: Enhanced Mocking

```python
def test_with_mocker(mocker):
    """pytest-mock provides a mocker fixture."""
    # Patch a function
    mock_api = mocker.patch("myapp.api.fetch_data")
    mock_api.return_value = {"status": "ok"}

    result = process()

    mock_api.assert_called_once()
    assert result["status"] == "ok"

    # Spy on a function (call real implementation but track calls)
    spy = mocker.spy(myapp.utils, "validate")
    process_with_validation(data)
    spy.assert_called_once_with(data)
```

### pytest-freezegun: Time Control

```python
import pytest
from datetime import datetime

@pytest.mark.freeze_time("2025-01-15 12:00:00")
def test_time_dependent():
    """Test code that depends on current time."""
    assert datetime.now().year == 2025
    result = get_greeting()
    assert result == "Good afternoon!"
```

## Test Configuration Template

Complete `pyproject.toml` configuration for a well-equipped test setup:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=80",
    "-x",                        # Stop on first failure
    "--tb=short",                # Shorter tracebacks
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "e2e: marks tests as end-to-end tests",
]
filterwarnings = [
    "error",                     # Treat warnings as errors
    "ignore::DeprecationWarning:third_party_lib.*",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]
```

## Authoritative References

- [pytest docs](https://docs.pytest.org/) — Official pytest documentation
- [Hypothesis docs](https://hypothesis.readthedocs.io/) — Property-based testing framework
- [factory_boy docs](https://factoryboy.readthedocs.io/) — Test data factories
- [syrupy docs](https://github.com/syrupy-project/syrupy) — Snapshot testing
- [Real Python: Testing](https://realpython.com/pytest-python-testing/) — Comprehensive pytest tutorial
- [testdriven.io](https://testdriven.io/) — Test-driven development tutorials
- [Python Testing with pytest](https://pragprog.com/titles/bopytest2/) — Brian Okken's book (Pragmatic Bookshelf)
