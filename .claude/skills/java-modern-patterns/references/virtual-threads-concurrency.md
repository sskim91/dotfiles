# Virtual Threads & Modern Concurrency

Patterns for virtual threads, structured concurrency, and scoped values in Java 21+.

## Virtual Threads Fundamentals

Virtual threads (JEP 444, finalized in Java 21) are lightweight threads managed by the JVM, not the OS. They are designed for **I/O-bound** workloads where threads spend most time waiting.

### Key Properties

| Property | Platform Threads | Virtual Threads |
|----------|-----------------|-----------------|
| Managed by | OS | JVM (mounted on carrier threads) |
| Memory per thread | ~1MB stack | ~few KB (grows on demand) |
| Max count | Thousands | Millions |
| Best for | CPU-bound work | I/O-bound work (HTTP, DB, file) |
| Pooling | Yes (ThreadPool) | Never pool — create per task |
| `synchronized` | Fine | Causes pinning — use `ReentrantLock` |
| ThreadLocal | Works but expensive | Use ScopedValue instead |

### Creating Virtual Threads

```java
// 1. Simplest — fire and forget
Thread.startVirtualThread(() -> handleRequest(request));

// 2. Thread.Builder for named threads
Thread.ofVirtual()
    .name("worker-", 0)  // worker-0, worker-1, ...
    .start(() -> processTask(task));

// 3. ExecutorService for structured use
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Result>> futures = tasks.stream()
        .map(task -> executor.submit(() -> process(task)))
        .toList();

    List<Result> results = futures.stream()
        .map(f -> {
            try { return f.get(); }
            catch (Exception e) { throw new RuntimeException(e); }
        })
        .toList();
}
```

### Thread Pinning — The #1 Pitfall

When a virtual thread enters a `synchronized` block during I/O, it **pins** to the carrier thread, blocking it. This defeats the purpose of virtual threads.

```java
// BAD: Pins the carrier thread during I/O
public synchronized String fetchData(String url) {
    return httpClient.send(request, BodyHandlers.ofString()).body();
}

// GOOD: ReentrantLock does not pin
private final ReentrantLock lock = new ReentrantLock();

public String fetchData(String url) {
    lock.lock();
    try {
        return httpClient.send(request, BodyHandlers.ofString()).body();
    } finally {
        lock.unlock();
    }
}
```

**Detect pinning at runtime:**
```bash
java -Djdk.tracePinnedThreads=full -jar app.jar
# Prints stack trace whenever a virtual thread pins
```

**JDK 24+ (JEP 491):** `synchronized` no longer pins virtual threads for most cases. But `ReentrantLock` remains the recommended pattern for portability across JDK versions.

### Spring Boot Integration

```yaml
# application.yml — enables virtual threads for Tomcat/Jetty,
# @Async, Kafka/RabbitMQ listeners, RestClient, and more
spring:
  threads:
    virtual:
      enabled: true
```

```java
// If you need a custom executor (e.g., for @Async with specific config)
@Configuration
public class VirtualThreadConfig implements AsyncConfigurer {

    @Override
    public Executor getAsyncExecutor() {
        return Executors.newVirtualThreadPerTaskExecutor();
    }
}
```

**Spring components that use virtual threads when enabled:**
- Tomcat/Jetty request processing
- `@Async` methods (via `applicationTaskExecutor`)
- `@Scheduled` tasks (via `taskScheduler`)
- Kafka `@KafkaListener`
- RabbitMQ `@RabbitListener`
- `RestClient` / `WebClient` (blocking operations)

### When NOT to Use Virtual Threads

- **CPU-bound computation**: Use `ForkJoinPool` or `parallelStream()`
- **Thread-per-core architectures**: Virtual threads add overhead for CPU work
- **Tight loops without I/O**: No yield points, no benefit
- **Legacy code with heavy `synchronized` + I/O**: Migrate to `ReentrantLock` first

## Structured Concurrency

Structured concurrency (JEP 505, preview through JDK 25) treats concurrent tasks as a unit of work tied to a lexical scope. When the scope ends, all child tasks are complete or cancelled.

> **API Version Note**: The API has changed across preview versions. Below uses the JDK 25 API (`StructuredTaskScope.open()`, `Subtask`, `Joiner`). JDK 21-23 used `new StructuredTaskScope.ShutdownOnFailure()` with `throwIfFailed()`. Adapt to your JDK version.

### Core Pattern: Fan-Out and Collect

```java
public record ProductPage(Product product, List<Review> reviews, Inventory stock) {}

// JDK 25 API (StructuredTaskScope.open + Subtask)
public ProductPage getProductPage(String productId) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {
        Subtask<Product> product   = scope.fork(() -> productService.findById(productId));
        Subtask<List<Review>> reviews = scope.fork(() -> reviewService.findByProduct(productId));
        Subtask<Inventory> stock   = scope.fork(() -> inventoryService.check(productId));

        scope.join();  // Blocks until ALL subtasks complete

        return new ProductPage(product.get(), reviews.get(), stock.get());
    }
    // Scope close guarantees: all threads terminated, resources released
}

// JDK 21-23 equivalent API (ShutdownOnFailure)
public ProductPage getProductPageJdk21(String productId) throws Exception {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        Supplier<Product> product   = scope.fork(() -> productService.findById(productId));
        Supplier<List<Review>> reviews = scope.fork(() -> reviewService.findByProduct(productId));
        Supplier<Inventory> stock   = scope.fork(() -> inventoryService.check(productId));

        scope.join().throwIfFailed();

        return new ProductPage(product.get(), reviews.get(), stock.get());
    }
}
```

### Joiner Strategies

```java
// Default: wait for all, propagate first exception
try (var scope = StructuredTaskScope.open()) { ... }

// Succeed on first result (race pattern)
try (var scope = StructuredTaskScope.open(Joiner.anySuccessfulResultOrThrow())) {
    scope.fork(() -> fetchFromPrimary(id));
    scope.fork(() -> fetchFromSecondary(id));
    scope.fork(() -> fetchFromCache(id));

    Result fastest = scope.join();  // Returns first successful result
    // All other tasks are automatically cancelled
}

// Collect all results (including failures)
try (var scope = StructuredTaskScope.open(Joiner.allSuccessfulOrThrow())) {
    scope.fork(() -> callServiceA());
    scope.fork(() -> callServiceB());
    scope.fork(() -> callServiceC());

    List<Result> allResults = scope.join().toList();
}
```

### Error Handling

```java
public OrderDetails fetchOrderDetails(Long orderId) {
    try (var scope = StructuredTaskScope.open()) {
        var orderTask = scope.fork(() -> orderService.findById(orderId));
        var customerTask = scope.fork(() -> customerService.findByOrderId(orderId));

        scope.join();

        // Check individual subtask states
        return switch (orderTask.state()) {
            case SUCCESS -> new OrderDetails(orderTask.get(), customerTask.get());
            case FAILED -> throw new OrderException("Failed to fetch order", orderTask.exception());
            case UNAVAILABLE -> throw new IllegalStateException("Task was cancelled");
        };
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw new RuntimeException("Interrupted while fetching order details", e);
    }
}
```

### Nested Scopes

```java
// Parent scope cancels all children if any fail
public FullReport generateReport(String accountId) throws InterruptedException {
    try (var outer = StructuredTaskScope.open()) {
        var summaryTask = outer.fork(() -> {
            // Inner scope — its own lifecycle, but inherits parent's cancellation
            try (var inner = StructuredTaskScope.open()) {
                var balance = inner.fork(() -> balanceService.get(accountId));
                var txns    = inner.fork(() -> transactionService.recent(accountId));
                inner.join();
                return new Summary(balance.get(), txns.get());
            }
        });

        var alertsTask = outer.fork(() -> alertService.getActive(accountId));

        outer.join();
        return new FullReport(summaryTask.get(), alertsTask.get());
    }
}
```

## Scoped Values

Scoped values (JEP 506, finalized in JDK 25) are immutable, implicitly-shared values bound to a scope. They replace `ThreadLocal` for virtual threads.

### Why Not ThreadLocal?

| Problem with ThreadLocal | ScopedValue Solution |
|-------------------------|---------------------|
| Mutable — any code can overwrite | Immutable once bound |
| Unbounded lifetime — leaks memory | Automatically unbound when scope exits |
| No inheritance control | Automatically inherited by child virtual threads |
| Expensive per-thread copy | Shared across virtual threads in same scope |
| Hard to reason about | Lexically scoped, predictable |

### Basic Usage

```java
public class RequestContext {
    // Declare as static final — the "key"
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();
    static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();
}

// Bind at entry point
public void handleRequest(HttpRequest req) {
    String requestId = UUID.randomUUID().toString();
    User user = authenticate(req);

    ScopedValue.where(RequestContext.REQUEST_ID, requestId)
               .where(RequestContext.CURRENT_USER, user)
               .run(() -> processRequest(req));
}

// Access anywhere in the call chain
public void auditLog(String action) {
    String reqId = RequestContext.REQUEST_ID.get();  // No parameter passing needed
    User user = RequestContext.CURRENT_USER.get();
    logger.info("[{}] user={} action={}", reqId, user.name(), action);
}
```

### With Structured Concurrency

```java
// Child virtual threads automatically inherit scoped values
static final ScopedValue<String> TENANT_ID = ScopedValue.newInstance();

public void processMultiTenantRequest(String tenantId) {
    ScopedValue.where(TENANT_ID, tenantId).run(() -> {
        try (var scope = StructuredTaskScope.open()) {
            // Each forked task can access TENANT_ID.get()
            scope.fork(() -> updateInventory());   // sees tenantId
            scope.fork(() -> sendNotification());  // sees tenantId
            scope.fork(() -> updateAuditLog());    // sees tenantId
            scope.join();
        }
    });
}
```

### Safe Access Pattern

```java
// Check before accessing
if (RequestContext.CURRENT_USER.isBound()) {
    User user = RequestContext.CURRENT_USER.get();
    // use user
} else {
    // Handle case where no user context exists (e.g., system task)
}

// Or use orElse for defaults
String requestId = RequestContext.REQUEST_ID.orElse("system");
```

### Migration from ThreadLocal

```java
// BEFORE: ThreadLocal
private static final ThreadLocal<UserContext> userContext = new ThreadLocal<>();

public void setUser(UserContext ctx) { userContext.set(ctx); }   // Mutable!
public UserContext getUser() { return userContext.get(); }
public void clear() { userContext.remove(); }                    // Easy to forget!

// AFTER: ScopedValue
private static final ScopedValue<UserContext> USER_CONTEXT = ScopedValue.newInstance();

public void withUser(UserContext ctx, Runnable task) {
    ScopedValue.where(USER_CONTEXT, ctx).run(task);  // Bound to scope, auto-cleanup
}

public UserContext getUser() {
    return USER_CONTEXT.get();  // Throws if not bound — fail fast
}
```

## Complete Pattern: Virtual Threads + Structured Concurrency + Scoped Values

```java
@RestController
@RequiredArgsConstructor
public class OrderController {

    static final ScopedValue<String> TRACE_ID = ScopedValue.newInstance();
    private final OrderService orderService;

    @GetMapping("/orders/{id}/details")
    public OrderDetails getOrderDetails(@PathVariable Long id,
                                         @RequestHeader("X-Trace-Id") String traceId) {
        // Bind trace ID to scope — all forked virtual threads inherit it
        return ScopedValue.where(TRACE_ID, traceId)
            .call(() -> orderService.fetchFullDetails(id));
    }
}

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepo;
    private final CustomerClient customerClient;
    private final InventoryClient inventoryClient;

    public OrderDetails fetchFullDetails(Long orderId) throws InterruptedException {
        // Structured concurrency: fan-out to 3 services in parallel
        try (var scope = StructuredTaskScope.open()) {
            var orderTask    = scope.fork(() -> orderRepo.findById(orderId));
            var customerTask = scope.fork(() -> customerClient.getByOrderId(orderId));
            var stockTask    = scope.fork(() -> inventoryClient.checkByOrderId(orderId));

            scope.join();

            // TRACE_ID is available here and in all forked tasks
            String traceId = OrderController.TRACE_ID.get();
            log.info("[{}] Fetched order details for {}", traceId, orderId);

            return new OrderDetails(orderTask.get(), customerTask.get(), stockTask.get());
        }
    }
}
```

## Performance Guidelines

### Tuning Carrier Threads

```bash
# Default: carrier threads = number of available processors
# Override only if benchmarks prove it helps
java -Djdk.virtualThreadScheduler.parallelism=16 \
     -Djdk.virtualThreadScheduler.maxPoolSize=256 \
     -jar app.jar
```

### Backpressure with Semaphore

```java
// Prevent overwhelming downstream services with millions of virtual threads
private final Semaphore limiter = new Semaphore(100);  // max 100 concurrent

public Result process(Request request) throws InterruptedException {
    limiter.acquire();
    try {
        return callDownstreamService(request);
    } finally {
        limiter.release();
    }
}
```

### Monitoring

```java
// JFR events for virtual threads
// Enable: -XX:StartFlightRecording=settings=profile

// Micrometer — use JVM thread metrics (auto-configured by Spring Boot Actuator)
// spring-boot-starter-actuator exposes jvm.threads.* metrics automatically
// For custom virtual thread tracking, use JFR events:
//   jdk.VirtualThreadStart, jdk.VirtualThreadEnd, jdk.VirtualThreadPinned

// Custom application-level concurrency tracking
@Bean
MeterBinder concurrencyMetrics(Semaphore limiter) {
    return registry -> {
        Gauge.builder("app.concurrency.available.permits",
                limiter::availablePermits)
            .description("Available permits for downstream calls")
            .register(registry);
    };
}
```

## Sources

- Ron Pressler, Alan Bateman — JEP 444: Virtual Threads, JEP 505: Structured Concurrency
- Per-Ake Minborg — JEP 506: Scoped Values
- InfoQ: "Spring Boot 3.2 and Spring Framework 6.1 Add Java 21, Virtual Threads Support"
- InfoQ: "Java Concurrency from the Trenches: Lessons Learned in the Wild"
- Inside.java: "Performance Improvements in JDK 25" (Claes Redestad, Per-Ake Minborg)
- Jose Paumard: "Developing an Asynchronous Application with Virtual Threads and Structured Concurrency"
- InfoQ Java Trends Report 2025 — "Spring team now recommends use of Virtual Threads"
- JEP 491: Synchronize Virtual Threads Without Pinning (JDK 24)
