# Modern Python Features (3.10 ~ 3.14)

Version-by-version guide to Python's most impactful new features.

## Python 3.10 (Oct 2021)

### Structural Pattern Matching (PEP 634, 635, 636)

The `match` statement brings pattern matching to Python.

```python
def handle_command(command: str) -> str:
    match command.split():
        case ["quit"]:
            return "Goodbye!"
        case ["hello", name]:
            return f"Hello, {name}!"
        case ["move", direction, distance]:
            return f"Moving {direction} by {distance}"
        case _:
            return "Unknown command"

# Pattern matching with types
def process_event(event: Event) -> None:
    match event:
        case ClickEvent(x=x, y=y):
            handle_click(x, y)
        case KeyEvent(key="enter"):
            handle_enter()
        case KeyEvent(key=k) if k.isalpha():
            handle_key(k)
```

**Guard clauses in patterns:**

```python
def classify_point(point: tuple[int, int]) -> str:
    match point:
        case (0, 0):
            return "origin"
        case (x, 0) if x > 0:
            return "positive x-axis"
        case (0, y) if y > 0:
            return "positive y-axis"
        case (x, y) if x > 0 and y > 0:
            return "first quadrant"
        case _:
            return "other"
```

**Matching sequences and mappings:**

```python
def process_data(data: dict | list) -> None:
    match data:
        # Match dict with specific keys
        case {"type": "user", "name": str(name), "age": int(age)}:
            create_user(name, age)
        # Match list with at least 2 elements
        case [first, second, *rest]:
            process_items(first, second, rest)
        # Match nested structures
        case {"items": [{"id": int(id_)}, *_]}:
            process_first_item(id_)
```

### Union Type Syntax (PEP 604)

```python
# Before (Python 3.9-)
from typing import Union, Optional

def greet(name: Union[str, None]) -> str: ...
def find(id: Optional[int] = None) -> str: ...

# After (Python 3.10+)
def greet(name: str | None) -> str: ...
def find(id: int | None = None) -> str: ...

# Also works with isinstance
if isinstance(value, str | int):
    process(value)
```

### ParamSpec (PEP 612)

Type-safe decorator typing.

```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec('P')
R = TypeVar('R')

def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that preserves the original function's type signature."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_call
def add(a: int, b: int) -> int:
    return a + b

# Type checker knows: add(a: int, b: int) -> int
```

## Python 3.11 (Oct 2022)

### Exception Groups and except* (PEP 654)

Handle multiple exceptions simultaneously.

```python
# Raising ExceptionGroup
def validate_form(data: dict) -> None:
    errors = []
    if not data.get("name"):
        errors.append(ValueError("Name is required"))
    if not data.get("email"):
        errors.append(ValueError("Email is required"))
    if errors:
        raise ExceptionGroup("Validation failed", errors)

# Catching with except*
try:
    validate_form({})
except* ValueError as eg:
    for e in eg.exceptions:
        print(f"Validation error: {e}")
except* TypeError as eg:
    for e in eg.exceptions:
        print(f"Type error: {e}")
```

### TaskGroup (PEP 654 related)

See [concurrency-deep-dive.md](concurrency-deep-dive.md) for detailed coverage.

```python
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(fetch("url1"))
    task2 = tg.create_task(fetch("url2"))
# All tasks guaranteed complete or cancelled here
```

### Self Type (PEP 673)

```python
from typing import Self

class Builder:
    def set_name(self, name: str) -> Self:
        self.name = name
        return self  # Returns correct subclass type

    def set_value(self, value: int) -> Self:
        self.value = value
        return self

class ExtendedBuilder(Builder):
    def set_extra(self, extra: str) -> Self:
        self.extra = extra
        return self

# Type checker knows this returns ExtendedBuilder, not Builder
result = ExtendedBuilder().set_name("test").set_extra("data")
```

### tomllib - Built-in TOML Parser

```python
import tomllib

with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

# Or from string
data = tomllib.loads('[project]\nname = "myapp"')
print(data["project"]["name"])  # "myapp"
```

### Exception Notes (PEP 678)

```python
try:
    process_batch(items)
except Exception as e:
    e.add_note(f"Processing batch of {len(items)} items")
    e.add_note(f"Failed at index {current_index}")
    raise
# Notes appear in traceback after the exception message
```

### Fine-Grained Error Locations (PEP 657)

```python
# Python 3.11+ provides much better tracebacks:
# Traceback (most recent call last):
#   File "example.py", line 3, in <module>
#     x['a']['b']['c']
#     ~~~~~~~~^^^^^
# TypeError: 'NoneType' object is not subscriptable
```

## Python 3.12 (Oct 2023)

### Type Parameter Syntax (PEP 695)

New, cleaner syntax for generics and type aliases.

```python
# Before (3.11-)
from typing import TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...

# After (3.12+)
class Stack[T]:
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...

# Generic functions
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

# Multiple type parameters
class Mapping[K, V]:
    def get(self, key: K) -> V | None: ...

# Type aliases with type statement
type Point = tuple[float, float]
type Matrix[T] = list[list[T]]
type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
```

### @override Decorator (PEP 698)

```python
from typing import override

class Base:
    def process(self) -> None:
        print("base")

class Child(Base):
    @override
    def process(self) -> None:  # OK
        print("child")

    @override
    def prcess(self) -> None:  # Type checker ERROR: typo, no such method in Base
        print("oops")
```

### Improved f-strings (PEP 701)

```python
# Nested quotes allowed
msg = f"{'hello'}"  # Previously required different quote types
msg = f"result: {d["key"]}"  # Dict access without escaping

# Multi-line f-strings
query = f"""
    SELECT *
    FROM {table_name}
    WHERE id = {user_id}
"""

# Nested f-strings
msg = f"{'=' * 20 + f' {title} ' + '=' * 20}"
```

### Per-Interpreter GIL (PEP 684)

```python
# Each sub-interpreter gets its own GIL
# Enables true parallelism within a single process
# Primarily used via C API, Python API still evolving
import _interpreters  # Low-level API

# This is the foundation for future free-threading work
```

## Python 3.13 (Oct 2024)

### Free-Threaded Mode (PEP 703) — Experimental

CPython can now run without the GIL (Global Interpreter Lock).

```bash
# Install free-threaded build
# python3.13t (the 't' suffix indicates free-threaded)
python3.13t -X gil=0 script.py
```

```python
import threading

# With free-threaded Python, threads can truly run in parallel
# No GIL means CPU-bound threads get real speedup
def cpu_work(n: int) -> int:
    return sum(i * i for i in range(n))

threads = [
    threading.Thread(target=cpu_work, args=(10_000_000,))
    for _ in range(4)
]
for t in threads:
    t.start()
for t in threads:
    t.join()
# Actually runs on 4 cores simultaneously!
```

**Important caveats:**
- Experimental, not default
- Some C extensions may not be compatible
- Performance of single-threaded code may be slightly slower
- Install with `--disable-gil` flag or use `python3.13t`

### JIT Compiler (PEP 744) — Experimental

```bash
# Enable JIT (copy-and-patch JIT compiler)
python3.13 -X jit script.py
PYTHON_JIT=1 python3.13 script.py
```

- Copy-and-patch JIT for improved performance
- Transparent to user code
- Foundation for future optimization work

### typing.TypeIs (PEP 742)

More intuitive type narrowing than `TypeGuard` — narrows in both branches.

```python
from typing import TypeIs

def is_str(val: object) -> TypeIs[str]:
    return isinstance(val, str)

def process(val: str | int) -> None:
    if is_str(val):
        val.upper()    # Type checker knows: val is str
    else:
        val + 1        # Type checker knows: val is int (NOT object!)
    # TypeGuard would NOT narrow the else branch
```

### typing.ReadOnly (PEP 705)

```python
from typing import TypedDict, ReadOnly

class Config(TypedDict):
    host: ReadOnly[str]    # Cannot be modified
    port: ReadOnly[int]    # Cannot be modified
    debug: bool            # Mutable

def update(config: Config) -> None:
    config["debug"] = True   # OK
    config["host"] = "new"   # Type error!
```

### Type Parameter Defaults (PEP 696)

```python
# Type parameters can now have defaults
class Container[T = int]:
    def __init__(self, value: T) -> None:
        self.value = value

c = Container(42)       # T is int (default)
c2 = Container("hello") # T is str (inferred)
```

### warnings.deprecated() (PEP 702)

```python
from warnings import deprecated

@deprecated("Use new_function() instead")
def old_function() -> None: ...

class OldClass:
    @deprecated("Use new_method() instead")
    def old_method(self) -> None: ...

# Works with type checkers AND runtime warnings
```

### Improved Interactive Interpreter

- Multi-line editing with history
- Syntax highlighting and colored tracebacks
- `F1` (help), `F2` (history browse), `F3` (paste mode)
- `exit` and `quit` work without parentheses

### New `copy.replace()`

```python
import copy
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False

config = Config(host="localhost", port=8080)
dev_config = copy.replace(config, debug=True, port=3000)
# Config(host='localhost', port=3000, debug=True)
```

### Deprecated: Global `typing` aliases

```python
# These are deprecated in 3.13:
from typing import List, Dict, Set, Tuple, FrozenSet  # Use list, dict, set, tuple, frozenset

# Deprecated and will be removed in future:
from typing import Optional  # Use X | None
from typing import Union     # Use X | Y
```

## Python 3.14 (Oct 2025)

### Deferred Evaluation of Annotations (PEP 649)

Annotations are no longer evaluated eagerly at function definition time.

```python
# This now works without forward references or quotes!
class Tree:
    def __init__(self, left: Tree | None, right: Tree | None) -> None:
        self.left = left
        self.right = right
    # No need for 'Tree' in quotes - annotation is deferred

# Performance benefit: annotations only evaluated when accessed
# via __annotations__ or typing.get_type_hints()
```

### Template Strings — t-strings (PEP 750)

A new string prefix `t` for template strings that provide safe interpolation.

```python
from string.templatelib import Template

name = "World"
greeting = t"Hello, {name}!"
# greeting is a Template object, NOT a string

# Template objects can be processed by renderers
# that handle escaping, sanitization, etc.

# Use case: SQL injection prevention
def query(template: Template) -> Result:
    """Process template with proper SQL escaping."""
    sql_parts = []
    params = []
    for part in template:
        if isinstance(part, str):
            sql_parts.append(part)
        else:
            sql_parts.append("?")
            params.append(part.value)
    return db.execute("".join(sql_parts), params)

user_input = "Robert'; DROP TABLE users;--"
result = query(t"SELECT * FROM users WHERE name = {user_input}")
# Safe! user_input is a parameter, not interpolated into SQL

# Use case: HTML escaping
from html import escape

def html(template: Template) -> str:
    parts = []
    for part in template:
        if isinstance(part, str):
            parts.append(part)
        else:
            parts.append(escape(str(part.value)))
    return "".join(parts)

user_name = "<script>alert('xss')</script>"
safe_html = html(t"<h1>Welcome, {user_name}!</h1>")
# <h1>Welcome, &lt;script&gt;alert('xss')&lt;/script&gt;!</h1>
```

### concurrent.interpreters (PEP 734)

Multiple interpreters in a single process, each with its own GIL.

```python
import concurrent.interpreters

interp = concurrent.interpreters.create()
interp.run("print('Hello from subinterpreter')")

# Each interpreter has isolated state
# Enables true parallelism without multiprocessing overhead
```

### compression.zstd (PEP 784)

Zstandard compression in the standard library.

```python
from compression import zstd

compressed = zstd.compress(b"data" * 1000)
original = zstd.decompress(compressed)

# Also supported in tarfile, zipfile, shutil
```

### except Without Parentheses (PEP 758)

```python
# When not using 'as', parentheses are now optional
try:
    connect()
except TimeoutError, ConnectionRefusedError:  # No parentheses needed
    print("Connection failed")

# With 'as', parentheses still required
except (TimeoutError, ConnectionRefusedError) as e:
    print(f"Error: {e}")
```

### functools.partial with Placeholder

```python
from functools import partial, Placeholder

# Placeholder for positional arguments
pow2 = partial(pow, Placeholder, 2)  # pow(?, 2)
pow2(3)  # 9

format_hex = partial(format, Placeholder, "x")
format_hex(255)  # "ff"
```

### Other Notable Changes

- **`finally` control flow warning (PEP 765)**: `return`/`break`/`continue` in `finally` blocks now emit `SyntaxWarning`
- **Free-threaded official support (PEP 779)**: Free-threaded builds enter official support phase
- **Incremental GC**: Reduces max pause times for large heaps
- **`annotationlib` module**: For introspecting deferred annotations
- **Calendar versioning**: After 3.14, Python moves to 3.26 (year-based)

## Version Feature Summary

| Feature | Version | PEP | Impact |
|---------|---------|-----|--------|
| `match` statement | 3.10 | 634 | Control flow |
| `X \| Y` union type | 3.10 | 604 | Type hints |
| `ParamSpec` | 3.10 | 612 | Decorator typing |
| `ExceptionGroup` / `except*` | 3.11 | 654 | Error handling |
| `Self` type | 3.11 | 673 | Type hints |
| `tomllib` | 3.11 | 680 | stdlib |
| `TaskGroup` | 3.11 | — | Concurrency |
| Exception Notes | 3.11 | 678 | Error handling |
| `type` statement | 3.12 | 695 | Type aliases |
| `@override` | 3.12 | 698 | OOP |
| Improved f-strings | 3.12 | 701 | Syntax |
| Per-interpreter GIL | 3.12 | 684 | Concurrency |
| Free-threaded mode | 3.13 | 703 | Concurrency |
| JIT compiler | 3.13 | 744 | Performance |
| `TypeIs` | 3.13 | 742 | Type narrowing |
| `ReadOnly` TypedDict | 3.13 | 705 | Type hints |
| `warnings.deprecated()` | 3.13 | 702 | Deprecation |
| `copy.replace()` | 3.13 | — | stdlib |
| Deferred annotations | 3.14 | 649 | Type hints |
| Template strings (t"") | 3.14 | 750 | Security/Templating |
| `concurrent.interpreters` | 3.14 | 734 | Concurrency |
| `compression.zstd` | 3.14 | 784 | stdlib |
| `functools.Placeholder` | 3.14 | — | stdlib |

## Authoritative References

### Official Sources
- [What's New in Python](https://docs.python.org/3/whatsnew/) — Official changelog for every release
- [PEP Index](https://peps.python.org/) — All Python Enhancement Proposals
- [Python Docs](https://docs.python.org/3/) — Official standard library reference
- [Python Insider](https://blog.python.org/) — Core team official blog
- [Python Discuss](https://discuss.python.org/) — Official community discussion forum
- [PyPI](https://pypi.org/) — Python Package Index

### Learning & Tutorials
- [Real Python](https://realpython.com/) — Comprehensive tutorials and guides
- [ArjanCodes](https://arjancodes.com/) — Software design patterns and clean Python
- [mCoding](https://youtube.com/@mCoding) — Python internals and advanced topics
- [Trey Hunner](https://treyhunner.com/) — Pythonic idioms and type hints
- [testdriven.io](https://testdriven.io/) — Testing and deployment tutorials
- [Awesome Python](https://github.com/vinta/awesome-python) — Curated library list

### Core Developer Blogs
- [Guido van Rossum](https://gvanrossum.github.io/) — Python creator, language design
- [Hynek Schlawack](https://hynek.me/) — attrs/structlog author, best practices
- [Brett Cannon](https://snarky.ca/) — Import system, packaging
- [Seth Larson](https://sethmlarson.dev/) — PSF Security, supply chain
