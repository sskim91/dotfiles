---
name: jpa-patterns
description: Use when designing JPA entities, writing JPQL/Criteria queries, resolving N+1 problems, configuring HikariCP, or choosing ID generation strategies. Do NOT use for raw SQL optimization (use sql-optimization-patterns).
paths: "**/*.java, **/build.gradle*, **/pom.xml"
---

# JPA/Hibernate Patterns

프로덕션 이슈를 만드는 지점만 담는다. JPA API·매핑 문법 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **NEVER** use `FetchType.EAGER` on `@OneToMany` or `@ManyToMany` collections
2. **ALWAYS** disable OSIV: `spring.jpa.open-in-view=false`
3. **NEVER** use Lombok `@Data` on entities — breaks equals/hashCode, triggers lazy loading via toString
4. **ALWAYS** use `@Transactional(readOnly = true)` for read-only service methods
5. **NEVER** rely on `hibernate.ddl-auto` in production — use Flyway or Liquibase
6. **ALWAYS** initialize collections: `private List<X> items = new ArrayList<>()`
7. **Prefer** `SEQUENCE` (allocationSize=50) over `IDENTITY` when batch inserts matter
8. **NEVER** return entities directly from controllers — use DTO projections
9. **Keep transactions short** — no HTTP calls or heavy computation inside `@Transactional`
10. equals/hashCode: Vlad Mihalcea 패턴 — `id != null && id.equals(other.getId())` + `getClass().hashCode()`

## Production Properties

```properties
spring.jpa.open-in-view=false

# Batch inserts (SEQUENCE 전략 필요 — IDENTITY는 배치 불가)
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true

# HikariCP: connections = (core_count x 2) + effective_spindle_count
spring.datasource.hikari.maximum-pool-size=10
```

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@ManyToOne(fetch = FetchType.EAGER)` → LAZY 기본, 필요시 JOIN FETCH
- ❌ `equals()/hashCode()`를 Lombok/IDE 자동 생성으로 → Vlad Mihalcea 패턴 사용
- ❌ JOIN FETCH를 List 컬렉션 2개 이상에 → `MultipleBagFetchException`. Set 우회 말고 **별도 쿼리로 분리**
- ❌ N+1 해결에 `@EntityGraph` 남용 → JOIN FETCH 또는 DTO projection 우선
- ❌ bulk `@Modifying @Query` 후 stale entity → `@Modifying(clearAutomatically = true)`
- ❌ `@DataJpaTest`에 H2 사용 → Testcontainers로 실제 DB
- ❌ deep pagination에 OFFSET → keyset/cursor 페이지네이션

N+1 검증은 SQL 로그로:
```properties
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE
```

## Cross-References

| Topic | Skill |
|-------|-------|
| Raw SQL, index design, EXPLAIN | `sql-optimization-patterns` |
| Records/sealed types (엔티티엔 record 금지) | `java-modern-patterns` |
| Spring Boot 테스트 슬라이스 | `springboot-tdd` |

## Authoritative Sources

- **Vlad Mihalcea** — vladmihalcea.com, "High-Performance Java Persistence"
- **HikariCP Wiki** — github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
