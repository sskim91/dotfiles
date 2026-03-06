# Query Optimization Patterns

Deep-dive reference for JPA/Hibernate query performance.

## N+1 Problem: 4 Solutions

The N+1 problem: 1 query fetches N parent entities, then N additional queries fetch each parent's children.

### Solution 1: JOIN FETCH (Most common)

```java
@Query("SELECT o FROM OrderEntity o JOIN FETCH o.items WHERE o.customer.id = :customerId")
List<OrderEntity> findByCustomerWithItems(@Param("customerId") Long customerId);
```

- Loads parent + children in **single SQL query** with JOIN
- Cannot be used with `Pageable` (Hibernate fetches all rows, paginates in memory with warning)
- Best for: loading a single entity with its associations

### Solution 2: @EntityGraph (Declarative)

```java
// Ad-hoc EntityGraph
@EntityGraph(attributePaths = {"items", "customer"})
@Query("SELECT o FROM OrderEntity o WHERE o.status = :status")
List<OrderEntity> findByStatusWithDetails(@Param("status") OrderStatus status);

// Named EntityGraph
@Entity
@NamedEntityGraph(name = "Order.withItems",
    attributeNodes = @NamedAttributeNode("items"))
public class OrderEntity { ... }

// Usage
@EntityGraph(value = "Order.withItems")
List<OrderEntity> findByStatus(OrderStatus status);
```

- Declarative alternative to JOIN FETCH
- Can be combined with derived query methods
- Different methods on same entity can use different graphs
- Best for: multiple use cases needing different fetch strategies

### Solution 3: @BatchSize (Batch loading)

```java
@OneToMany(mappedBy = "order")
@BatchSize(size = 20)
private List<OrderItemEntity> items = new ArrayList<>();
```

- When accessing items of one order, Hibernate batches loading for up to 20 orders' items in a single `IN` query
- Total queries: 1 + ceil(N/batchSize) instead of 1 + N
- Best for: large result sets where JOIN FETCH would cause Cartesian product

Global batch size:
```properties
spring.jpa.properties.hibernate.default_batch_fetch_size=20
```

### Solution 4: Subselect Fetching

```java
@OneToMany(mappedBy = "order")
@Fetch(FetchMode.SUBSELECT)
private List<OrderItemEntity> items = new ArrayList<>();
```

- Loads all children for all loaded parents in a single subselect query
- Total queries: exactly 2 (1 for parents, 1 for all children)
- Best for: when you always need all children for all loaded parents

### Comparison

| Solution | Total Queries | Memory | Pagination | Best For |
|----------|--------------|--------|------------|----------|
| JOIN FETCH | 1 | High (Cartesian) | No | Single entity + associations |
| @EntityGraph | 1 | High (Cartesian) | No | Multiple fetch profiles |
| @BatchSize | 1 + ceil(N/size) | Moderate | Yes | Large collections |
| SUBSELECT | 2 | Moderate | Yes | Load all children always |

## MultipleBagFetchException

Thrown when JOIN FETCH is used on 2+ `List` collections simultaneously.

### Wrong "fix" (Set workaround)

```java
// DON'T DO THIS — causes Cartesian product
@OneToMany(mappedBy = "order")
private Set<OrderItemEntity> items = new HashSet<>();

@OneToMany(mappedBy = "order")
private Set<OrderNoteEntity> notes = new HashSet<>();
```

Changing List to Set avoids the exception but produces a Cartesian product JOIN — if items has 5 rows and notes has 3 rows, the result set has 15 rows. This gets exponentially worse with more collections.

### Correct fix: Separate queries

```java
@Query("SELECT o FROM OrderEntity o JOIN FETCH o.items WHERE o.id = :id")
Optional<OrderEntity> findWithItems(@Param("id") Long id);

@Query("SELECT o FROM OrderEntity o JOIN FETCH o.notes WHERE o.id = :id")
Optional<OrderEntity> findWithNotes(@Param("id") Long id);

// In service:
@Transactional(readOnly = true)
public OrderDto getOrderWithDetails(Long id) {
    OrderEntity order = orderRepo.findWithItems(id)
        .orElseThrow(() -> new EntityNotFoundException("Order not found"));
    // Second query initializes notes; Hibernate merges into same persistence context
    orderRepo.findWithNotes(id);
    // Now both items and notes are initialized on the same entity
    return OrderDto.from(order);
}
```

Two queries (one per collection) instead of one Cartesian product. Much more efficient.

> **Source**: Vlad Mihalcea — "The best way to fix the Hibernate MultipleBagFetchException"

## Specification Pattern (Dynamic Queries)

For search/filter APIs with variable filter combinations:

```java
// Repository
public interface OrderRepository extends JpaRepository<OrderEntity, Long>,
                                         JpaSpecificationExecutor<OrderEntity> {}

// Specifications
public class OrderSpecs {
    public static Specification<OrderEntity> hasStatus(OrderStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }

    public static Specification<OrderEntity> createdAfter(Instant date) {
        return (root, query, cb) -> cb.greaterThan(root.get("createdAt"), date);
    }

    public static Specification<OrderEntity> titleContains(String keyword) {
        return (root, query, cb) ->
            cb.like(cb.lower(root.get("title")), "%" + keyword.toLowerCase() + "%");
    }

    public static Specification<OrderEntity> customerIdEquals(Long customerId) {
        return (root, query, cb) -> cb.equal(root.get("customer").get("id"), customerId);
    }
}

// Service: compose dynamically
@Transactional(readOnly = true)
public Page<OrderDto> searchOrders(OrderSearchRequest req, Pageable pageable) {
    Specification<OrderEntity> spec = Specification.where(null);

    if (req.status() != null) {
        spec = spec.and(OrderSpecs.hasStatus(req.status()));
    }
    if (req.keyword() != null) {
        spec = spec.and(OrderSpecs.titleContains(req.keyword()));
    }
    if (req.since() != null) {
        spec = spec.and(OrderSpecs.createdAfter(req.since()));
    }
    if (req.customerId() != null) {
        spec = spec.and(OrderSpecs.customerIdEquals(req.customerId()));
    }

    return orderRepository.findAll(spec, pageable)
        .map(OrderDto::from);  // Entity -> DTO mapping
}
```

## Projections

### Interface Projection (Spring generates proxy)

```java
public interface OrderSummary {
    Long getId();
    String getTitle();
    OrderStatus getStatus();
    Instant getCreatedAt();
}

// Repository — Spring auto-generates optimized SELECT
Page<OrderSummary> findAllByStatus(OrderStatus status, Pageable pageable);
```

### Record/Class Projection (Constructor expression)

```java
public record OrderSummaryDto(Long id, String title, OrderStatus status, Instant createdAt) {}

@Query("SELECT new com.example.dto.OrderSummaryDto(o.id, o.title, o.status, o.createdAt) " +
       "FROM OrderEntity o WHERE o.status = :status")
Page<OrderSummaryDto> findSummaries(@Param("status") OrderStatus status, Pageable pageable);
```

### Dynamic Projection (Caller chooses)

```java
<T> List<T> findByStatus(OrderStatus status, Class<T> type);

// Usage
List<OrderSummary> summaries = repo.findByStatus(ACTIVE, OrderSummary.class);
List<OrderEntity> entities = repo.findByStatus(ACTIVE, OrderEntity.class);
```

### Nested Projection

```java
public interface OrderWithCustomer {
    Long getId();
    String getTitle();
    CustomerSummary getCustomer();

    interface CustomerSummary {
        Long getId();
        String getName();
    }
}
```

### When to use which

| Type | SQL Optimization | Flexibility | Use Case |
|------|-----------------|-------------|----------|
| Interface | Yes (closed) | High | List/table views, API responses |
| Record/Class | Yes | Medium | Complex DTOs, custom constructors |
| Dynamic | Yes | Highest | Multiple views on same query |
| Entity | No (SELECT *) | Full access | Write operations |

## Bulk Operations

```java
// Bulk update
@Modifying(clearAutomatically = true, flushAutomatically = true)
@Query("UPDATE OrderEntity o SET o.status = :status WHERE o.createdAt < :before")
int bulkUpdateExpired(@Param("status") OrderStatus status, @Param("before") Instant before);

// Bulk delete
@Modifying(clearAutomatically = true)
@Query("DELETE FROM OrderEntity o WHERE o.status = :status AND o.createdAt < :before")
int bulkDeleteOld(@Param("status") OrderStatus status, @Param("before") Instant before);
```

**IMPORTANT**: Bulk operations bypass the persistence context.
- `clearAutomatically = true`: clears L1 cache after execution to avoid stale data
- `flushAutomatically = true`: flushes pending changes before execution

## Pagination Strategies

### Offset-based (Simple)

```java
PageRequest page = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<OrderSummary> result = repo.findAllByStatus(ACTIVE, page);
// result.getTotalElements(), result.getTotalPages(), result.getContent()
```

- Easy to implement
- **Problem**: `OFFSET 10000` still scans 10,000 rows — gets slower with deeper pages

### Keyset/Cursor-based (Scalable)

```java
// JPQL: row value comparison not supported, use explicit conditions
@Query("SELECT o FROM OrderEntity o " +
       "WHERE o.status = :status " +
       "AND (o.createdAt < :lastCreatedAt " +
       "     OR (o.createdAt = :lastCreatedAt AND o.id < :lastId)) " +
       "ORDER BY o.createdAt DESC, o.id DESC")
List<OrderEntity> findNextPage(@Param("status") OrderStatus status,
                                @Param("lastCreatedAt") Instant lastCreatedAt,
                                @Param("lastId") Long lastId,
                                Pageable pageable);

// Or with native SQL (PostgreSQL/MySQL 8+): row value comparison is supported
@Query(value = "SELECT * FROM orders " +
       "WHERE status = :status AND (created_at, id) < (:lastCreatedAt, :lastId) " +
       "ORDER BY created_at DESC, id DESC",
       nativeQuery = true)
List<OrderEntity> findNextPageNative(@Param("status") String status,
                                      @Param("lastCreatedAt") Instant lastCreatedAt,
                                      @Param("lastId") Long lastId,
                                      Pageable pageable);
```

- Constant performance regardless of page depth
- Requires compound cursor (usually timestamp + id)
- Cannot jump to arbitrary page — only next/previous
- JPQL requires expanded OR condition; native SQL supports `(col1, col2) < (val1, val2)`

### Slice (No total count query)

```java
Slice<OrderSummary> findAllByStatus(OrderStatus status, Pageable pageable);
```

- Returns `Slice` instead of `Page` — no `COUNT(*)` query
- Use when you only need "has next page?" without total count

## OSIV (Open Session in View) — Disable It

```properties
# CRITICAL: Always disable in production
spring.jpa.open-in-view=false
```

**What OSIV does**: Keeps Hibernate Session open through the entire HTTP request, including the view/controller layer.

**Why it's harmful**:
- DB connections held during view rendering and HTTP response writing
- Lazy loading triggers in controller/view layer — hidden N+1 queries
- Connection pool exhaustion under load
- Violates separation of concerns (data access in presentation layer)
- `HibernateException` may occur in view layer without proper handling

**Spring Boot warning**: Since Spring Boot 2.0, a warning is logged when OSIV is enabled but not explicitly configured.

**Solution**: Fetch everything needed in the `@Service` layer with proper fetch strategies.

> **Sources**: Vlad Mihalcea — "The Open Session in View Anti-Pattern"; Thorben Janssen — thorben-janssen.com

## Caching

### First-Level Cache (L1)

- Per `EntityManager`/Session — always enabled
- Avoid keeping entities across transactions
- Be aware: large result sets fill L1 cache → `em.clear()` periodically for batch processing

### Second-Level Cache (L2)

```java
@Entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class CategoryEntity { ... }
```

```properties
spring.jpa.properties.hibernate.cache.use_second_level_cache=true
spring.jpa.properties.hibernate.cache.region.factory_class=org.hibernate.cache.jcache.JCacheRegionFactory
spring.jpa.properties.javax.cache.provider=org.ehcache.jsr107.EhcacheCachingProvider
```

**Use cautiously** — only for read-heavy, rarely-changing entities (categories, configurations).
Validate eviction strategy carefully. Incorrect cache invalidation causes stale data.

### Query Cache

```java
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
List<CategoryEntity> findAll();
```

- Caches query results, invalidated when any entity of the queried type changes
- Only useful for: static reference data with rare writes

## Batch Write Optimization

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

**Requirement**: ID strategy must be `SEQUENCE` (not `IDENTITY`).

```java
@Transactional
public void importOrders(List<OrderDto> dtos) {
    for (int i = 0; i < dtos.size(); i++) {
        OrderEntity order = toEntity(dtos.get(i));
        entityManager.persist(order);

        if (i > 0 && i % 50 == 0) {
            entityManager.flush();
            entityManager.clear();  // Prevent L1 cache from growing unbounded
        }
    }
}
```

## @QueryHints for Read-Only

```java
@QueryHints(@QueryHint(name = "org.hibernate.readOnly", value = "true"))
@Query("SELECT o FROM OrderEntity o WHERE o.status = :status")
List<OrderEntity> findActiveReadOnly(@Param("status") OrderStatus status);
```

Hibernate skips dirty checking for these entities — reduces memory and CPU overhead on read paths.
