---
name: jpa-patterns
description: Use when designing JPA entities, writing JPQL/Criteria queries, resolving N+1 problems, configuring HikariCP, or choosing ID generation strategies. Do NOT use for raw SQL optimization (use sql-optimization-patterns).
---

# JPA/Hibernate Patterns

Domain-specific intelligence for data modeling, repositories, and performance tuning in Spring Boot.

## CRITICAL Rules

These rules prevent the most common production issues. Violating any causes performance degradation or bugs.

1. **NEVER** use `FetchType.EAGER` on `@OneToMany` or `@ManyToMany` collections
2. **ALWAYS** disable OSIV: `spring.jpa.open-in-view=false`
3. **NEVER** use Lombok `@Data` on entities — breaks equals/hashCode, triggers lazy loading via toString
4. **ALWAYS** use `@Transactional(readOnly = true)` for read-only service methods
5. **NEVER** rely on `hibernate.ddl-auto` in production — use Flyway or Liquibase
6. **ALWAYS** initialize collections: `private List<X> items = new ArrayList<>()`
7. **Prefer** `SEQUENCE` over `IDENTITY` when batch inserts matter
8. **NEVER** return entities directly from controllers — use DTO projections
9. **ALWAYS** add database indexes for columns in WHERE, JOIN, ORDER BY
10. **Keep transactions short** — no HTTP calls or heavy computation inside `@Transactional`

## Decision Trees

### ID Generation Strategy

```
Need distributed/sortable IDs?
 +-- Yes --> UUID v7 or TSID (Hypersistence Utils)
 +-- No
      +-- Need JDBC batch inserts? --> SEQUENCE (allocationSize=50)
      +-- Simple auto-increment OK? --> IDENTITY (no batch optimization)

Always: consider @NaturalId for business keys alongside surrogate key
```

### Fetch Strategy Selection

```
Loading related entities?
 +-- Single association, always needed with parent
 |    --> JOIN FETCH in @Query
 +-- Same entity, different use cases need different associations
 |    --> @EntityGraph (named or ad-hoc)
 +-- Large collection (100+ items)
 |    --> @BatchSize(size=N) or @Fetch(FetchMode.SUBSELECT)
 +-- Multiple collections in one query
 |    --> SEPARATE QUERIES (not Set workaround!)
 +-- Read-only list/table view
      --> DTO Projection (skip entity loading entirely)
```

### Collection Type

```
@ManyToMany --> Set<> (avoid duplicates, proper semantics)
@OneToMany
 +-- Single collection on entity? --> List<> (simpler, most common)
 +-- Multiple collections exist?  --> Set<> (avoids MultipleBagFetchException)
 +-- Need ordering?               --> List<> with @OrderColumn
 +-- Multiple collections + JOIN FETCH needed?
      --> DON'T rely on Set alone! Use separate queries
```

### Query Approach

```
What kind of query?
 +-- Static, well-defined           --> @Query with JPQL
 +-- Dynamic filters (search API)   --> JpaSpecificationExecutor + Specification
 +-- Simple CRUD by single field    --> Derived query method (findByStatus)
 +-- Complex reporting/analytics    --> Native SQL or DTO projection
 +-- Bulk update/delete             --> @Modifying @Query
 +-- Need pagination                --> Pageable + Page/Slice return type
```

## Quick Reference

### Entity Template

```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_orders_status", columnList = "status"),
    @Index(name = "idx_orders_customer_created", columnList = "customer_id, created_at")
})
@EntityListeners(AuditingEntityListener.class)
public class OrderEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
    @SequenceGenerator(name = "order_seq", sequenceName = "order_seq", allocationSize = 50)
    private Long id;

    @Column(nullable = false, length = 100)
    private String title;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private OrderStatus status = OrderStatus.PENDING;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "customer_id", nullable = false)
    private CustomerEntity customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItemEntity> items = new ArrayList<>();

    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;

    // equals/hashCode: Vlad Mihalcea pattern
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderEntity other)) return false;
        return id != null && id.equals(other.getId());
    }

    @Override
    public int hashCode() {
        return getClass().hashCode();
    }

    // Bidirectional sync methods
    public void addItem(OrderItemEntity item) {
        items.add(item);
        item.setOrder(this);
    }

    public void removeItem(OrderItemEntity item) {
        items.remove(item);
        item.setOrder(null);
    }
}
```

Enable auditing:
```java
@Configuration
@EnableJpaAuditing
public class JpaConfig {}
```

### Repository Patterns

```java
public interface OrderRepository extends JpaRepository<OrderEntity, Long>,
                                         JpaSpecificationExecutor<OrderEntity> {

    // Derived query
    Optional<OrderEntity> findByTitle(String title);

    // JOIN FETCH for N+1 prevention
    @Query("SELECT o FROM OrderEntity o JOIN FETCH o.items WHERE o.id = :id")
    Optional<OrderEntity> findWithItems(@Param("id") Long id);

    // @EntityGraph for flexible fetching
    @EntityGraph(attributePaths = {"customer", "items"})
    @Query("SELECT o FROM OrderEntity o WHERE o.id = :id")
    Optional<OrderEntity> findWithDetails(@Param("id") Long id);

    // Record DTO Projection
    @Query("SELECT new com.example.dto.OrderSummaryDto(o.id, o.title, o.status, o.createdAt) " +
           "FROM OrderEntity o WHERE o.status = :status")
    Page<OrderSummaryDto> findSummariesByStatus(@Param("status") OrderStatus status, Pageable pageable);

    // Interface projection
    Page<OrderSummary> findAllByStatus(OrderStatus status, Pageable pageable);

    // Bulk update (bypasses entity lifecycle)
    @Modifying(clearAutomatically = true)
    @Query("UPDATE OrderEntity o SET o.status = :newStatus " +
           "WHERE o.createdAt < :before AND o.status = :oldStatus")
    int bulkUpdateStatus(@Param("newStatus") OrderStatus newStatus,
                         @Param("oldStatus") OrderStatus oldStatus,
                         @Param("before") Instant before);
}

// Interface projection
public interface OrderSummary {
    Long getId();
    String getTitle();
    OrderStatus getStatus();
    Instant getCreatedAt();
}
```

### Transaction Patterns

```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    // Read-only: skips dirty checking, may use replica DB
    @Transactional(readOnly = true)
    public OrderDto getOrder(Long id) {
        return orderRepository.findById(id)
            .map(OrderDto::from)
            .orElseThrow(() -> new EntityNotFoundException("Order not found: " + id));
    }

    // Write: keep scope minimal
    @Transactional
    public OrderDto updateStatus(Long id, OrderStatus newStatus) {
        OrderEntity order = orderRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Order not found: " + id));
        order.setStatus(newStatus);
        return OrderDto.from(order);  // No explicit save — dirty checking handles it
    }
}
```

### Pagination

```java
// Offset-based (simple, slow for deep pages)
PageRequest page = PageRequest.of(pageNumber, 20, Sort.by("createdAt").descending());
Page<OrderSummary> orders = repo.findAllByStatus(OrderStatus.ACTIVE, page);

// Keyset/Cursor-based (fast for deep pages)
@Query("SELECT o FROM OrderEntity o WHERE o.status = :status AND o.id < :lastId " +
       "ORDER BY o.id DESC")
List<OrderEntity> findNextPage(@Param("status") OrderStatus status,
                                @Param("lastId") Long lastId,
                                Pageable pageable);
```

### Connection Pool (HikariCP)

```properties
# Formula: connections = (core_count x 2) + effective_spindle_count
# For 4-core server with SSD: ~10 connections
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000

# Deadlock avoidance formula: pool_size = Tn x (Cm - 1) + 1
# Tn = max threads, Cm = max simultaneous connections per thread

# CRITICAL
spring.jpa.open-in-view=false

# Batch inserts (requires SEQUENCE, not IDENTITY)
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

## Workflow Instructions

### When designing a new entity:

1. Choose ID strategy (see Decision Tree)
2. Apply entity template with auditing
3. Implement equals/hashCode using Vlad Mihalcea pattern
4. Add bidirectional sync methods for `@OneToMany`
5. Add `@Table` indexes for query filter columns
6. For deep patterns: [references/entity-design.md](references/entity-design.md)

### When fixing N+1 queries:

1. Enable SQL logging: `logging.level.org.hibernate.SQL=DEBUG`
2. Identify the lazy-loading trigger point
3. Choose fetch strategy (see Decision Tree)
4. Verify fix with SQL log — should see single JOIN query
5. For complex cases: [references/query-optimization.md](references/query-optimization.md)

### When optimizing read performance:

1. Are you returning entities where projections would suffice?
2. Is OSIV enabled? Disable it
3. `@Transactional(readOnly=true)` on read paths?
4. Indexes exist for WHERE/JOIN/ORDER BY columns?
5. For anti-patterns: [references/anti-patterns.md](references/anti-patterns.md)

### When setting up testing:

1. Use `@DataJpaTest` + Testcontainers (not H2)
2. Enable SQL logging for assertion
3. For patterns: [references/testing-patterns.md](references/testing-patterns.md)

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@ManyToOne(fetch = FetchType.EAGER)` → LAZY 기본, 필요시 JOIN FETCH
- ❌ `equals()/hashCode()`에 `@Id` 사용 → 비즈니스 키 또는 UUID 사용
- ❌ `@Transactional` 누락하고 lazy loading 접근 → LazyInitializationException
- ❌ N+1 해결에 `@EntityGraph` 남용 → JOIN FETCH 또는 DTO projection 우선
- ❌ `@GeneratedValue(strategy = IDENTITY)` batch insert 시 → SEQUENCE 전략 사용

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| N+1 queries in logs | Lazy loading in loop | JOIN FETCH, @EntityGraph, or @BatchSize |
| `LazyInitializationException` | Accessing lazy field outside transaction | Fetch in service layer, or use DTO projection |
| `MultipleBagFetchException` | JOIN FETCH on 2+ List collections | Separate queries, NOT Set workaround |
| Slow batch inserts | Using IDENTITY strategy | Switch to SEQUENCE with allocationSize |
| Connection pool exhaustion | OSIV holding connections | Disable OSIV, shorten transactions |
| Dirty checking overhead on reads | Missing readOnly flag | Add `@Transactional(readOnly = true)` |
| Slow deep pagination | Offset-based with large page number | Switch to keyset/cursor pagination |
| Cascade delete not working | Wrong cascade or missing orphanRemoval | Check CascadeType and `orphanRemoval = true` |
| Entity not updated after bulk op | Bulk @Query bypasses persistence context | Add `@Modifying(clearAutomatically = true)` |
| `DataIntegrityViolationException` | Missing constraint | Add proper @Column constraints and indexes |

## Deep-Dive References

- [Entity Design](references/entity-design.md) — ID strategies, equals/hashCode, inheritance, value objects, soft delete
- [Query Optimization](references/query-optimization.md) — N+1 solutions, Specification, projections, bulk ops, caching
- [Anti-Patterns](references/anti-patterns.md) — Common mistakes with before/after fixes
- [Testing](references/testing-patterns.md) — @DataJpaTest, Testcontainers, SQL assertion

## Authoritative Sources

Patterns derived from:
- **Vlad Mihalcea** — vladmihalcea.com, "High-Performance Java Persistence"
- **Thorben Janssen** — thorben-janssen.com, "Hibernate Tips"
- **Spring Data JPA Reference** — docs.spring.io/spring-data/jpa/reference/
- **HikariCP Wiki** — github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
- **Baeldung** — baeldung.com/spring-data-jpa-tutorial
