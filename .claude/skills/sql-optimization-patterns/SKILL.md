---
name: sql-optimization-patterns
description: SQL query optimization, indexing strategies, and EXPLAIN plan analysis for PostgreSQL and MySQL. Use when debugging slow queries, designing indexes, analyzing EXPLAIN output, resolving N+1 query problems, optimizing pagination, or tuning database performance. Do NOT use for basic SQL syntax, simple CRUD queries, or JPA entity design (use jpa-patterns skill instead).
---

# SQL Optimization Patterns

판단 기준과 규칙 중심. SQL 문법이 아닌, **올바른 최적화 전략** 선택을 안내.

## Quick Start

- **느린 쿼리 디버깅?** --> [Optimization Workflow](#optimization-workflow) below
- **인덱스 설계?** --> [Index Type Decision](#index-type-decision) below
- **페이지네이션 전략?** --> [Pagination Decision](#pagination-decision) below
- **EXPLAIN 분석?** --> [references/query-plan-analysis.md](references/query-plan-analysis.md)
- **PostgreSQL 심화?** --> [references/postgres-optimization-guide.md](references/postgres-optimization-guide.md)
- **MySQL 심화?** --> [references/mysql-optimization-guide.md](references/mysql-optimization-guide.md)

## CRITICAL Rules

1. **ALWAYS** `EXPLAIN ANALYZE` before optimizing -- 추측 금지, 실측 기반
2. **NEVER** `SELECT *` in production -- 필요한 컬럼만 명시
3. **ALWAYS** index columns in WHERE, JOIN, ORDER BY -- 풀 테이블 스캔 방지
4. **NEVER** function on indexed column in WHERE -- `WHERE LOWER(email) = x` 는 인덱스 무시 (functional index 필요)
5. **ALWAYS** `ANALYZE` after bulk data changes -- 통계 갱신으로 옵티마이저 판단 정상화
6. **NEVER** OFFSET for deep pagination -- 10만 행 이후 극심한 성능 저하
7. **PREFER** batch operations -- 루프 내 개별 INSERT/UPDATE 금지
8. **ALWAYS** covering index for hot queries -- Index Only Scan 유도
9. **NEVER** over-index -- 인덱스마다 INSERT/UPDATE/DELETE 비용 증가
10. **ALWAYS** monitor slow query log -- 문제는 코드가 아닌 운영에서 발견됨

## Optimization Workflow

```
Slow query reported
+-- 1. EXPLAIN ANALYZE 실행
|    +-- Seq Scan on large table? --> 인덱스 필요 (Index Decision Tree)
|    +-- Nested Loop on large sets? --> JOIN 전략 변경 또는 인덱스 추가
|    +-- High cost but low rows? --> 통계 오래됨, ANALYZE 실행
|    +-- Sort with high cost? --> ORDER BY 컬럼에 인덱스 추가
+-- 2. 쿼리 자체 최적화
|    +-- SELECT * ? --> 필요한 컬럼만
|    +-- Correlated subquery? --> JOIN으로 변환
|    +-- N+1 pattern? --> JOIN 또는 IN clause batch
+-- 3. 인덱스 추가/조정
+-- 4. EXPLAIN ANALYZE 재실행으로 개선 확인
```

## Index Type Decision

```
What query pattern?
+-- Equality (=) + Range (<, >, BETWEEN)
|    --> B-Tree (default, most common)
+-- Equality only, no range
|    --> Hash (PostgreSQL, slightly faster for =)
+-- Full-text search (LIKE '%word%')
|    --> GIN + to_tsvector
+-- JSONB containment (@>, ?)
|    --> GIN
+-- Geometric/spatial data
|    --> GiST
+-- Very large table, data correlates with physical order
|    --> BRIN (10-100x smaller than B-Tree)
```

### Composite Index Rules

```
Index column order matters!
+-- WHERE a = ? AND b = ?      --> (a, b) or (b, a) - both work
+-- WHERE a = ? AND b > ?      --> (a, b) - equality first, range last
+-- WHERE a = ? ORDER BY b     --> (a, b) - covers both filter and sort
+-- WHERE a = ? AND b = ? AND c > ?  --> (a, b, c) - equalities first
```

**Leftmost prefix rule:** `INDEX(a, b, c)` 는 `(a)`, `(a, b)`, `(a, b, c)` 쿼리에 사용 가능. `(b, c)` 단독은 불가.

### Index Selection Checklist

| Index Type | When | Example |
|-----------|------|---------|
| Standard B-Tree | WHERE/JOIN/ORDER BY | `CREATE INDEX idx_email ON users(email)` |
| Composite | Multi-column filter | `CREATE INDEX idx_user_status ON orders(user_id, status)` |
| Partial | 특정 조건 행만 자주 조회 | `CREATE INDEX idx_active ON users(email) WHERE status = 'active'` |
| Covering (INCLUDE) | Index Only Scan 유도 | `CREATE INDEX idx_email_cover ON users(email) INCLUDE (name, created_at)` |
| Expression | 함수 결과로 필터링 | `CREATE INDEX idx_lower ON users(LOWER(email))` |

## Pagination Decision

```
Need pagination?
+-- Small dataset (<10K rows)?
|    --> Offset-based (simple, "jump to page N" 가능)
+-- Large dataset, infinite scroll?
|    --> Cursor-based (consistent performance)
+-- Search results with page numbers?
|    --> Offset + total count cache
+-- Real-time feed?
|    --> Cursor (keyset) only
```

### Cursor-Based Pattern

```sql
-- First page
SELECT id, name, created_at FROM users
ORDER BY created_at DESC, id DESC
LIMIT 21;  -- +1 for has_next detection

-- Next page (after last item)
SELECT id, name, created_at FROM users
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 21;

-- Required index
CREATE INDEX idx_users_cursor ON users(created_at DESC, id DESC);
```

## Core Optimization Patterns

### N+1 Query

```sql
-- BAD: N+1 (loop executes N queries)
-- app code: for user in users: query("SELECT * FROM orders WHERE user_id = ?", user.id)

-- GOOD: JOIN
SELECT u.id, u.name, o.id as order_id, o.total
FROM users u LEFT JOIN orders o ON u.id = o.user_id
WHERE u.id IN (1, 2, 3, 4, 5);

-- GOOD: Batch IN clause
SELECT * FROM orders WHERE user_id IN (1, 2, 3, 4, 5);
```

### Correlated Subquery

```sql
-- BAD: Executes subquery per row
SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id)
FROM users u;

-- GOOD: JOIN + GROUP BY
SELECT u.name, COUNT(o.id) as order_count
FROM users u LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.name;
```

### Aggregate Optimization

```sql
-- BAD: COUNT(*) on entire large table
SELECT COUNT(*) FROM orders;

-- GOOD: Approximate count (PostgreSQL)
SELECT reltuples::bigint FROM pg_class WHERE relname = 'orders';

-- GOOD: Filtered count with index
CREATE INDEX idx_orders_created ON orders(created_at);
SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL '7 days';
```

### Batch Operations

```sql
-- BAD: Individual inserts in loop
INSERT INTO users (name) VALUES ('Alice');
INSERT INTO users (name) VALUES ('Bob');

-- GOOD: Batch insert
INSERT INTO users (name) VALUES ('Alice'), ('Bob'), ('Carol');

-- BEST: COPY for bulk (PostgreSQL)
COPY users (name, email) FROM '/tmp/users.csv' CSV HEADER;
```

## Anti-Patterns

| Anti-Pattern | Why Bad | Fix |
|-------------|---------|-----|
| `SELECT *` | 불필요한 I/O, covering index 무효 | 필요한 컬럼만 명시 |
| `WHERE LOWER(col) = ?` | 인덱스 사용 불가 | Expression index 또는 정규화 저장 |
| `LIKE '%abc'` | 앞부분 와일드카드 = 풀 스캔 | GIN trigram index 또는 full-text search |
| `OR` in WHERE | 인덱스 비효율 | `UNION ALL` 또는 별도 쿼리 |
| Implicit type cast | `WHERE id = '123'` 인덱스 무시 가능 | 타입 일치시키기 |
| CTE as optimization fence | PostgreSQL 12+에서 inline 되지만 주의 | `MATERIALIZED` / `NOT MATERIALIZED` 명시 |
| Over-indexing | 쓰기 성능 저하, 디스크 낭비 | 사용되지 않는 인덱스 주기적 제거 |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Seq Scan on indexed column | 통계 오래됨 또는 선택도 낮음 | `ANALYZE table;` 실행 |
| Index 있는데 안 쓰임 | 행 비율 높으면 옵티마이저가 Seq Scan 선택 | 정상 동작. Partial index 고려 |
| Nested Loop 느림 | 큰 테이블 간 JOIN | 조인 컬럼 인덱스 확인 |
| 페이지네이션 느려짐 | OFFSET 깊어짐 | Cursor-based pagination |
| 벌크 INSERT 느림 | 인덱스 많음 | 인덱스 DROP -> INSERT -> 재생성 |
| Lock contention | 장시간 트랜잭션 | 트랜잭션 짧게, batch 처리 |
| Planner 잘못된 추정 | 통계 부정확 | `ALTER TABLE SET STATISTICS` 높이기 |

## EXPLAIN Key Metrics

| Metric | Good | Bad | Action |
|--------|------|-----|--------|
| Index Scan / Index Only Scan | O | | 유지 |
| Seq Scan (small table) | O | | 무시 |
| Seq Scan (large table) | | X | 인덱스 추가 |
| Nested Loop (small inner) | O | | 유지 |
| Nested Loop (large inner) | | X | 인덱스 추가 또는 Hash Join 유도 |
| Sort (in-memory) | O | | 유지 |
| Sort (on-disk) | | X | work_mem 증가 또는 인덱스 |
| Rows estimate vs actual 10x+ 차이 | | X | ANALYZE 실행 |

## Maintenance Commands

```sql
-- Update statistics (lightweight)
ANALYZE users;

-- Vacuum + analyze (reclaim dead rows)
VACUUM ANALYZE users;

-- Full vacuum (locks table, reclaims disk space)
VACUUM FULL users;  -- use during maintenance window only

-- Find unused indexes (PostgreSQL)
SELECT indexrelname, idx_scan FROM pg_stat_user_indexes
WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC;

-- Find slow queries (PostgreSQL)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;
```

## Cross-References

| Topic | Skill |
|-------|-------|
| JPA entity, repository, N+1 in Hibernate | `jpa-patterns` |
| EXPLAIN 분석 심화 | [references/query-plan-analysis.md](references/query-plan-analysis.md) |
| PostgreSQL 전용 최적화 | [references/postgres-optimization-guide.md](references/postgres-optimization-guide.md) |
| MySQL 전용 최적화 | [references/mysql-optimization-guide.md](references/mysql-optimization-guide.md) |
| 고급 기법 (파티셔닝, MV, 모니터링) | [references/advanced-techniques.md](references/advanced-techniques.md) |

## References

- [PostgreSQL EXPLAIN docs](https://www.postgresql.org/docs/current/using-explain.html) -- Official guide
- [Use The Index, Luke](https://use-the-index-luke.com/) -- SQL indexing bible
- [pganalyze](https://pganalyze.com/docs) -- PostgreSQL performance monitoring
- [Markus Winand: SQL Performance Explained](https://sql-performance-explained.com/)
- [MySQL Query Optimization](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
