# Python Concurrency Deep Dive

Advanced concurrency patterns beyond the basics covered in the main skill.

## Concurrency Model Selection

| Model | Best For | GIL Impact | Key Module |
|-------|----------|------------|------------|
| `threading` | I/O-bound (files, network) | Limited by GIL | `concurrent.futures` |
| `multiprocessing` | CPU-bound (computation) | Bypasses GIL | `concurrent.futures` |
| `asyncio` | High-concurrency I/O | Single-threaded | `asyncio` |
| Free-threaded (3.13+) | True parallelism | No GIL | Experimental |

## asyncio Advanced Patterns

### TaskGroup (Python 3.11+)

Structured concurrency replaces `asyncio.gather()` for better error handling.

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[str]:
    """Fetch URLs with structured concurrency."""
    results: list[str] = []

    async with asyncio.TaskGroup() as tg:
        for url in urls:
            tg.create_task(fetch_one(url, results))

    return results
    # If any task raises, ALL tasks are cancelled and
    # an ExceptionGroup is raised with all errors

async def fetch_one(url: str, results: list[str]) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            results.append(await resp.text())
```

**Why TaskGroup over gather?**

```python
# Bad: gather() silently collects exceptions
results = await asyncio.gather(*tasks, return_exceptions=True)
# Must manually check each result for exceptions

# Good: TaskGroup propagates exceptions immediately
async with asyncio.TaskGroup() as tg:
    for task in tasks:
        tg.create_task(task)
# ExceptionGroup raised if any task fails - no silent failures
```

### Timeout Patterns

```python
# asyncio.timeout (Python 3.11+)
async def fetch_with_timeout(url: str) -> str:
    async with asyncio.timeout(10):  # 10 seconds
        return await fetch(url)

# asyncio.timeout_at for absolute deadline
async def batch_process(items: list[Item]) -> None:
    deadline = asyncio.get_event_loop().time() + 30.0
    for item in items:
        async with asyncio.timeout_at(deadline):
            await process(item)
```

### Semaphore for Rate Limiting

```python
async def fetch_all_limited(urls: list[str], max_concurrent: int = 10) -> list[str]:
    """Fetch URLs with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_limited(url: str) -> str:
        async with semaphore:
            return await fetch(url)

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_limited(url)) for url in urls]

    return [t.result() for t in tasks]
```

### async Generator

```python
async def stream_lines(path: str) -> AsyncIterator[str]:
    """Stream file lines asynchronously."""
    async with aiofiles.open(path) as f:
        async for line in f:
            yield line.strip()

# Usage
async for line in stream_lines("large.log"):
    if "ERROR" in line:
        await alert(line)
```

## threading Advanced Patterns

### Thread-Safe Queue Pipeline

```python
import queue
import threading

def producer(q: queue.Queue[str | None], items: list[str]) -> None:
    for item in items:
        q.put(item)
    q.put(None)  # Sentinel to signal completion

def consumer(q: queue.Queue[str | None], results: list[str]) -> None:
    while True:
        item = q.get()
        if item is None:
            break
        results.append(process(item))
        q.task_done()

def pipeline(items: list[str]) -> list[str]:
    q: queue.Queue[str | None] = queue.Queue(maxsize=100)
    results: list[str] = []

    prod = threading.Thread(target=producer, args=(q, items))
    cons = threading.Thread(target=consumer, args=(q, results))

    prod.start()
    cons.start()
    prod.join()
    cons.join()

    return results
```

### ThreadPoolExecutor with Progress

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_process(items: list[Item], max_workers: int = 4) -> list[Result]:
    """Process items in parallel with progress tracking."""
    results = []
    total = len(items)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(process_item, item): item
            for item in items
        }

        for i, future in enumerate(as_completed(future_to_item), 1):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Failed {item}: {e}")
            print(f"Progress: {i}/{total}")

    return results
```

## multiprocessing Patterns

### Shared State with Manager

```python
from multiprocessing import Manager, Pool

def worker(shared_dict: dict, key: str, value: int) -> None:
    """Worker that updates shared state."""
    shared_dict[key] = value * 2

def parallel_with_shared_state() -> dict:
    with Manager() as manager:
        shared = manager.dict()

        with Pool() as pool:
            pool.starmap(worker, [
                (shared, "a", 1),
                (shared, "b", 2),
                (shared, "c", 3),
            ])

        return dict(shared)
```

### Process Pool with Chunking

```python
from concurrent.futures import ProcessPoolExecutor
import math

def cpu_heavy(n: int) -> bool:
    """CPU-intensive: check if n is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(numbers: list[int]) -> list[int]:
    """Find primes using multiple processes."""
    with ProcessPoolExecutor() as executor:
        results = executor.map(cpu_heavy, numbers, chunksize=1000)
    return [n for n, is_prime in zip(numbers, results) if is_prime]
```

## Anti-Patterns

### Don't Mix asyncio and threading Carelessly

```python
# Bad: Blocking call in async context
async def bad_example():
    result = requests.get(url)  # Blocks the event loop!

# Good: Use async-native library or run_in_executor
async def good_example():
    # Option 1: async library
    async with aiohttp.ClientSession() as session:
        result = await session.get(url)

    # Option 2: run blocking code in executor
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, requests.get, url)
```

### Don't Share Mutable State Without Locks

```python
# Bad: Race condition
counter = 0

def increment():
    global counter
    counter += 1  # Not atomic!

# Good: Use Lock
lock = threading.Lock()
counter = 0

def increment():
    global counter
    with lock:
        counter += 1
```

## When to Use What

```
Need concurrent I/O?
├── Many connections (100+)? → asyncio
├── Few connections? → threading
└── Need simplicity? → concurrent.futures.ThreadPoolExecutor

Need parallel computation?
├── Pure Python math? → multiprocessing
├── NumPy/pandas? → Already releases GIL, use threading
└── Python 3.13+ experimental? → Free-threaded mode

Need both I/O and CPU?
└── asyncio + ProcessPoolExecutor via run_in_executor
```

## Authoritative References

- [Python asyncio docs](https://docs.python.org/3/library/asyncio.html) - Official asyncio reference
- [PEP 654 – Exception Groups](https://peps.python.org/pep-0654/) - ExceptionGroup and except*
- [Real Python: Async IO](https://realpython.com/async-io-python/) - Comprehensive asyncio tutorial
- [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) - ThreadPool/ProcessPool
- [PEP 703 – Free-threaded CPython](https://peps.python.org/pep-0703/) - GIL removal proposal
