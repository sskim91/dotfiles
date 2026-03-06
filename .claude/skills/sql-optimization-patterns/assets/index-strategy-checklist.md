# Index Strategy Checklist

인덱스 설계 시 체계적으로 검토해야 할 항목들.

## 인덱스 생성 의사결정 플로우

```
쿼리가 느린가?
    ↓
EXPLAIN 확인 → Full Table Scan인가?
    ↓ Yes
WHERE/JOIN/ORDER BY에 사용되는 컬럼 확인
    ↓
테이블 크기가 충분히 큰가? (수천 행 이상)
    ↓ Yes
해당 컬럼의 선택성(Selectivity)이 높은가?
    ↓ Yes
인덱스 생성 → EXPLAIN으로 효과 검증
```

## 1. 인덱스 생성 전 체크리스트

- [ ] EXPLAIN으로 현재 쿼리 플랜 확인했는가?
- [ ] Full Table Scan 또는 비효율적 접근 패턴이 확인되었는가?
- [ ] 대상 테이블의 행 수가 인덱스 효과를 볼 만큼 충분한가? (수천 행 이상)
- [ ] 해당 컬럼의 카디널리티(고유값 수)가 적절한가?
- [ ] 이미 유사한 인덱스가 존재하지 않는가? (중복 인덱스 확인)
- [ ] Write 성능 영향을 고려했는가? (INSERT/UPDATE/DELETE 빈도)
- [ ] 인덱스 크기를 추정했는가? (디스크 공간)

## 2. 복합 인덱스 컬럼 순서 규칙

**핵심 원칙: Equality → Range → Sort**

```sql
-- 쿼리: WHERE status = 'active' AND created_at > '2025-01-01' ORDER BY id
-- 최적 인덱스 순서:
CREATE INDEX idx_optimal ON orders(
    status,        -- 1. Equality (=)
    created_at,    -- 2. Range (>, <, BETWEEN)
    id             -- 3. Sort (ORDER BY)
);
```

### 컬럼 순서 결정 가이드

| 순서 | 조건 유형 | 이유 |
|------|-----------|------|
| 1순위 | Equality (`=`, `IN`) | B-Tree에서 정확한 위치로 점프 |
| 2순위 | Range (`>`, `<`, `BETWEEN`, `LIKE 'abc%'`) | 범위 내 순차 스캔 |
| 3순위 | Sort (`ORDER BY`) | 추가 정렬 연산 제거 |
| 4순위 | Covering (`SELECT` 컬럼) | 테이블 접근 제거 (INCLUDE 사용) |

### Leftmost Prefix 규칙

복합 인덱스 `(a, b, c)`에서:

| 쿼리 조건 | 인덱스 사용 | 설명 |
|-----------|-------------|------|
| `WHERE a = 1` | O (a 사용) | 첫 번째 컬럼 |
| `WHERE a = 1 AND b = 2` | O (a, b 사용) | 첫 두 컬럼 |
| `WHERE a = 1 AND b = 2 AND c = 3` | O (전체 사용) | 전체 인덱스 |
| `WHERE b = 2` | X | 첫 번째 컬럼 누락 |
| `WHERE b = 2 AND c = 3` | X | 첫 번째 컬럼 누락 |
| `WHERE a = 1 AND c = 3` | 부분 (a만) | 중간 컬럼 누락, skip scan 가능성 |
| `WHERE a = 1 AND b > 5 AND c = 3` | 부분 (a, b) | Range 이후 컬럼은 인덱스 활용 불가 |

## 3. 인덱스 유형별 사용 기준

### B-Tree (기본)

```sql
-- 대부분의 경우 기본 선택
CREATE INDEX idx_users_email ON users(email);
```

- Equality (`=`), Range (`>`, `<`, `BETWEEN`), Sort, LIKE 'prefix%'
- 거의 모든 쿼리 패턴에 적합

### Covering Index (PostgreSQL: INCLUDE, MySQL: 복합 인덱스)

```sql
-- PostgreSQL: INCLUDE로 추가 컬럼 포함
CREATE INDEX idx_orders_covering ON orders(user_id, status)
INCLUDE (total, created_at);
-- user_id + status로 검색, total + created_at도 인덱스에서 바로 반환

-- MySQL: 복합 인덱스로 커버링 구현
CREATE INDEX idx_orders_covering ON orders(user_id, status, total, created_at);
```

- SELECT 컬럼이 모두 인덱스에 포함 → Index Only Scan
- 테이블 접근 없이 인덱스만으로 쿼리 완료

### Partial Index (PostgreSQL 전용)

```sql
-- 활성 주문만 인덱싱 (전체의 10%라면 인덱스 크기 90% 절약)
CREATE INDEX idx_active_orders ON orders(user_id, created_at)
WHERE status = 'active';

-- NULL이 아닌 값만 인덱싱
CREATE INDEX idx_orders_shipped ON orders(shipped_at)
WHERE shipped_at IS NOT NULL;
```

- 데이터의 일부만 인덱싱 → 작은 인덱스, 빠른 갱신
- 쿼리의 WHERE 절이 인덱스 조건을 포함해야 사용됨

### Expression Index

```sql
-- PostgreSQL
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- MySQL (Functional Index, 8.0.13+)
CREATE INDEX idx_users_email_lower ON users((LOWER(email)));
```

- WHERE 절에서 함수를 사용하는 경우
- 함수 없이는 인덱스 사용 불가 문제 해결

### GIN / GiST / BRIN

상세 내용은 [postgres-optimization-guide.md](postgres-optimization-guide.md) 4번 참조.

## 4. 인덱스를 만들지 말아야 할 때

| 상황 | 이유 |
|------|------|
| 테이블이 매우 작음 (수백 행 이하) | Seq Scan이 더 빠름 |
| 컬럼의 카디널리티가 매우 낮음 (예: boolean, status 3-4종) | 인덱스 선택성 부족 |
| 테이블이 Write-heavy | INSERT/UPDATE/DELETE마다 인덱스 갱신 비용 |
| 쿼리에서 대부분의 행을 반환 | Full Scan이 더 효율적 (보통 전체의 10-20% 이상) |
| 이미 동일/유사 인덱스 존재 | 중복 인덱스는 Write 비용만 증가 |
| LIKE '%keyword%' (앞쪽 와일드카드) | B-Tree 인덱스 사용 불가 (pg_trgm GIN 대안) |

## 5. 인덱스 유지보수 체크리스트

### 정기 점검 (월 1회)

- [ ] 사용되지 않는 인덱스 확인 및 제거
- [ ] 중복 인덱스 확인 및 제거
- [ ] 인덱스 bloat 확인 (PostgreSQL)
- [ ] 통계 갱신 (`ANALYZE`)
- [ ] 느린 쿼리 로그에서 인덱스 부족 패턴 확인

### 미사용 인덱스 확인

```sql
-- PostgreSQL
SELECT
    schemaname, tablename, indexname,
    idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelid NOT IN (
      SELECT indexrelid FROM pg_constraint WHERE contype IN ('p', 'u')
  )
ORDER BY pg_relation_size(indexrelid) DESC;

-- MySQL
SELECT * FROM sys.schema_unused_indexes
WHERE object_schema NOT IN ('mysql', 'performance_schema');
```

### 중복 인덱스 확인

```sql
-- MySQL
SELECT * FROM sys.schema_redundant_indexes
WHERE table_schema NOT IN ('mysql', 'performance_schema');

-- PostgreSQL: pg_catalog으로 수동 확인
-- 또는 pgstattuple 확장 사용
```

### 인덱스 Bloat 확인 (PostgreSQL)

```sql
-- pgstattuple 확장
CREATE EXTENSION IF NOT EXISTS pgstattuple;

SELECT
    indexrelid::regclass AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    avg_leaf_density,
    leaf_fragmentation
FROM pgstatindex('idx_orders_user_date');
-- avg_leaf_density < 50% 이면 REINDEX 고려

-- 인덱스 재구성
REINDEX INDEX CONCURRENTLY idx_orders_user_date;
```

## 6. 실전 인덱스 설계 예시

### 사용자 검색 API

```sql
-- 쿼리 패턴
SELECT id, name, email FROM users
WHERE status = 'active'
  AND email LIKE 'john%'
ORDER BY created_at DESC
LIMIT 20;

-- 인덱스 설계
-- 1. Equality(status) → 2. Range(email LIKE prefix) → 3. Sort(created_at)
CREATE INDEX idx_users_search ON users(status, email)
INCLUDE (name, created_at);
-- Partial index로 더 최적화
CREATE INDEX idx_active_users_search ON users(email)
INCLUDE (name, created_at)
WHERE status = 'active';
```

### 주문 대시보드

```sql
-- 쿼리 패턴
SELECT user_id, COUNT(*), SUM(total)
FROM orders
WHERE created_at >= '2025-01-01'
  AND status IN ('completed', 'shipped')
GROUP BY user_id
ORDER BY SUM(total) DESC;

-- 인덱스 설계
CREATE INDEX idx_orders_dashboard ON orders(status, created_at)
INCLUDE (user_id, total);
```

### 시계열 로그

```sql
-- 쿼리 패턴: 최근 로그 조회
SELECT * FROM access_logs
WHERE service = 'api'
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- 인덱스 설계
CREATE INDEX idx_logs_service_time ON access_logs(service, created_at DESC);
-- 대형 테이블이면 파티셔닝 + BRIN 조합도 검토
```
