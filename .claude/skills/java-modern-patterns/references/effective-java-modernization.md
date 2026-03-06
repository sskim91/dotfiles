# Effective Java in the Java 21+ Era

A modernization guide mapping Joshua Bloch's Effective Java (3rd Edition, 2018) principles
to Java 21-25 idioms. Focuses on items that changed, need reinterpretation, or interact
with modern features in non-obvious ways.

> "The fundamental principles of good API design remain the same, but the tools
> for expressing those principles have become dramatically more powerful."

## Records & Immutability

Items 1, 2, 10-13, 17, 49, 50 — how records change the game.

### Item 17 + 50: Immutability Is Default — But Watch Mutable Components

Records enforce immutability at the language level: fields are `final`, no setters.
But if a component is a mutable type, the record only holds an immutable *reference*
to mutable data.

```java
// TRAP: Record wrapping a mutable collection
record StudentGrades(String name, List<Integer> grades) {}

var grades = new ArrayList<>(List.of(90, 85));
var student = new StudentGrades("Alice", grades);
grades.add(100);           // Mutates the list INSIDE the record!
student.grades().add(50);  // Also mutates it!

// FIX: Defensive copy in compact constructor (EJ Item 50)
record StudentGrades(String name, List<Integer> grades) {
    public StudentGrades {
        grades = List.copyOf(grades);  // Unmodifiable + null-element check
    }
}
// Now both external and internal mutation paths are blocked
```

**Rule**: Any record component of a mutable type (`List`, `Map`, `Set`, `Date`, array)
MUST be defensively copied in the compact constructor.

**Special case — arrays**: Records use reference equality for arrays in `equals()`.
Avoid arrays as record components entirely; prefer `List`.

```java
// BAD: Arrays break equals/hashCode semantics in records
record Matrix(int[][] data) {}
new Matrix(new int[][]{{1}}).equals(new Matrix(new int[][]{{1}}));  // false!

// GOOD: Use List for correct value semantics
record Matrix(List<List<Integer>> data) {
    public Matrix {
        data = data.stream().map(List::copyOf).toList();
    }
}
```

### Items 10-12: equals/hashCode/toString — Records Handle It, Mostly

Records auto-generate all three based on ALL components. This eliminates the most
error-prone boilerplate in Java. But know the edge cases:

| Scenario | Record Behavior | Action Needed |
|----------|----------------|---------------|
| Standard value types (String, int, etc.) | Correct by default | None |
| Float/Double components | Uses `Float.equals()` — NaN equals NaN | Usually fine; be aware of semantics |
| Array components | Reference equality — **broken** | Don't use arrays in records; use List |
| Exclude a field from equality | Not possible — all components participate | Use a class instead, or restructure |
| Custom toString format | Override `toString()` only | Fine to override selectively |

**When to still write a class instead of a record:**
- Need to exclude fields from equals/hashCode
- Need mutable state
- Need inheritance (records are implicitly `final`)
- Entity with identity semantics (JPA `@Entity`)
- Need lazy computation or caching inside the object

### Item 1: Static Factory Methods — Enhanced with Sealed Types

EJ's advice to prefer static factories over constructors gains a new dimension
with sealed types: factories can return different sealed subtypes while the caller
only sees the parent type.

```java
public sealed interface CacheEntry<V> permits Hit, Miss, Expired {
    record Hit<V>(V value, Instant cachedAt) implements CacheEntry<V> {}
    record Miss<V>() implements CacheEntry<V> {}
    record Expired<V>(V staleValue, Instant expiredAt) implements CacheEntry<V> {}

    // Static factory — caller uses CacheEntry<V>, unaware of subtypes
    static <V> CacheEntry<V> lookup(Cache<V> cache, String key) {
        var entry = cache.getRaw(key);
        if (entry == null) return new Miss<>();
        if (entry.isExpired()) return new Expired<>(entry.value(), entry.timestamp());
        return new Hit<>(entry.value(), entry.timestamp());
    }
}

// Caller: exhaustive pattern match — compiler verifies all cases handled
String display = switch (CacheEntry.lookup(cache, "user:42")) {
    case Hit(var user, _)      -> "Found: " + user;
    case Miss()                -> "Not in cache";
    case Expired(var user, _)  -> "Stale: " + user;
};
```

This combines three EJ principles in one:
- **Item 1**: Static factory hides concrete types
- **Item 64**: Caller programs to the `CacheEntry` interface
- **Sealed exhaustiveness**: Compiler ensures no case is missed

### Item 2: Builder Pattern — When Records Aren't Enough

Records require all components at construction time. For objects with many optional
parameters, the Builder pattern (EJ Item 2) is still the right choice.

```java
// Record: great when all fields are required and count is small
record Point(double x, double y) {}

// Builder: still needed for complex optional configuration
public class HttpClientConfig {
    private final Duration timeout;
    private final int maxRetries;
    private final boolean followRedirects;
    private final ProxyConfig proxy;         // optional
    private final SSLContext sslContext;      // optional
    private final List<Interceptor> interceptors;  // optional, accumulating
    // ...more optional fields

    private HttpClientConfig(Builder builder) { ... }

    public static class Builder {
        // Required
        private final Duration timeout;
        // Optional with defaults
        private int maxRetries = 3;
        private boolean followRedirects = true;
        // ...
    }
}
```

**For simple "modify one field" cases, use a wither pattern instead of a builder:**

```java
record ServerConfig(String host, int port, boolean ssl, Duration timeout) {
    // Wither methods — return new instance with one field changed
    ServerConfig withPort(int port) { return new ServerConfig(host, port, ssl, timeout); }
    ServerConfig withSsl(boolean ssl) { return new ServerConfig(host, port, ssl, timeout); }
    ServerConfig withTimeout(Duration t) { return new ServerConfig(host, port, ssl, t); }
}

var config = new ServerConfig("localhost", 8080, false, Duration.ofSeconds(30))
    .withSsl(true)
    .withPort(443);
```

| Situation | Approach |
|-----------|----------|
| All fields required, few fields (2-5) | Record |
| Need named-parameter clarity for many required fields | Record (names are self-documenting) |
| Many optional fields with defaults | Builder |
| Accumulating collections (addInterceptor, addHeader) | Builder |
| Modify one field of an existing immutable object | Wither method on record |

### Item 49: Validate Parameters — Compact Constructors Are the Modern Place

EJ says: validate parameters at the start of every public method. Records provide
a dedicated syntax for this: the compact constructor.

```java
// Compact constructor — parameters are implicit, assignment is automatic
public record EmailAddress(String value) {
    public EmailAddress {
        Objects.requireNonNull(value, "email must not be null");
        if (!value.contains("@")) {
            throw new IllegalArgumentException("Invalid email: " + value);
        }
        value = value.strip().toLowerCase();  // Normalize BEFORE implicit assignment
    }
}

// Multi-field cross-validation
public record DateRange(LocalDate start, LocalDate end) {
    public DateRange {
        Objects.requireNonNull(start, "start");
        Objects.requireNonNull(end, "end");
        if (start.isAfter(end)) {
            throw new IllegalArgumentException(
                "start(%s) must not be after end(%s)".formatted(start, end));
        }
    }
}
```

**Key difference from EJ-era**: In a compact constructor, you validate and normalize
the parameters — then the JVM assigns them to fields automatically. No explicit
`this.field = field;` is needed or allowed.

### Item 13: clone — Irrelevant for Records

EJ devoted an entire item to the pitfalls of `clone()`. Records make this a non-issue:

- Records are immutable — "cloning" is just sharing the reference
- When you need a modified copy, use a wither method (see Item 2 above)
- Records cannot override `clone()` in a meaningful way (all components are already accessible)

```java
record Config(String host, int port) {
    Config withPort(int port) { return new Config(host, port); }
}

Config original = new Config("localhost", 8080);
Config copy = original;  // Safe — immutable, no need to clone
Config modified = original.withPort(9090);  // Wither for modified copies
```

## Sealed Types & Class Design

Items 18, 20, 23 — the design revolution.

### Item 23: Tagged Classes — The Definitive Solution

EJ Item 23 warned against "tagged classes" (a single class with a type field and
switch statements). The advice was to use class hierarchies. Java 21+ provides the
*complete* answer:

```java
// ANTI-PATTERN: Tagged class (EJ's warning)
class Figure {
    enum Shape { RECTANGLE, CIRCLE }
    final Shape shape;
    double length, width;  // for rectangle
    double radius;         // for circle

    double area() {
        return switch (shape) {
            case RECTANGLE -> length * width;
            case CIRCLE -> Math.PI * radius * radius;
        };
    }
}

// EJ's ADVICE (2018): Abstract class hierarchy
// Better, but not exhaustive, can't deconstruct fields in switch

// JAVA 21+ ANSWER: Sealed interface + records
sealed interface Figure permits Rectangle, Circle {}
record Rectangle(double length, double width) implements Figure {}
record Circle(double radius) implements Figure {}

static double area(Figure f) {
    return switch (f) {
        case Rectangle(var l, var w) -> l * w;
        case Circle(var r)           -> Math.PI * r * r;
    };
    // Compiler error if a new subtype is added without handling it here
}
```

Why this surpasses EJ's 2018 advice:
- **Exhaustiveness**: Compiler checks all cases — no forgotten subtypes
- **Deconstruction**: Extract fields directly in the pattern — no casts, no getters
- **Immutability**: Records are immutable by default — no defensive programming
- **Conciseness**: Three lines define a complete data type with equals/hashCode/toString

### Item 18: Composition over Inheritance — Sealed Types ARE Composition

This is subtle but important. `sealed interface + record` looks like inheritance
syntactically (records "implement" the interface), but it functions as **composition**:

- Records carry **data only** — no inherited behavior
- Behavior lives **outside** the hierarchy (in services, utility classes)
- Adding new operations doesn't modify existing types
- The data hierarchy is closed; the operation set is open

```java
// Data definition — stable, rarely changes
sealed interface Event permits OrderPlaced, OrderShipped, OrderCancelled {}
record OrderPlaced(String orderId, Instant at, List<Item> items) implements Event {}
record OrderShipped(String orderId, Instant at, String carrier) implements Event {}
record OrderCancelled(String orderId, Instant at, String reason) implements Event {}

// Operation 1: easy to add without touching Event types
class EventSerializer {
    static String toJson(Event e) {
        return switch (e) { ... };
    }
}

// Operation 2: another operation, zero changes to data types
class EventAnalytics {
    static Duration fulfillmentTime(OrderShipped shipped, OrderPlaced placed) {
        return Duration.between(placed.at(), shipped.at());
    }
}
```

This is the "expression problem" solved for the common case:
**types are stable, operations change frequently** → data-oriented programming.

**EJ's Item 18 still applies directly when:**
- You're working with mutable classes (not records)
- You need to wrap and delegate behavior (Decorator pattern)
- Types are open-ended (not a fixed set of alternatives)

### Item 20: Interfaces over Abstract Classes — Sealed Adds Controlled Extensibility

EJ preferred interfaces because classes can implement multiple interfaces.
Sealed interfaces add a new capability: **compiler-enforced closed hierarchies**.

```java
// Open interface: anyone can implement (EJ's default recommendation)
public interface Converter<S, T> {
    T convert(S source);
}

// Sealed interface: only permitted types (when you need exhaustiveness)
public sealed interface JsonValue permits JsonObject, JsonArray,
        JsonString, JsonNumber, JsonBoolean, JsonNull {}
// Pattern matching on all JSON types — compiler enforced, no default needed
```

**Decision guide:**
- Library API meant for user extension → open `interface`
- Domain model with known, fixed alternatives → `sealed interface`
- Need shared implementation across subtypes → `sealed abstract class` (rare)

## Concurrency Revisited

Items 78-84 — the most transformed chapter in Effective Java.

### Items 78-79: synchronized Is Dangerous with Virtual Threads

EJ centered on `synchronized` as the primary synchronization tool. With virtual
threads, `synchronized` blocks that contain I/O operations cause **thread pinning** —
the virtual thread cannot yield, blocking its carrier thread.

```java
// EJ-ERA: synchronized — DANGEROUS with virtual threads (pins carrier during I/O)
public synchronized User getOrLoad(String id) {
    User user = cache.get(id);
    if (user == null) {
        user = database.findById(id);  // I/O inside synchronized = PINNING
        cache.put(id, user);
    }
    return user;
}

// JAVA 21+: ReentrantLock — does not pin virtual threads
private final ReentrantLock lock = new ReentrantLock();
public User getOrLoad(String id) {
    lock.lock();
    try {
        return cache.computeIfAbsent(id, database::findById);
    } finally {
        lock.unlock();
    }
}

// BEST: ConcurrentHashMap — no explicit locking needed
private final ConcurrentHashMap<String, User> cache = new ConcurrentHashMap<>();
public User getOrLoad(String id) {
    return cache.computeIfAbsent(id, database::findById);
}
```

**Migration priority for existing code:**
1. `synchronized` with NO I/O inside → low risk, migrate opportunistically
2. `synchronized` with I/O inside → **migrate immediately**, causes pinning under load
3. JDK 24+ (JEP 491) fixes pinning in most cases, but `ReentrantLock` remains
   recommended for portability across JDK versions

### Item 80: Executors over Threads — But Never Pool Virtual Threads

EJ said: don't create raw threads; use `ExecutorService` with thread pools. This is
still true for platform threads, but the rules invert for virtual threads:

```java
// EJ-ERA: Pool platform threads (correct, still correct for platform threads)
ExecutorService pool = Executors.newFixedThreadPool(20);
pool.submit(() -> handleRequest(req));

// JAVA 21+: Virtual threads are NOT pooled — one per task, always
// BAD: Putting virtual threads in a fixed pool defeats their purpose
ExecutorService bad = Executors.newFixedThreadPool(20);

// GOOD: Create a fresh virtual thread per task
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var request : requests) {
        executor.submit(() -> handleRequest(request));
    }
}

// BEST: Structured concurrency for related tasks
try (var scope = StructuredTaskScope.open()) {
    var order    = scope.fork(() -> fetchOrder(id));
    var customer = scope.fork(() -> fetchCustomer(id));
    scope.join();
    return combine(order.get(), customer.get());
}
```

| EJ Guidance | Virtual Thread Era |
|-------------|-------------------|
| Use thread pools | Pool **platform** threads only; **never** pool virtual threads |
| Size pool to N*cpu | Irrelevant for VT; use `Semaphore` for backpressure instead |
| Reuse threads to save resources | VTs are ~KB each — create and discard freely |
| `CompletableFuture` for async composition | `StructuredTaskScope` is simpler and safer |

### Item 81: Concurrency Utilities — Updated Arsenal

EJ recommended `CountDownLatch`, `Semaphore`, `ConcurrentHashMap` over `wait/notify`.
All still valid, but structured concurrency provides better alternatives for
common patterns:

| EJ-Era Pattern | Java 21+ Alternative | When to Switch |
|---------------|---------------------|---------------|
| `CountDownLatch` for fan-out/join | `StructuredTaskScope.open()` | Related subtasks with shared lifecycle |
| `CompletableFuture.allOf()` | `StructuredTaskScope.open()` | Parent-child task relationships |
| `CompletableFuture.anyOf()` | `Joiner.anySuccessfulResultOrThrow()` | Race pattern (first-wins) |
| `Semaphore` for rate limiting | Still `Semaphore` | Backpressure with virtual threads |
| `ConcurrentHashMap` | Still `ConcurrentHashMap` | Concurrent shared state — unchanged |
| `ThreadLocal` | `ScopedValue` | Any code running on virtual threads |

**Key insight**: `StructuredTaskScope` is not just syntax sugar over `CountDownLatch`.
It provides **automatic cancellation propagation** — if one subtask fails, siblings
are cancelled and resources cleaned up. `CompletableFuture` chains lack this guarantee.

### Item 83: Lazy Initialization — StableValue Replaces All Patterns (JDK 25 Preview)

EJ Item 83 discusses double-checked locking and the lazy initialization holder class
idiom — both notoriously tricky to get right. JDK 25 introduces `StableValue` (preview)
which makes all of them obsolete:

```java
// EJ-ERA: Double-checked locking (error-prone, subtle memory model requirements)
private volatile ExpensiveResource resource;
public ExpensiveResource getResource() {
    ExpensiveResource result = resource;
    if (result == null) {
        synchronized (this) {
            result = resource;
            if (result == null) {
                resource = result = new ExpensiveResource();
            }
        }
    }
    return result;
}

// EJ-ERA: Lazy initialization holder class (correct but indirect)
private static class ResourceHolder {
    static final ExpensiveResource INSTANCE = new ExpensiveResource();
}
public static ExpensiveResource getResource() {
    return ResourceHolder.INSTANCE;
}

// JDK 25+: StableValue (preview) — simple, correct, JVM-optimized
private final StableValue<ExpensiveResource> resource = StableValue.of();
public ExpensiveResource getResource() {
    return resource.computeIfUnset(ExpensiveResource::new);
    // Computed at most once, thread-safe, constant-foldable by JIT
}
```

**Until StableValue is finalized**: The holder class idiom (for static fields) and
double-checked locking with `volatile` (for instance fields) from EJ remain correct.

### Item 82: Document Thread Safety — More Important Than Ever

With virtual threads, the same code may run on millions of concurrent threads instead
of a bounded pool of tens. Thread safety documentation is **more critical**, not less.

EJ's thread safety levels still apply verbatim:

| Level | Example | Record-Era Note |
|-------|---------|-----------------|
| **Immutable** | Records, `String`, `BigDecimal` | Records land here by default |
| **Unconditionally thread-safe** | `ConcurrentHashMap`, `AtomicLong` | Use for shared mutable state |
| **Conditionally thread-safe** | `Collections.synchronizedMap` | Document which lock protects what |
| **Not thread-safe** | `HashMap`, `ArrayList` | VTs don't change this — millions of VTs make it worse |

## Streams, Lambdas & Collections

Items 42-48, 64 — expanded by Gatherers and Sequenced Collections.

### Items 45-46: Use Streams Judiciously — Gatherers Move the Boundary

EJ warned against overusing streams: when the pipeline gets too complex, fall back
to imperative loops. Gatherers expand what streams can express cleanly, pushing that
boundary further:

```java
// EJ-ERA: Too complex for streams, fall back to imperative loop
// "Collect elements into fixed-size batches"
List<List<Order>> batches = new ArrayList<>();
for (int i = 0; i < orders.size(); i += 50) {
    batches.add(orders.subList(i, Math.min(i + 50, orders.size())));
}

// JAVA 24+: Gatherers make this a clean stream operation
List<List<Order>> batches = orders.stream()
    .gather(Gatherers.windowFixed(50))
    .toList();
```

```java
// EJ-ERA: Running computation requires mutable state, use a loop
List<Double> runningAvg = new ArrayList<>();
double sum = 0;
for (int i = 0; i < prices.size(); i++) {
    sum += prices.get(i);
    runningAvg.add(sum / (i + 1));
}

// JAVA 24+: Gatherers.scan — functional, composable, no mutable state leaks
record Avg(double sum, int count) {
    double value() { return sum / count; }
}
List<Double> runningAvg = prices.stream()
    .gather(Gatherers.scan(() -> new Avg(0, 0),
        (avg, p) -> new Avg(avg.sum() + p, avg.count() + 1)))
    .map(Avg::value)
    .toList();
```

**EJ's core principle endures**: Don't force everything into streams. But Gatherers
handle many cases that previously justified imperative loops — batching, windowing,
running totals, stateful transforms.

### Item 48: Parallel Streams Caution — mapConcurrent Is Often Better

EJ rightly warned that `parallelStream()` is rarely beneficial and can be harmful.
`Gatherers.mapConcurrent()` provides a superior alternative for I/O-bound parallelism:

```java
// EJ WARNING: Don't use parallel streams for I/O
// parallelStream() uses the common ForkJoinPool — designed for CPU work
List<String> results = urls.parallelStream()    // BAD: blocks FJP threads on I/O
    .map(url -> httpClient.fetch(url))
    .toList();

// JAVA 24+: mapConcurrent — bounded I/O parallelism on virtual threads
List<String> results = urls.stream()
    .gather(Gatherers.mapConcurrent(10, url -> httpClient.fetch(url)))
    .toList();
// 10 concurrent virtual threads, backpressure built in, no FJP contention
```

| Scenario | Tool |
|----------|------|
| CPU-bound parallel computation | `parallelStream()` — EJ's cautions still apply |
| I/O-bound concurrent calls (HTTP, DB) | `Gatherers.mapConcurrent(n, fn)` |
| Complex fan-out with error handling and cancellation | `StructuredTaskScope` |

### Item 64: Refer to Objects by Interfaces — New Interfaces to Know

EJ says: declare variables using interface types, not implementations.
Java 21 added `SequencedCollection`, `SequencedSet`, and `SequencedMap` to the
type hierarchy — use them when ordering matters:

```java
// EJ-ERA: Limited interface choices for ordered collections
List<String> items = new ArrayList<>();         // Ordered, but List implies index access
Set<String> seen = new LinkedHashSet<>();       // Ordered, but Set interface hides that

// JAVA 21+: Express ordering intent through the type system
SequencedCollection<String> history = new ArrayList<>();
SequencedSet<String> recentlyUsed = new LinkedHashSet<>();
SequencedMap<String, Integer> lruCache = new LinkedHashMap<>();

// The interface communicates: order matters, first/last access is expected
history.addFirst(urgentItem);
history.addLast(normalItem);
String latest = history.getLast();

// Reversed view — backed by original, not a copy
for (String item : history.reversed()) {
    process(item);
}
```

**Updated decision guide:**
- Just need iteration + size → `Collection`
- Need positional index access → `List`
- Need first/last + ordered iteration (no index) → `SequencedCollection`
- Need uniqueness + insertion order → `SequencedSet`
- Need key-value + insertion/sort order → `SequencedMap`

## Exceptions & Error Handling

Items 69-73 — the ADT complement.

### Items 69-71: Expected Failures as Data, Not Control Flow

EJ's exception guidance is still sound: use exceptions for exceptional conditions
(Item 69), checked exceptions for recoverable conditions (Item 70). But Java 21+
sealed types provide a complementary approach for **expected, non-exceptional outcomes**
that the caller must handle:

```java
// EJ-ERA: Checked exception for "not found" (Item 70)
public User findUser(String email) throws UserNotFoundException {
    User user = repository.findByEmail(email);
    if (user == null) throw new UserNotFoundException(email);
    return user;
}
// Problem: "not found" is expected, not exceptional — try-catch is noisy

// EJ-ERA ALTERNATIVE: Return null (Item 55 says use Optional instead)
public Optional<User> findUser(String email) { ... }
// Problem: Optional can't carry error details — why did it fail?

// JAVA 21+: Result ADT — all outcomes are explicit, compiler-checked
public sealed interface FindResult permits Found, NotFound, DbError {
    record Found(User user) implements FindResult {}
    record NotFound(String email) implements FindResult {}
    record DbError(String message, Exception cause) implements FindResult {}
}

public FindResult findUser(String email) {
    try {
        User user = repository.findByEmail(email);
        return user != null ? new Found(user) : new NotFound(email);
    } catch (DataAccessException e) {
        return new DbError("Database unavailable", e);
    }
}

// Caller: exhaustive handling — compiler verifies all outcomes addressed
String response = switch (findUser(email)) {
    case Found(var user)          -> "Welcome, " + user.name();
    case NotFound(var addr)       -> "No account for " + addr;
    case DbError(var msg, var _)  -> "Service error: " + msg;
};
```

**When to use which:**

| Situation | Approach | Why |
|-----------|----------|-----|
| Programming error (null arg, illegal state) | Unchecked exception (EJ Item 72) | Caller can't recover — fail fast |
| Truly exceptional, must handle (IOException) | Checked exception (EJ Item 70) | Framework/infrastructure contract |
| Expected failure as business logic | Result ADT | Not exceptional; caller must handle each case |
| Multiple distinct outcomes to branch on | Result ADT | Pattern matching makes handling clean |
| API boundary (service → controller) | Result ADT | Maps cleanly to HTTP status codes |

**EJ's Item 73 (throw exceptions appropriate to the abstraction)** combines well with
the ADT approach: translate low-level exceptions into domain-specific result types
at service boundaries, and let callers pattern-match on outcomes rather than catching
abstraction-violating exceptions.

## Migration Quick Reference

| EJ Item | Status | Java 21+ Action |
|---------|--------|-----------------|
| 2: Builder | Changed | Record (required-only); Builder (complex optional); wither (single-field) |
| 10-12: equals/hashCode/toString | Superseded | Record auto-generates all three |
| 13: clone | Superseded | Records are immutable; use wither for modified copies |
| 17: Minimize mutability | Automated | Records enforce; guard mutable components in compact constructor |
| 20: Interfaces > abstract classes | Reinterpret | `sealed interface` adds exhaustive extensibility |
| 23: No tagged classes | Superseded | `sealed interface` + `record` — the definitive answer |
| 45-46: Streams judiciously | Reinterpret | Gatherers expand what streams handle cleanly |
| 47: Return Collection > Stream | Reinterpret | `SequencedCollection` gives richer return types |
| 48: Parallel streams caution | Reinterpret | `Gatherers.mapConcurrent()` for I/O parallelism |
| 50: Defensive copies | Reinterpret | Critical inside record compact constructors |
| 78-79: synchronized | Changed | `ReentrantLock` — `synchronized` pins virtual threads |
| 80: Executors > threads | Changed | Pool platform threads only; **never pool** virtual threads |
| 81: Concurrency utilities | Changed | `StructuredTaskScope` for fan-out; `ScopedValue` over `ThreadLocal` |
| 83: Lazy initialization | Changed | `StableValue` (JDK 25 preview) replaces all patterns |

**Still fully valid (unchanged):** Items 1, 5-9, 15, 18, 42-44, 49, 57-62, 64, 69-77, 82.
Notable: Item 18 (composition) *reinforced* by sealed + records; Item 82 (thread safety docs)
*more critical* with virtual threads; Item 49 now applies in compact constructors;
Item 64 expanded with `SequencedCollection` family.

## Sources

- Joshua Bloch, *Effective Java*, 3rd Edition (Addison-Wesley, 2018)
- Brian Goetz, "Data Oriented Programming in Java" (InfoQ, inside.java)
- Ron Pressler, Alan Bateman — JEP 444: Virtual Threads
- JEP 491: Synchronize Virtual Threads Without Pinning (JDK 24)
- JEP 502: Stable Values (JDK 25, Preview)
- JEP 431: Sequenced Collections
- JEP 485: Stream Gatherers
- Nicolai Parlog, "All New Java Language Features Since Java 21" (inside.java)
- InfoQ Java Trends Report 2025
