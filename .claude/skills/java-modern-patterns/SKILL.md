---
name: java-modern-patterns
description: Use when writing Java 21+ code, refactoring to modern idioms, choosing records vs classes, using virtual threads, or applying pattern matching. Do NOT use for JPA (use jpa-patterns) or SQL optimization (use sql-optimization-patterns).
---

# Modern Java 21+ Implementation Patterns

Data-oriented programming, concurrency, and modern API patterns for Java 21 through 25.

## Quick Start

- **Modeling domain types?** → See [Decision Trees](#decision-trees) below, then [DOP reference](references/data-oriented-programming.md)
- **Adopting virtual threads?** → Check [CRITICAL Rules](#critical-rules) #1, #5, #9, then [Concurrency reference](references/virtual-threads-concurrency.md)
- **Migrating from Effective Java patterns?** → [EJ Modernization reference](references/effective-java-modernization.md)

## CRITICAL Rules

These prevent the most common mistakes when adopting modern Java features.

1. **NEVER** use `synchronized` blocks with I/O inside virtual thread tasks — causes thread pinning (fixed in JDK 24+ via JEP 491, but `ReentrantLock` remains portable)
2. **ALWAYS** prefer `sealed interface` + `record` over class hierarchies for modeling domain alternatives
3. **PREFER** `ScopedValue` over `ThreadLocal` with virtual threads — ThreadLocal works but wastes memory at scale
4. **ALWAYS** handle all cases in pattern-matching `switch` — rely on compiler exhaustiveness, avoid `default`
5. **NEVER** pool virtual threads — create a new one per task via `Thread.startVirtualThread()` or `Executors.newVirtualThreadPerTaskExecutor()`
6. **ALWAYS** use records for DTOs, API responses, and value objects — not for JPA entities
7. **NEVER** add mutable state to records — they are transparent carriers of immutable data
8. **PREFER** `switch` expressions over `if-else` chains when branching on type or value
9. **PREFER** `ReentrantLock` over `synchronized` when code may run on virtual threads (required before JDK 24; recommended after for portability)
10. **PREFER** `Gatherers` for custom stream intermediate operations over imperative loops with accumulators

## Decision Trees

### Modeling Domain Types

```
Need to represent a fixed set of alternatives?
 +-- Yes
 |    +-- Each alternative carries data? --> sealed interface + record subtypes (ADT)
 |    +-- Alternatives are just labels?  --> enum
 +-- No
      +-- Pure data carrier, immutable?  --> record
      +-- Need mutable state or identity? --> class
      +-- Need inheritance + encapsulation? --> class (possibly sealed)
```

### Choosing Concurrency Model

```
What kind of concurrent work?
 +-- Independent I/O-bound tasks (HTTP, DB, file)
 |    +-- Need to fan-out & collect results? --> StructuredTaskScope + virtual threads
 |    +-- Fire-and-forget?                   --> Thread.startVirtualThread()
 |    +-- Spring Boot web handler?           --> spring.threads.virtual.enabled=true
 +-- CPU-bound parallel computation
 |    --> Platform threads (ForkJoinPool / parallelStream)
 +-- Scheduled/periodic tasks
 |    --> ScheduledExecutorService with platform threads
 +-- Need to pass context across threads?
      --> ScopedValue (not ThreadLocal)
```

### Pattern Matching Approach

```
What are you switching on?
 +-- sealed interface / sealed class
 |    --> Exhaustive type-pattern switch (no default!)
 +-- record type (need to extract fields)
 |    --> Record deconstruction pattern: case Rect(var w, var h)
 +-- Guarded conditions on patterns
 |    --> Pattern guards: case String s when s.length() > 10
 +-- Mixed types from external API
 |    --> Type patterns with default fallback
 +-- Don't care about the value/variable
      --> Unnamed pattern: case Noise(_)
```

### Stream Operation Choice

```
What kind of transformation?
 +-- Standard map/filter/reduce        --> Built-in Stream ops
 +-- Fixed-size windows (batching)     --> Gatherers.windowFixed(n)
 +-- Sliding window analysis           --> Gatherers.windowSliding(n)
 +-- Stateful one-to-many transform    --> Custom Gatherer with state
 +-- Scan/running accumulation         --> Gatherers.scan(seed, op)
 +-- Limit by condition (takeWhile++)  --> Custom Gatherer
 +-- Simple grouping/collecting        --> Collectors (terminal op)
```

## Quick Reference

### Algebraic Data Type (ADT) Template

```java
// Sealed interface = sum type (choice)
// Record = product type (aggregation)
public sealed interface PaymentResult
        permits PaymentResult.Success, PaymentResult.Declined, PaymentResult.Error {

    record Success(String transactionId, BigDecimal amount) implements PaymentResult {}
    record Declined(String reason, String code) implements PaymentResult {}
    record Error(Exception cause) implements PaymentResult {}
}

// Exhaustive pattern-matching switch
public String describe(PaymentResult result) {
    return switch (result) {
        case Success(var txId, var amount) -> "Paid %s: %s".formatted(amount, txId);
        case Declined(var reason, var _)   -> "Declined: " + reason;  // _ requires JDK 22+
        case Error(var cause)              -> "Error: " + cause.getMessage();
    };
    // No default needed — compiler guarantees exhaustiveness
}
```

### Virtual Threads + Structured Concurrency Template

```java
// Fan-out pattern: call multiple services, collect results
// NOTE: API below is JDK 25. JDK 21-23 uses new StructuredTaskScope.ShutdownOnFailure()
// See references/virtual-threads-concurrency.md for JDK 21 equivalent
public OrderDetails fetchOrderDetails(Long orderId) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {
        Subtask<Order> orderTask    = scope.fork(() -> orderService.findById(orderId));
        Subtask<Customer> custTask  = scope.fork(() -> customerService.findByOrderId(orderId));
        Subtask<List<Item>> itemsTask = scope.fork(() -> itemService.findByOrderId(orderId));

        scope.join();  // Wait for all subtasks

        return new OrderDetails(
            orderTask.get(),
            custTask.get(),
            itemsTask.get()
        );
    }
}
```

### Scoped Values Template

```java
// Replace ThreadLocal with ScopedValue for virtual threads
private static final ScopedValue<UserContext> CURRENT_USER = ScopedValue.newInstance();

// Bind in entry point (controller/filter)
public void handleRequest(UserContext user, Runnable handler) {
    ScopedValue.where(CURRENT_USER, user).run(handler);
}

// Read anywhere in the call chain — no parameter passing needed
public void auditLog(String action) {
    UserContext user = CURRENT_USER.get();  // Inherited by child virtual threads
    logger.info("user={} action={}", user.id(), action);
}
```

### Record Patterns & Guards

```java
// Nested record deconstruction
sealed interface Shape permits Circle, Rect {}
record Circle(Point center, double radius) implements Shape {}
record Rect(Point topLeft, Point bottomRight) implements Shape {}
record Point(double x, double y) {}

public double area(Shape shape) {
    return switch (shape) {
        case Circle(_, var r) when r <= 0 -> 0;  // guard
        case Circle(_, var r)             -> Math.PI * r * r;
        case Rect(Point(var x1, var y1),
                  Point(var x2, var y2))  -> Math.abs((x2 - x1) * (y2 - y1));
    };
}
```

### Stream Gatherers

```java
// Fixed-size batch processing
List<List<Integer>> batches = IntStream.rangeClosed(1, 100)
    .boxed()
    .gather(Gatherers.windowFixed(10))
    .toList();
// [[1..10], [11..20], ..., [91..100]]

// Running average with scan (state must be immutable — return new object each time)
record Avg(double sum, int count) {
    double value() { return sum / count; }
}
List<Double> runningAvg = prices.stream()
    .gather(Gatherers.scan(() -> new Avg(0, 0),
        (avg, price) -> new Avg(avg.sum() + price, avg.count() + 1)))
    .map(Avg::value)
    .toList();
```

### Unnamed Variables & Patterns

```java
// Unused exception variable
try {
    return Integer.parseInt(input);
} catch (NumberFormatException _) {
    return defaultValue;
}

// Unused lambda parameter
map.forEach((_, value) -> process(value));

// Don't care about record component
case Success(_, var amount) -> handleAmount(amount);
```

## Workflow Instructions

### When designing a domain model:

1. Identify the alternatives (sum types) — use `sealed interface`
2. Define each variant's data — use `record` for each permitted subtype
3. Add behavior via pattern-matching `switch` **outside** the hierarchy
4. Leverage exhaustiveness — let the compiler catch missing cases
5. For deep patterns: [references/data-oriented-programming.md](references/data-oriented-programming.md)

### When migrating to virtual threads:

1. Enable in Spring Boot: `spring.threads.virtual.enabled=true`
2. Replace `synchronized` with `ReentrantLock` in I/O-critical paths
3. Replace `ThreadLocal` with `ScopedValue`
4. Detect thread pinning: `-Djdk.tracePinnedThreads=full`
5. For patterns: [references/virtual-threads-concurrency.md](references/virtual-threads-concurrency.md)

### When building concurrent workflows:

1. Identify independent I/O tasks that can run in parallel
2. Use `StructuredTaskScope.open()` to fork subtasks
3. Call `scope.join()` to wait — cancellation propagates automatically
4. Extract results via `subtask.get()`
5. For advanced patterns: [references/virtual-threads-concurrency.md](references/virtual-threads-concurrency.md)

### When modernizing legacy (Effective Java era) code:

1. Identify tagged classes → convert to `sealed interface` + `record`
2. Replace `synchronized` + I/O with `ReentrantLock` (virtual thread safety)
3. Replace `ThreadLocal` with `ScopedValue` where virtual threads are used
4. Add defensive copies in record compact constructors for mutable components
5. For full EJ item mapping: [references/effective-java-modernization.md](references/effective-java-modernization.md)

### When modernizing stream pipelines:

1. Replace imperative accumulation loops with `Gatherers`
2. Use `windowFixed(n)` for batch processing
3. Use `windowSliding(n)` for moving-window analysis
4. Write custom `Gatherer` for complex stateful transforms
5. For examples: [references/modern-api-patterns.md](references/modern-api-patterns.md)

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ sealed class의 permits 절에 모든 서브타입 나열 실패 → exhaustive matching 깨짐
- ❌ record에 mutable 필드(List, Map) 직접 저장 → 방어적 복사 필수 (compact constructor)
- ❌ virtual thread에서 `synchronized` 사용 → pinning 발생, ReentrantLock 사용
- ❌ pattern matching에서 guard 조건 누락 → `case Foo f when f.bar() > 0` 형태로

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Virtual thread hangs under load | Thread pinning from `synchronized` | Replace with `ReentrantLock`; detect with `-Djdk.tracePinnedThreads=full` |
| `NoSuchElementException` from `ScopedValue.get()` | Accessed outside `ScopedValue.where().run()` | Ensure binding exists in the call chain; use `isBound()` to check |
| Compiler error "switch not exhaustive" | Missing case for sealed subtype | Add the missing case — do NOT add `default` (loses exhaustiveness guarantee) |
| `IllegalArgumentException` in record constructor | No validation in compact constructor | Add validation in compact constructor body |
| Virtual threads slower than platform threads | CPU-bound workload, not I/O-bound | Use platform threads / `ForkJoinPool` for CPU-bound work |
| `ClassCastException` in pattern match | Stale pattern after sealed type change | Recompile all classes that switch on the sealed hierarchy |
| Stream Gatherer produces empty result | `Gatherer.finisher()` not invoked | Ensure terminal operation triggers the pipeline (e.g., `.toList()`) |
| Spring `@Async` not using virtual threads | Custom executor overrides default | Configure `AsyncConfigurer` with `Executors.newVirtualThreadPerTaskExecutor()` |
| Gatherer state corrupted in parallel stream | Mutable shared state in `Gatherer.ofSequential` | Use `Gatherer.of()` with combiner, or ensure sequential stream |

## Deep-Dive References

- [Data-Oriented Programming](references/data-oriented-programming.md) — Records, sealed types, ADTs, pattern matching, refactoring from OOP
- [Virtual Threads & Concurrency](references/virtual-threads-concurrency.md) — Virtual threads, structured concurrency, scoped values, Spring Boot integration
- [Modern API Patterns](references/modern-api-patterns.md) — Stream Gatherers, Sequenced Collections, new JDK APIs
- [Effective Java Modernization](references/effective-java-modernization.md) — Effective Java items reinterpreted for Java 21+, migration guide from EJ-era patterns

## Authoritative Sources

Patterns derived from:
- **Brian Goetz** — "Data Oriented Programming in Java" (InfoQ, inside.java)
- **Jose Paumard** — JEP Cafe series, "Clean Code with Records, Sealed Classes and Pattern Matching"
- **Nicolai Parlog** — Inside Java Newscast, "All New Java Language Features Since Java 21"
- **Viktor Klang** — Stream Gatherers design lead (inside.java)
- **InfoQ Java Trends Report 2025** — Industry adoption analysis
- **OpenJDK JEPs** — 440 (Record Patterns), 441 (Pattern Matching for switch), 444 (Virtual Threads), 485 (Stream Gatherers), 505 (Structured Concurrency), 506 (Scoped Values)
- **JDK 25 Performance Improvements** — inside.java (Claes Redestad, Per-Ake Minborg)
