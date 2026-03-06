# JPA/Hibernate Anti-Patterns

Common mistakes in production systems with before/after fixes.

## 1. Entity as DTO (Returning entities from controllers)

```java
// WRONG: Exposes internal structure, triggers lazy loading, serialization issues
@GetMapping("/orders/{id}")
public OrderEntity getOrder(@PathVariable Long id) {
    return orderRepository.findById(id).orElseThrow();
}

// RIGHT: Map to DTO in service layer
@GetMapping("/orders/{id}")
public OrderDto getOrder(@PathVariable Long id) {
    return orderService.getOrder(id);  // Returns DTO
}
```

**Problems**: JSON serialization triggers lazy fields, circular references, exposes DB schema, no control over what's sent.

## 2. Lombok @Data on Entities

```java
// WRONG: @Data generates equals/hashCode with ALL fields
@Data
@Entity
public class OrderEntity {
    @Id @GeneratedValue
    private Long id;
    @OneToMany(mappedBy = "order")
    private List<OrderItemEntity> items;  // Included in equals/hashCode/toString!
}

// RIGHT: Use @Getter @Setter, implement equals/hashCode manually
@Getter @Setter
@Entity
public class OrderEntity {
    @Id @GeneratedValue
    private Long id;
    @OneToMany(mappedBy = "order")
    private List<OrderItemEntity> items;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderEntity other)) return false;
        return id != null && id.equals(other.getId());
    }

    @Override
    public int hashCode() { return getClass().hashCode(); }

    @Override
    public String toString() { return "OrderEntity{id=" + id + "}"; }
}
```

**Problems**:
- `toString()` includes lazy collections → triggers N+1 queries during logging
- `equals()`/`hashCode()` with all fields → entity lost in HashSet after persist
- Circular `toString()` between parent/child → StackOverflowError

## 3. FetchType.EAGER on Collections

```java
// WRONG: Always loads all items, even when not needed
@OneToMany(mappedBy = "order", fetch = FetchType.EAGER)
private List<OrderItemEntity> items;

// RIGHT: Default LAZY + fetch when needed
@OneToMany(mappedBy = "order")  // FetchType.LAZY is default for collections
private List<OrderItemEntity> items = new ArrayList<>();

// Fetch explicitly when needed:
@Query("SELECT o FROM OrderEntity o JOIN FETCH o.items WHERE o.id = :id")
Optional<OrderEntity> findWithItems(@Param("id") Long id);
```

**Problems**: EAGER cascades — if items has EAGER on another relation, you load the entire object graph. Also doesn't work as expected with JPQL (still causes N+1).

## 4. Missing Bidirectional Sync Methods

```java
// WRONG: Only setting one side
order.getItems().add(newItem);
// newItem.order is still null! DB constraint may fail or association broken

// RIGHT: Use sync methods
public void addItem(OrderItemEntity item) {
    items.add(item);
    item.setOrder(this);
}

// Usage
order.addItem(newItem);
```

**Problem**: In-memory state and DB state diverge. The owning side (`@ManyToOne`) must be set for the FK to be populated.

## 5. CascadeType.ALL Everywhere

```java
// WRONG: Cascade everything blindly
@ManyToOne(cascade = CascadeType.ALL)
private CustomerEntity customer;
// Deleting an order cascades delete to customer!

// RIGHT: Cascade only on owning parent -> child relationships
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "customer_id")
private CustomerEntity customer;  // No cascade — customer lifecycle is independent

@OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItemEntity> items;  // Cascade OK — items belong to order
```

**Rule**: Only cascade from parent to child (where child has no meaning without parent). Never cascade from child to parent or between peers.

## 6. N+1 in Loops (Hidden in service layer)

```java
// WRONG: N+1 hidden in loop
@Transactional(readOnly = true)
public List<OrderDto> getActiveOrders() {
    List<OrderEntity> orders = orderRepo.findByStatus(ACTIVE);
    return orders.stream()
        .map(o -> new OrderDto(o.getId(), o.getTitle(),
            o.getItems().size(),           // Triggers lazy load per order!
            o.getCustomer().getName()))     // Another lazy load per order!
        .toList();
}

// RIGHT: Fetch upfront or use projection
@Transactional(readOnly = true)
public List<OrderDto> getActiveOrders() {
    // Option A: JOIN FETCH — loads associations in single query
    return orderRepo.findByStatusWithDetails(ACTIVE).stream()
        .map(OrderDto::from).toList();

    // Option B: DTO Projection (best performance) — skips entity loading entirely
    // return orderRepo.findSummariesByStatus(ACTIVE, Pageable.unpaged())
    //     .getContent().stream().map(OrderDto::fromSummary).toList();
}
```

## 7. Long-Running Transactions

```java
// WRONG: HTTP call inside transaction holds DB connection
@Transactional
public void processOrder(Long orderId) {
    OrderEntity order = orderRepo.findById(orderId).orElseThrow();
    PaymentResult result = paymentApi.charge(order.getTotal());  // HTTP call!
    order.setPaymentId(result.id());
}

// RIGHT: Minimize transaction scope
public void processOrder(Long orderId) {
    OrderDto order = orderService.getOrder(orderId);          // Read transaction
    PaymentResult result = paymentApi.charge(order.total());  // Outside transaction
    orderService.updatePayment(orderId, result.id());         // Short write transaction
}
```

**Problems**: DB connections held during slow external calls → connection pool exhaustion → cascading failures.

## 8. Using hibernate.ddl-auto in Production

```properties
# WRONG
spring.jpa.hibernate.ddl-auto=update  # Unpredictable schema changes in production!

# RIGHT
spring.jpa.hibernate.ddl-auto=validate  # Only validates schema matches entities
# Use Flyway or Liquibase for migrations
```

**Problems**: `update` may create duplicate indexes, won't drop columns, can't handle complex migrations. `create-drop` destroys data.

## 9. Missing Indexes

```java
// WRONG: Query filters on unindexed columns
@Query("SELECT o FROM OrderEntity o WHERE o.status = :status AND o.createdAt > :since")
List<OrderEntity> findRecentByStatus(...);
// Full table scan!

// RIGHT: Add indexes matching query patterns
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_orders_status_created", columnList = "status, created_at")
})
public class OrderEntity { ... }
```

**Rule**: Every column in WHERE, JOIN ON, and ORDER BY should be indexed. Composite indexes should match the query column order.

## 10. select * When Only a Few Columns Needed

```java
// WRONG: Loading full entity for a list view
List<OrderEntity> orders = orderRepo.findAll();
// Loads ALL columns, ALL lazy-initializable proxies

// RIGHT: Use projection
Page<OrderSummary> orders = orderRepo.findAllByStatus(ACTIVE, pageable);
// Selects only id, title, status, createdAt
```

**Impact**: Less data transferred, less memory, no dirty checking overhead, no risk of accidental lazy loading.

> **Source**: Thorben Janssen — "10 Common Hibernate Mistakes That Cripple Your Performance"

## 11. flush() Abuse

```java
// WRONG: Calling flush after every operation
orderRepo.save(order);
entityManager.flush();  // Unnecessary! Hibernate batches writes automatically

// RIGHT: Let Hibernate manage flush timing
orderRepo.save(order);
// Hibernate flushes at transaction commit or before queries that need consistent state
```

**Exception**: Call `flush()` + `clear()` before JPQL bulk operations to avoid stale persistence context.

## 12. Ignoring Hibernate Statistics (Debugging)

Enable during development to catch issues early:

```properties
spring.jpa.properties.hibernate.generate_statistics=true
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE  # Parameter values (Hibernate 6+)
```

Check statistics for:
- Query count per request (detect N+1)
- Second-level cache hit/miss ratio
- Entity fetch/load counts
