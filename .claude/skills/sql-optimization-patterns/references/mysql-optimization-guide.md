# MySQL/MariaDB Optimization Guide

MySQL/InnoDB 고유의 최적화 기법과 설정 튜닝 가이드.
SKILL.md의 공통 패턴과 중복되지 않는 MySQL 전용 내용만 다룬다.

## 1. InnoDB 아키텍처 이해

```
Client Query
    ↓
Query Parser → Optimizer → Execution Engine
    ↓                           ↓
Buffer Pool (RAM)          Redo Log Buffer
    ↓                           ↓
Data Files (.ibd)          Redo Log Files (ib_logfile)
                               ↓
                          Undo Log (ibdata1)
```

**핵심 구성 요소:**

| 구성 요소 | 역할 |
|-----------|------|
| Buffer Pool | 데이터/인덱스 페이지 캐시 (가장 중요) |
| Redo Log | WAL (Write-Ahead Log), crash recovery |
| Undo Log | MVCC 지원, 트랜잭션 롤백 |
| Change Buffer | Secondary index 변경 버퍼링 |
| Adaptive Hash Index | 자주 접근되는 페이지의 해시 인덱스 자동 생성 |

## 2. 핵심 InnoDB 설정

### Buffer Pool

```ini
# my.cnf / my.ini
[mysqld]
# Buffer Pool: 가용 메모리의 60-80% (전용 서버 기준)
innodb_buffer_pool_size = 24G          # 32GB 서버 기준

# Buffer Pool Instances: buffer_pool_size >= 1G 일 때
innodb_buffer_pool_instances = 8       # mutex 경합 감소

# Dump/Load: 재시작 후 warmup 시간 단축
innodb_buffer_pool_dump_at_shutdown = ON
innodb_buffer_pool_load_at_startup = ON
innodb_buffer_pool_dump_pct = 40       # 최근 사용 40% 덤프
```

```sql
-- Buffer Pool 히트율 확인
SELECT
    (1 - (
        (SELECT variable_value FROM performance_schema.global_status
         WHERE variable_name = 'Innodb_buffer_pool_reads')
        /
        (SELECT variable_value FROM performance_schema.global_status
         WHERE variable_name = 'Innodb_buffer_pool_read_requests')
    )) * 100 AS buffer_pool_hit_ratio;
-- 99% 이상이 이상적

-- Buffer Pool 상태 요약
SHOW ENGINE INNODB STATUS\G
```

### Redo Log

```ini
# Redo Log 크기: 1-2시간분의 쓰기 워크로드 수용
innodb_redo_log_capacity = 4G          # MySQL 8.0.30+
# (구버전: innodb_log_file_size = 2G, innodb_log_files_in_group = 2)

# 트랜잭션 커밋 시 flush 전략
innodb_flush_log_at_trx_commit = 1     # 1=안전(기본), 2=성능, 0=최대성능
# 1: 매 커밋마다 flush (ACID 완전 보장)
# 2: 초당 flush (crash 시 최대 1초 데이터 손실)
# 0: 초당 flush (mysqld crash 시도 데이터 손실)
```

### I/O 설정

```ini
# I/O 방식
innodb_flush_method = O_DIRECT         # OS 이중 버퍼링 방지

# I/O 용량 (SSD 기준)
innodb_io_capacity = 2000              # 일상 I/O (HDD: 200, SSD: 2000+)
innodb_io_capacity_max = 4000          # 최대 I/O

# 파일 핸들
innodb_open_files = 4000
table_open_cache = 4000
```

### 기타 중요 설정

```ini
# 테이블별 독립 tablespace (기본 ON)
innodb_file_per_table = ON

# 메타데이터 접근 시 통계 갱신 비활성화
innodb_stats_on_metadata = OFF

# Thread 설정
innodb_thread_concurrency = 0          # 0=자동 (기본 권장)

# Temporary table
tmp_table_size = 256M
max_heap_table_size = 256M

# Sort/Join buffer
sort_buffer_size = 4M                  # 세션당 할당
join_buffer_size = 4M                  # 세션당 할당
```

## 3. MySQL 8.0+ 최적화 기능

### Hash Join (8.0.18+)

equi-join에 인덱스가 없어도 Hash Join으로 효율적 처리.
이전 버전의 Block Nested-Loop를 대체.

```sql
-- Hash Join 확인 (EXPLAIN FORMAT=TREE에서 표시)
EXPLAIN FORMAT=TREE
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.created_at > '2025-01-01';
-- → Hash join (c.id = o.customer_id)
```

### Invisible Index (8.0+)

인덱스를 삭제하지 않고 옵티마이저에서 숨길 수 있음.
인덱스 삭제 전 영향도 테스트에 유용.

```sql
-- 인덱스 비활성화 (삭제하지 않고)
ALTER TABLE orders ALTER INDEX idx_orders_status INVISIBLE;

-- 쿼리 성능 확인 후...

-- 다시 활성화
ALTER TABLE orders ALTER INDEX idx_orders_status VISIBLE;

-- 특정 세션에서 invisible 인덱스 사용
SET SESSION optimizer_switch = 'use_invisible_indexes=on';
```

### Descending Index (8.0+)

```sql
-- 내림차순 인덱스 (8.0 이전에는 ASC만 실제 지원)
CREATE INDEX idx_orders_date_desc ON orders(created_at DESC);

-- 혼합 정렬 최적화
CREATE INDEX idx_orders_user_date
ON orders(user_id ASC, created_at DESC);
```

### Functional Index (8.0.13+)

```sql
-- Expression 기반 인덱스
CREATE INDEX idx_users_email_lower
ON users((LOWER(email)));

-- JSON 값 인덱스
CREATE INDEX idx_events_type
ON events((CAST(data->>'$.type' AS CHAR(50))));

-- 날짜 함수 인덱스
CREATE INDEX idx_orders_year
ON orders((YEAR(created_at)));
```

### Window Functions 최적화

```sql
-- ROW_NUMBER 기반 페이지네이션 (cursor 대안)
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY created_at DESC) AS rn
    FROM orders
    WHERE user_id = 123
) sub
WHERE rn BETWEEN 21 AND 40;

-- Running total
SELECT
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;
```

## 4. Optimizer Hints

쿼리 레벨에서 옵티마이저 동작을 직접 제어.

```sql
-- 특정 인덱스 강제 사용
SELECT /*+ INDEX(orders idx_orders_user_date) */
    * FROM orders WHERE user_id = 123;

-- JOIN 순서 고정
SELECT /*+ JOIN_ORDER(c, o, oi) */
    c.name, o.total, oi.product_id
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN order_items oi ON o.id = oi.order_id;

-- 병렬 실행 제한/해제 (InnoDB Cluster 등)
SELECT /*+ SET_VAR(max_execution_time=5000) */
    * FROM large_table WHERE condition;

-- Hash Join 힌트
SELECT /*+ HASH_JOIN(o, c) */
    * FROM orders o JOIN customers c ON o.customer_id = c.id;

-- No Hash Join (Nested Loop 강제)
SELECT /*+ NO_HASH_JOIN(o, c) */
    * FROM orders o JOIN customers c ON o.customer_id = c.id;

-- Subquery 전략 제어
SELECT /*+ SEMIJOIN(@subq MATERIALIZATION) */
    * FROM orders
WHERE customer_id IN (SELECT /*+ QB_NAME(subq) */ id FROM vip_customers);

-- Merge 힌트 (derived table 인라인)
SELECT /*+ MERGE(derived) */
    * FROM (SELECT * FROM orders WHERE status = 'active') AS derived;
```

### Index Hints (전통 방식)

```sql
-- 인덱스 사용 권장
SELECT * FROM orders USE INDEX (idx_orders_user_date)
WHERE user_id = 123 AND created_at > '2025-01-01';

-- 인덱스 강제 사용
SELECT * FROM orders FORCE INDEX (idx_orders_user_date)
WHERE user_id = 123 AND created_at > '2025-01-01';

-- 특정 인덱스 제외
SELECT * FROM orders IGNORE INDEX (idx_orders_status)
WHERE status = 'active';

-- JOIN/ORDER BY/GROUP BY에 대한 인덱스 힌트
SELECT * FROM orders USE INDEX FOR ORDER BY (idx_orders_date)
ORDER BY created_at DESC;
```

## 5. Slow Query Log

```ini
# my.cnf
[mysqld]
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1                    # 1초 이상 쿼리 기록
log_queries_not_using_indexes = ON     # 인덱스 미사용 쿼리도 기록
min_examined_row_limit = 1000          # 최소 검사 행 수 필터
```

```bash
# mysqldumpslow로 분석
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log   # 총 시간 기준 Top 10
mysqldumpslow -s c -t 10 /var/log/mysql/slow.log   # 횟수 기준 Top 10
mysqldumpslow -s at -t 10 /var/log/mysql/slow.log  # 평균 시간 기준 Top 10

# pt-query-digest (Percona Toolkit, 더 상세한 분석)
pt-query-digest /var/log/mysql/slow.log
```

## 6. Performance Schema

MySQL 내장 성능 모니터링 프레임워크.

```sql
-- 가장 느린 쿼리 Top 10
SELECT
    DIGEST_TEXT AS query,
    COUNT_STAR AS exec_count,
    ROUND(SUM_TIMER_WAIT / 1e12, 2) AS total_sec,
    ROUND(AVG_TIMER_WAIT / 1e12, 4) AS avg_sec,
    SUM_ROWS_EXAMINED AS rows_examined,
    SUM_ROWS_SENT AS rows_sent
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;

-- 인덱스 미사용 쿼리
SELECT
    DIGEST_TEXT,
    COUNT_STAR,
    SUM_NO_INDEX_USED
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_NO_INDEX_USED > 0
ORDER BY COUNT_STAR DESC
LIMIT 10;

-- 테이블별 I/O 통계
SELECT
    OBJECT_SCHEMA,
    OBJECT_NAME,
    COUNT_READ, COUNT_WRITE,
    ROUND(SUM_TIMER_READ / 1e12, 2) AS read_sec,
    ROUND(SUM_TIMER_WRITE / 1e12, 2) AS write_sec
FROM performance_schema.table_io_waits_summary_by_table
WHERE OBJECT_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

## 7. Generated Columns (가상 컬럼)

계산된 값에 인덱스를 생성할 때 유용.

```sql
-- 가상 컬럼 (VIRTUAL: 저장 안함, 조회 시 계산)
ALTER TABLE users
ADD COLUMN email_domain VARCHAR(255)
    GENERATED ALWAYS AS (SUBSTRING_INDEX(email, '@', -1)) VIRTUAL;

-- 저장 컬럼 (STORED: 디스크에 저장, 인덱스 가능)
ALTER TABLE users
ADD COLUMN email_domain VARCHAR(255)
    GENERATED ALWAYS AS (SUBSTRING_INDEX(email, '@', -1)) STORED;

CREATE INDEX idx_users_domain ON users(email_domain);
```

## 8. Character Set / Collation 영향

```sql
-- utf8mb4 + utf8mb4_0900_ai_ci 권장 (MySQL 8.0 기본)
-- utf8mb3은 이모지 저장 불가

-- Collation 불일치 시 인덱스 사용 불가
-- 예: 테이블은 utf8mb4_general_ci, 쿼리는 utf8mb4_bin → 인덱스 무시

-- Collation 확인
SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'mydb'
  AND DATA_TYPE IN ('varchar', 'char', 'text');

-- JOIN 시 양쪽 테이블의 collation 일치 확인
-- 불일치하면 CONVERT() 사용으로 인덱스 무효화됨
```

## 9. MySQL 시스템 스키마 (sys)

MySQL 5.7+ 내장 진단 뷰.

```sql
-- 가장 비용 높은 쿼리
SELECT * FROM sys.statements_with_runtimes_in_95th_percentile LIMIT 10;

-- Full table scan 쿼리
SELECT * FROM sys.statements_with_full_table_scans LIMIT 10;

-- 사용되지 않는 인덱스
SELECT * FROM sys.schema_unused_indexes;

-- 중복 인덱스
SELECT * FROM sys.schema_redundant_indexes;

-- 테이블 통계
SELECT * FROM sys.schema_table_statistics ORDER BY total_latency DESC LIMIT 10;

-- I/O 핫스팟
SELECT * FROM sys.io_global_by_file_by_latency LIMIT 10;

-- 메모리 사용
SELECT * FROM sys.memory_global_total;
```

## 10. 유용한 설정 요약표

| 설정 | OLTP 권장값 | OLAP 권장값 | 설명 |
|------|-------------|-------------|------|
| `innodb_buffer_pool_size` | RAM의 70-80% | RAM의 70-80% | 데이터 캐시 |
| `innodb_flush_log_at_trx_commit` | 1 (안전) | 2 (성능) | 커밋 flush |
| `innodb_flush_method` | O_DIRECT | O_DIRECT | 이중 버퍼 방지 |
| `innodb_io_capacity` | 2000 (SSD) | 2000+ | I/O 대역폭 |
| `sort_buffer_size` | 2-4M | 16-64M | 정렬 메모리 |
| `join_buffer_size` | 2-4M | 16-64M | 조인 메모리 |
| `tmp_table_size` | 64-256M | 256M-1G | 임시 테이블 |
| `max_connections` | 150-300 | 50-100 | 동시 커넥션 |
