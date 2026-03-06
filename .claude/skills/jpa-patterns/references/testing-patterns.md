# JPA Testing Patterns

Practical testing strategies for Spring Data JPA with real databases.

## @DataJpaTest + Testcontainers

### Setup

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TestEntityManager em;
}
```

### Reusable Container (Singleton pattern)

Avoid starting a new container per test class:

```java
public abstract class AbstractRepositoryTest {

    static final PostgreSQLContainer<?> POSTGRES;

    static {
        POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");
        POSTGRES.start();  // Started once, shared across all test classes
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }
}

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class OrderRepositoryTest extends AbstractRepositoryTest {
    // Tests here — container is already running
}
```

### Spring Boot 3.1+ with @ServiceConnection

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {

    @Container
    @ServiceConnection  // Auto-configures datasource properties
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private OrderRepository orderRepository;
}
```

No `@DynamicPropertySource` needed — Spring Boot auto-detects and configures.

## Why Not H2?

| Aspect | H2 | Testcontainers (PostgreSQL) |
|--------|----|-----------------------------|
| SQL dialect | H2 SQL (subtly different) | Production SQL |
| JSON columns | Limited | Full support |
| Window functions | Partial | Full support |
| Indexes | Different behavior | Identical to production |
| Migrations | May fail on dialect differences | Flyway/Liquibase runs identically |
| Confidence | Low — "works in test, fails in prod" | High — same engine |

## SQL Logging for Assertions

### Configuration

```properties
# application-test.properties
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE
spring.jpa.properties.hibernate.generate_statistics=true
```

### Asserting Query Count

Using `hibernate-testing` or manual statistics:

```java
@Test
void findWithItems_shouldExecuteSingleQuery() {
    // Given
    OrderEntity order = createTestOrder(5);  // 5 items

    em.flush();
    em.clear();

    // Reset statistics
    Statistics stats = em.getEntityManager()
        .getEntityManagerFactory()
        .unwrap(SessionFactory.class)
        .getStatistics();
    stats.clear();

    // When
    Optional<OrderEntity> result = orderRepository.findWithItems(order.getId());

    // Then
    assertThat(result).isPresent();
    assertThat(result.get().getItems()).hasSize(5);
    assertThat(stats.getPrepareStatementCount()).isEqualTo(1);  // Single query!
}
```

### Using datasource-proxy for Query Counting

```xml
<!-- pom.xml -->
<dependency>
    <groupId>net.ttddyy</groupId>
    <artifactId>datasource-proxy</artifactId>
    <version>1.10</version>
    <scope>test</scope>
</dependency>
```

```java
@TestConfiguration
public class DataSourceProxyConfig {
    @Bean
    public DataSource dataSource(DataSource original) {
        return ProxyDataSourceBuilder.create(original)
            .countQuery()
            .build();
    }
}
```

## Test Data Setup

### Using TestEntityManager

```java
@Test
void findByStatus_shouldReturnOnlyActiveOrders() {
    // Given
    OrderEntity active = new OrderEntity();
    active.setTitle("Active Order");
    active.setStatus(OrderStatus.ACTIVE);
    em.persistAndFlush(active);

    OrderEntity cancelled = new OrderEntity();
    cancelled.setTitle("Cancelled Order");
    cancelled.setStatus(OrderStatus.CANCELLED);
    em.persistAndFlush(cancelled);

    em.clear();  // Detach entities to force fresh load

    // When
    Page<OrderSummary> result = orderRepository.findAllByStatus(
        OrderStatus.ACTIVE, PageRequest.of(0, 10));

    // Then
    assertThat(result.getContent()).hasSize(1);
    assertThat(result.getContent().get(0).getTitle()).isEqualTo("Active Order");
}
```

### Using @Sql

```java
@Test
@Sql("/test-data/orders.sql")
@Sql(scripts = "/test-data/cleanup.sql", executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
void findRecentOrders_shouldReturnOrdersAfterDate() {
    // Given — data loaded from SQL script

    // When
    List<OrderEntity> result = orderRepository.findRecentByStatus(
        OrderStatus.ACTIVE, Instant.parse("2025-01-01T00:00:00Z"));

    // Then
    assertThat(result).hasSize(3);
}
```

## Testing Specifications

```java
@Test
void specification_shouldFilterByStatusAndKeyword() {
    // Given
    em.persistAndFlush(createOrder("Q4 Planning", OrderStatus.ACTIVE));
    em.persistAndFlush(createOrder("Q4 Budget", OrderStatus.ACTIVE));
    em.persistAndFlush(createOrder("Q3 Planning", OrderStatus.COMPLETED));
    em.clear();

    Specification<OrderEntity> spec = OrderSpecs.hasStatus(OrderStatus.ACTIVE)
        .and(OrderSpecs.titleContains("planning"));

    // When
    List<OrderEntity> result = orderRepository.findAll(spec);

    // Then
    assertThat(result).hasSize(1);
    assertThat(result.get(0).getTitle()).isEqualTo("Q4 Planning");
}
```

## Testing Projections

```java
@Test
void interfaceProjection_shouldReturnOnlySelectedFields() {
    // Given
    em.persistAndFlush(createOrder("Test Order", OrderStatus.ACTIVE));
    em.clear();

    // When
    Page<OrderSummary> result = orderRepository.findAllByStatus(
        OrderStatus.ACTIVE, PageRequest.of(0, 10));

    // Then
    assertThat(result.getContent()).hasSize(1);
    OrderSummary summary = result.getContent().get(0);
    assertThat(summary.getTitle()).isEqualTo("Test Order");
    assertThat(summary.getStatus()).isEqualTo(OrderStatus.ACTIVE);
    // summary has no getItems() — only projected fields available
}
```

## Testing Pagination

```java
@Test
void pagination_shouldReturnCorrectPageInfo() {
    // Given
    for (int i = 0; i < 25; i++) {
        em.persistAndFlush(createOrder("Order " + i, OrderStatus.ACTIVE));
    }
    em.clear();

    // When
    Page<OrderSummary> page = orderRepository.findAllByStatus(
        OrderStatus.ACTIVE, PageRequest.of(1, 10, Sort.by("createdAt").descending()));

    // Then
    assertThat(page.getContent()).hasSize(10);
    assertThat(page.getTotalElements()).isEqualTo(25);
    assertThat(page.getTotalPages()).isEqualTo(3);
    assertThat(page.getNumber()).isEqualTo(1);  // Second page (0-indexed)
}
```

## Testing Auditing

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@EnableJpaAuditing
@Testcontainers
class AuditingTest extends AbstractRepositoryTest {

    @Test
    void save_shouldPopulateAuditFields() {
        // When
        OrderEntity order = new OrderEntity();
        order.setTitle("Audit Test");
        OrderEntity saved = orderRepository.saveAndFlush(order);

        // Then
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getUpdatedAt()).isNotNull();
        assertThat(saved.getCreatedAt()).isEqualTo(saved.getUpdatedAt());
    }

    @Test
    void update_shouldChangeUpdatedAt() throws InterruptedException {
        // Given
        OrderEntity order = orderRepository.saveAndFlush(createOrder("Test", OrderStatus.ACTIVE));
        Instant originalUpdatedAt = order.getUpdatedAt();
        Thread.sleep(10);  // Ensure different timestamp

        // When
        order.setStatus(OrderStatus.COMPLETED);
        orderRepository.saveAndFlush(order);

        // Then
        assertThat(order.getUpdatedAt()).isAfter(originalUpdatedAt);
    }
}
```

## Connection Pool in Tests

Keep test pool small to detect connection leak issues:

```properties
# application-test.properties
spring.datasource.hikari.maximum-pool-size=5
spring.datasource.hikari.minimum-idle=2
spring.datasource.hikari.connection-timeout=5000
spring.datasource.hikari.leak-detection-threshold=10000
```

`leak-detection-threshold`: logs a warning if a connection is held longer than 10 seconds — helps catch missing `@Transactional` or unclosed connections.
