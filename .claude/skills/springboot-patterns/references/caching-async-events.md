# Caching, Async & Events

## Caching

Enable: `@EnableCaching` on a `@Configuration` class.

### Basic Usage

```java
@Service
public class ProductService {
    private final ProductRepository repo;

    public ProductService(ProductRepository repo) {
        this.repo = repo;
    }

    @Cacheable(value = "products", key = "#id")
    public Product getById(Long id) {
        return repo.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Product " + id));
    }

    @Cacheable(value = "products", key = "'list:' + #category + ':' + #pageable.pageNumber")
    public Page<Product> listByCategory(String category, Pageable pageable) {
        return repo.findByCategory(category, pageable);
    }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public Product update(Long id, UpdateProductRequest req) {
        // update logic
    }

    @CacheEvict(value = "products", allEntries = true)
    @Transactional
    public void bulkImport(List<CreateProductRequest> requests) {
        // bulk logic
    }
}
```

### Redis Cache Configuration

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public RedisCacheConfiguration cacheConfiguration() {
        return RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10))
            .disableCachingNullValues()
            .serializeValuesWith(
                SerializationPair.fromSerializer(
                    new GenericJackson2JsonRedisSerializer()));
    }

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        return RedisCacheManager.builder(factory)
            .cacheDefaults(cacheConfiguration())
            .withCacheConfiguration("products",
                cacheConfiguration().entryTtl(Duration.ofMinutes(30)))
            .build();
    }
}
```

### Cache Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| Cache not working | Self-invocation (same class) | Extract to separate @Service |
| Stale data | No eviction on write | Add @CacheEvict on mutations |
| Memory leak | No TTL on local cache | Set TTL or use Redis |
| Serialization error | Entity not serializable | Cache DTOs, not entities |

## Async Processing

Enable: `@EnableAsync` on a `@Configuration` class.

### Custom Executor (Production)

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean("taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(new CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

### Async Service

```java
@Service
public class NotificationService {
    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);

    @Async
    public CompletableFuture<Void> sendEmail(String to, String subject) {
        log.info("sending_email to={}", to);
        // send logic
        return CompletableFuture.completedFuture(null);
    }
}
```

**Rules:**
- `@Async` methods must be `public` and called from a different bean (proxy limitation)
- Return `void` or `CompletableFuture<T>`
- Always configure custom executor — default uses `SimpleAsyncTaskExecutor` (no thread reuse)
- Tracing 사용 시 `ContextPropagatingTaskDecorator` 설정 필요 (아래 참조)

### Context Propagation for Tracing

`@Async` 메서드에서 tracing context가 전파되려면 decorator 설정 필요:

```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean
    ContextPropagatingTaskDecorator taskDecorator() {
        return new ContextPropagatingTaskDecorator();
    }

    @Bean("taskExecutor")
    public Executor taskExecutor(ContextPropagatingTaskDecorator decorator) {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setTaskDecorator(decorator);
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}
```

## Application Events

### Event Definition

```java
public record OrderCompletedEvent(Long orderId, Long userId, BigDecimal amount) {}
```

### Publishing

```java
@Service
public class OrderService {
    private final ApplicationEventPublisher publisher;

    public OrderService(ApplicationEventPublisher publisher, /* other deps */) {
        this.publisher = publisher;
    }

    @Transactional
    public Order complete(Long orderId) {
        Order order = // complete logic
        publisher.publishEvent(
            new OrderCompletedEvent(order.getId(), order.getUserId(), order.getAmount()));
        return order;
    }
}
```

### Listening

```java
@Component
public class OrderEventListener {
    private final NotificationService notifications;
    private final AnalyticsService analytics;

    // Synchronous — runs in same thread/transaction
    @EventListener
    public void onOrderCompleted(OrderCompletedEvent event) {
        notifications.sendEmail(event.userId(), "Order completed");
    }

    // After transaction commits — safe for external calls
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void afterOrderCommitted(OrderCompletedEvent event) {
        analytics.trackPurchase(event.orderId(), event.amount());
    }

    // Async listener — non-blocking
    @Async
    @EventListener
    public void onOrderCompletedAsync(OrderCompletedEvent event) {
        // heavy processing
    }
}
```

**When to use which:**

| Listener | Use When |
|----------|----------|
| `@EventListener` | Same-transaction side effects |
| `@TransactionalEventListener(AFTER_COMMIT)` | External API calls, messaging |
| `@Async @EventListener` | Heavy processing, non-critical |

## Scheduled Tasks

Enable: `@EnableScheduling` on a `@Configuration` class.

```java
@Component
public class MaintenanceScheduler {
    private static final Logger log = LoggerFactory.getLogger(MaintenanceScheduler.class);

    @Scheduled(cron = "0 0 3 * * *") // Daily at 3 AM
    public void cleanupExpired() {
        log.info("cleanup_started");
        // cleanup logic
    }

    @Scheduled(fixedDelay = 60_000) // 60s after previous completion
    public void refreshCache() {
        // refresh logic
    }

    @Scheduled(fixedRate = 30_000) // Every 30s regardless of completion
    public void healthCheck() {
        // health check logic
    }
}
```

**Rules:**
- `@Scheduled` methods must be `void` with no parameters
- Use `fixedDelay` for sequential tasks, `fixedRate` for periodic tasks
- Use `@SchedulerLock` (ShedLock) in multi-instance deployments to prevent duplicate execution
