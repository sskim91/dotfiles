# Entity Design Patterns

Deep-dive reference for JPA entity design decisions.

## ID Generation Strategies

### IDENTITY (Auto-Increment)

```java
@Id
@GeneratedValue(strategy = GenerationType.IDENTITY)
private Long id;
```

- Simple, widely supported
- **Disables JDBC batch inserts** — Hibernate must execute INSERT immediately to get the generated ID
- Use for: simple CRUD apps without batch insert requirements

### SEQUENCE (Recommended for performance)

```java
@Id
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
@SequenceGenerator(name = "order_seq", sequenceName = "order_seq", allocationSize = 50)
private Long id;
```

- Allows JDBC batch inserts (Hibernate pre-allocates IDs in memory)
- `allocationSize=50`: Hibernate allocates 50 IDs per DB round-trip
- Requires DB sequence support (PostgreSQL, Oracle, H2; MySQL 8+ via emulation)
- Use for: performance-critical apps, batch inserts

### UUID

```java
@Id
@GeneratedValue(strategy = GenerationType.UUID)
@Column(columnDefinition = "uuid")  // PostgreSQL native UUID type
private UUID id;
```

- Globally unique, no DB dependency, safe for distributed systems
- Larger storage (16 bytes vs 8), poor B-tree index locality with random UUIDs
- **Tip**: Use UUID v7 (time-ordered) for better index performance

### TSID (Time-Sorted ID)

```java
// With Hypersistence Utils
@Id
@Tsid
private Long id;  // Long but globally unique + time-sorted
```

- 64-bit Long, time-sortable, globally unique, excellent index locality
- Best of both worlds: Long type + distributed uniqueness
- Requires Hypersistence Utils library

> **Source**: Vlad Mihalcea — "The best way to generate a TSID entity identifier with JPA and Hibernate"

### Comparison Table

| Strategy | Batch Insert | Distributed | Storage | Index Locality | DB Support |
|----------|-------------|-------------|---------|----------------|------------|
| IDENTITY | No | No | 8 bytes | Excellent | All |
| SEQUENCE | Yes | No | 8 bytes | Excellent | PostgreSQL, Oracle, H2 |
| UUID v4 | Yes | Yes | 16 bytes | Poor | All |
| UUID v7 | Yes | Yes | 16 bytes | Good | All |
| TSID | Yes | Yes | 8 bytes | Excellent | All |

## equals() and hashCode()

### Vlad Mihalcea Pattern (Recommended)

```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof OrderEntity other)) return false;
    return id != null && id.equals(other.getId());
}

@Override
public int hashCode() {
    return getClass().hashCode();  // Constant across all entity states
}
```

**Why this works**:
- `id != null` check: transient entities (id=null) are only equal by reference
- `instanceof` (not `getClass()`): works correctly with Hibernate proxies
- Constant `hashCode()`: entity stays in same hash bucket across persist/merge/detach
- Works in HashSet/HashMap across all entity states (transient, managed, detached)

**Why NOT use all fields**:
- Mutable fields change -> entity moves between hash buckets -> lost in Set/Map
- Lazy fields in hashCode -> triggers unexpected SQL queries
- `@Data` from Lombok uses all fields — never use on entities

> **Source**: Vlad Mihalcea — "How to implement equals and hashCode using the JPA entity identifier"

### @NaturalId Pattern (Business Key)

```java
@Entity
public class BookEntity {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE)
    private Long id;

    @NaturalId
    @Column(nullable = false, unique = true, updatable = false)
    private String isbn;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BookEntity other)) return false;
        return isbn != null && isbn.equals(other.getIsbn());
    }

    @Override
    public int hashCode() {
        return Objects.hash(isbn);  // Stable — isbn never changes
    }
}
```

Lookup: `session.byNaturalId(BookEntity.class).using("isbn", "978-...").load()`

Hibernate caches @NaturalId lookups automatically for performance.

**Criteria for natural key**: truly unique AND truly immutable. If either is questionable, use the ID-based pattern.

> **Source**: Vlad Mihalcea — "The best way to map a @NaturalId business key with JPA and Hibernate"

## Relationship Patterns

### @MapsId for One-to-One

```java
@Entity
public class UserProfileEntity {
    @Id  // Shares the same PK as UserEntity
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "id")
    private UserEntity user;

    private String bio;
    private String avatarUrl;
}
```

Eliminates an extra FK column. The profile table uses the same PK as the user table.

> **Source**: Vlad Mihalcea — "The best way to map a @OneToOne relationship with JPA and Hibernate"

### Bidirectional Sync Methods

Always provide helper methods to keep both sides of a bidirectional relationship in sync:

```java
@Entity
public class ParentEntity {
    @OneToMany(mappedBy = "parent", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ChildEntity> children = new ArrayList<>();

    public void addChild(ChildEntity child) {
        children.add(child);
        child.setParent(this);
    }

    public void removeChild(ChildEntity child) {
        children.remove(child);
        child.setParent(null);
    }
}
```

Without sync methods, the in-memory state diverges from DB state, causing subtle bugs.

### @ManyToOne is always the owner

```java
// Child side (owning side — has the FK column)
@ManyToOne(fetch = FetchType.LAZY)  // CRITICAL: always LAZY
@JoinColumn(name = "parent_id", nullable = false)
private ParentEntity parent;

// Parent side (inverse side — mappedBy)
@OneToMany(mappedBy = "parent")
private Set<ChildEntity> children = new HashSet<>();
```

## Auditing

### Basic (Timestamps)

```java
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity {
    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
```

### With User Tracking

```java
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class JpaConfig {
    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext())
            .map(SecurityContext::getAuthentication)
            .filter(Authentication::isAuthenticated)
            .map(Authentication::getName);
    }
}

@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class AuditableEntity extends BaseEntity {
    @CreatedBy
    @Column(updatable = false)
    private String createdBy;

    @LastModifiedBy
    private String updatedBy;
}
```

## Inheritance Strategies

| Strategy | Performance | Polymorphic Queries | Nullable Columns | When to Use |
|----------|-------------|---------------------|-------------------|-------------|
| `SINGLE_TABLE` | Best (no JOINs) | Fast | Many (subclass fields) | Default choice, simple hierarchy |
| `JOINED` | Moderate (JOINs) | Moderate | None | Many shared fields, strict normalization |
| `TABLE_PER_CLASS` | Poor (UNION) | Slowest | None | Rarely — independent tables |

**Default to SINGLE_TABLE** unless you have strong normalization requirements.

```java
@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "type", discriminatorType = DiscriminatorType.STRING)
public abstract class PaymentEntity {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE)
    private Long id;
    private BigDecimal amount;
    private Instant paidAt;
}

@Entity @DiscriminatorValue("CREDIT_CARD")
public class CreditCardPaymentEntity extends PaymentEntity {
    private String lastFourDigits;
    private String expiryMonth;
}

@Entity @DiscriminatorValue("BANK_TRANSFER")
public class BankTransferPaymentEntity extends PaymentEntity {
    private String bankCode;
    private String accountNumber;
}
```

## @DynamicUpdate

```java
@Entity
@DynamicUpdate  // Only includes changed columns in UPDATE SQL
public class ProductEntity {
    // ...many columns, typically only a few change at a time
}
```

- Trade-off: slight overhead to compute diff, but reduces UPDATE statement size
- Useful for: entities with many columns, row-level locking contention

## Embeddable / Value Objects

```java
@Embeddable
public record Address(
    @Column(nullable = false) String street,
    @Column(nullable = false) String city,
    @Column(length = 10) String zipCode,
    @Column(nullable = false, length = 2) String countryCode
) {}

@Entity
public class CustomerEntity {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE)
    private Long id;

    @Embedded
    private Address billingAddress;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "shipping_street")),
        @AttributeOverride(name = "city", column = @Column(name = "shipping_city")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "shipping_zip")),
        @AttributeOverride(name = "countryCode", column = @Column(name = "shipping_country"))
    })
    private Address shippingAddress;
}
```

Use for: group of fields forming a logical unit without their own identity/table.

## Soft Delete Pattern

```java
@Entity
@SQLRestriction("deleted = false")  // Hibernate 6.4+ (replaces deprecated @Where)
public class ArticleEntity {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE)
    private Long id;

    private boolean deleted = false;

    @Column(name = "deleted_at")
    private Instant deletedAt;

    public void softDelete() {
        this.deleted = true;
        this.deletedAt = Instant.now();
    }
}
```

To include deleted records:
```java
@Query(value = "SELECT * FROM articles WHERE id = :id", nativeQuery = true)
Optional<ArticleEntity> findByIdIncludingDeleted(@Param("id") Long id);
```

## Converter for Custom Types

```java
@Converter(autoApply = true)
public class MoneyConverter implements AttributeConverter<Money, BigDecimal> {
    @Override
    public BigDecimal convertToDatabaseColumn(Money money) {
        return money == null ? null : money.amount();
    }

    @Override
    public Money convertToEntityAttribute(BigDecimal value) {
        return value == null ? null : new Money(value);
    }
}
```
