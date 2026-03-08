# Ruff Rules & Pre-commit Guide

Comprehensive guide to ruff rule categories and automated linting setup.

## Ruff Rule Categories

Ruff implements 800+ rules from popular Python linters. Select rules by category prefix.

### Essential Rule Categories (Recommended for all projects)

| Prefix | Origin | Description | Key Rules |
|--------|--------|-------------|-----------|
| `E` | pycodestyle | PEP 8 style errors | Indentation, whitespace, syntax |
| `W` | pycodestyle | PEP 8 style warnings | Trailing whitespace, blank lines |
| `F` | Pyflakes | Logical errors | Unused imports/variables, undefined names |
| `I` | isort | Import sorting | Import order, grouping, sections |
| `B` | flake8-bugbear | Common bugs | Mutable defaults, assert usage, except patterns |
| `UP` | pyupgrade | Modernize code | Replace deprecated syntax with modern Python |

### Recommended Additional Categories

| Prefix | Origin | Description | Key Rules |
|--------|--------|-------------|-----------|
| `C4` | flake8-comprehensions | Optimize comprehensions | Unnecessary list/dict/set calls |
| `SIM` | flake8-simplify | Simplify code | Simplifiable if/else, context managers |
| `PT` | flake8-pytest-style | pytest conventions | Fixture style, assertion patterns |
| `RET` | flake8-return | Return statements | Unnecessary return/else after return |
| `ARG` | flake8-unused-arguments | Unused arguments | Detect unused function arguments |
| `PIE` | flake8-pie | Misc improvements | Unnecessary spread, pass, dict calls |
| `RUF` | Ruff-specific | Ruff originals | Mutable class defaults, ambiguous unicode |
| `PERF` | Perflint | Performance | Unnecessary list(), try-except in loop |

### Security-Focused Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `S` | flake8-bandit | Security vulnerabilities (hardcoded passwords, SQL injection, etc.) |
| `A` | flake8-builtins | Shadowing Python builtins |

### Documentation Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `D` | pydocstyle | Docstring conventions (Google/NumPy style) |

### Style Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `N` | pep8-naming | PEP 8 naming conventions |
| `Q` | flake8-quotes | Quote consistency |
| `COM` | flake8-commas | Trailing comma enforcement |
| `ISC` | flake8-implicit-str-concat | Implicit string concatenation |

### Type Checking Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `TC` | flake8-type-checking | Move imports to TYPE_CHECKING block |
| `FA` | flake8-future-annotations | Future annotations enforcement |
| `ANN` | flake8-annotations | Type annotation coverage enforcement |

### Specialized Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `C90` | mccabe | Cyclomatic complexity limits |
| `DTZ` | flake8-datetimez | Require timezone-aware datetime |
| `T10` | flake8-debugger | Detect debugger statements |
| `T20` | flake8-print | Detect print statements |
| `EM` | flake8-errmsg | Exception message patterns |
| `FBT` | flake8-boolean-trap | Boolean positional arg warnings |
| `BLE` | flake8-blind-except | Overly broad exception catching |
| `ERA` | eradicate | Detect commented-out code |
| `LOG` | flake8-logging | Correct logging usage |
| `G` | flake8-logging-format | Prevent f-strings in logging |
| `INP` | flake8-no-pep420 | Require `__init__.py` |
| `RSE` | flake8-raise | Clean raise statements |
| `SLF` | flake8-self | Private member access detection |
| `SLOT` | flake8-slots | `__slots__` recommendations |
| `TID` | flake8-tidy-imports | Import restrictions |
| `PTH` | flake8-use-pathlib | Replace os.path with pathlib |
| `FIX` | flake8-fixme | Detect FIXME/TODO |
| `TD` | flake8-todos | TODO format enforcement |
| `ASYNC` | flake8-async | Detect blocking calls in async |

### Framework-Specific Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `DJ` | flake8-django | Django patterns |
| `FAST` | FastAPI | FastAPI route patterns |
| `AIR` | Airflow | Airflow DAG patterns |
| `PD` | pandas-vet | pandas best practices |
| `NPY` | NumPy-specific | Deprecated NumPy aliases |

### Advanced Categories

| Prefix | Origin | Description |
|--------|--------|-------------|
| `FURB` | refurb | Modern Python alternatives |
| `FLY` | flynt | f-string conversion |
| `PLC/PLE/PLR/PLW` | Pylint | Convention/Error/Refactor/Warning |
| `TRY` | tryceratops | Exception handling patterns |

## Configuration Templates

### Minimal (New Projects)

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP"]

[tool.ruff.format]
quote-style = "double"
```

### Standard (Recommended)

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # bugbear
    "C4",     # comprehensions
    "UP",     # pyupgrade
    "SIM",    # simplify
    "PT",     # pytest-style
    "RET",    # return
    "RUF",    # ruff-specific
    "PERF",   # perflint
]
ignore = [
    "E501",   # Line too long (handled by formatter)
    "B008",   # Function call in default argument (needed for FastAPI Depends)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",   # Allow assert in tests
    "ARG",    # Unused arguments common in fixtures
    "PT004",  # Fixture doesn't return anything
]
"__init__.py" = [
    "F401",   # Unused imports OK in __init__.py
]

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

### Strict (Maximum Safety)

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = [
    "ALL",    # Enable all rules
]
ignore = [
    "D",       # Docstring rules (configure separately if needed)
    "ANN",     # Type annotations (use mypy instead)
    "E501",    # Line length (formatter handles this)
    "COM812",  # Missing trailing comma (conflicts with formatter)
    "ISC001",  # Implicit string concat (conflicts with formatter)
]

[tool.ruff.lint.pydocstyle]
convention = "google"  # or "numpy"
```

## Pre-commit Setup

### Installation

```bash
pip install pre-commit
```

### Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Ruff - linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0  # Check latest: https://github.com/astral-sh/ruff-pre-commit/releases
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # mypy - type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0  # Check latest
    hooks:
      - id: mypy
        additional_dependencies: []  # Add type stubs here

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: debug-statements        # Detect pdb/breakpoint
      - id: detect-private-key

  # Secrets detection
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.22.1  # Check latest
    hooks:
      - id: gitleaks
```

### Usage

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### CI Integration

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/ruff-action@v3
        with:
          args: "check"
      - uses: astral-sh/ruff-action@v3
        with:
          args: "format --check"
```

## ruff vs Other Tools

| Feature | ruff | black + isort + flake8 | Why ruff wins |
|---------|------|------------------------|---------------|
| Speed | 10-100x faster | Baseline | Written in Rust |
| Config | Single `pyproject.toml` | 3+ config files | Unified config |
| Maintenance | Single dependency | 3+ dependencies | Simpler |
| Auto-fix | 150+ auto-fixable rules | Limited | More automation |
| Formatting | Built-in (replaces black) | Separate tool | All-in-one |

## Common ruff Commands

```bash
# Lint and show errors
ruff check .

# Lint and auto-fix
ruff check --fix .

# Format code (replaces black)
ruff format .

# Check formatting (CI mode)
ruff format --check .

# Show which rules would be selected
ruff check --show-settings | grep select

# Explain a specific rule
ruff rule E501

# Preview upcoming rules
ruff check --preview .
```

## Authoritative References

- [Ruff docs](https://docs.astral.sh/ruff/) — Official ruff documentation
- [Ruff rules reference](https://docs.astral.sh/ruff/rules/) — Complete rule listing
- [pre-commit docs](https://pre-commit.com/) — Pre-commit framework
- [PEP 8](https://peps.python.org/pep-0008/) — Python style guide
- [mypy docs](https://mypy.readthedocs.io/) — Official mypy documentation
- [pyright docs](https://github.com/microsoft/pyright) — Microsoft's type checker
- [Astral blog](https://astral.sh/blog) — ruff and uv announcements
