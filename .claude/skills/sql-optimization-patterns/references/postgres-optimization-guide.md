# PostgreSQL Optimization Guide

PostgreSQL 고유의 최적화 기법과 설정 튜닝 가이드.
SKILL.md의 공통 패턴과 중복되지 않는 PostgreSQL 전용 내용만 다룬다.

## 1. postgresql.conf 핵심 파라미터

### Memory 설정

| 파라미터 | 권장값 | 설명 | 변경 반영 |
|----------|--------|------|-----------|
| `shared_buffers` | 전체 RAM의 25-40% | 데이터 페이지 캐시 (가장 중요) | Restart |
| `effective_cache_size` | 전체 RAM의 50-75% | Planner의 OS 캐시 크기 힌트 | Reload |
| `work_mem` | 32-256MB (워크로드 기반) | 정렬/해시 연산 메모리 (연산별 할당) | Session |
| `maintenance_work_mem` | 1-2GB | VACUUM, CREATE INDEX 메모리 | Session |
| `huge_pages` | `try` | TLB miss 감소 (shared_buffers 8GB 이상 시 권장) | Restart |

```sql
-- 현재 설정 확인
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;

-- 세션 단위 work_mem 조정 (리포팅 쿼리)
SET work_mem = '512MB';
SELECT /* 복잡한 분석 쿼리 */ ;
RESET work_mem;

-- 트랜잭션 단위 조정
BEGIN;
SET LOCAL work_mem = '256MB';
-- 복잡한 쿼리 실행
COMMIT;
```

**work_mem 과다 사용 감지:**

```sql
-- 디스크 spill 발생 쿼리 확인 (temp 파일 사용)
SELECT query, temp_blks_read, temp_blks_written
FROM pg_stat_statements
WHERE temp_blks_written > 0
ORDER BY temp_blks_written DESC
LIMIT 10;

-- 현재 세션 메모리 사용 확인
SELECT * FROM pg_backend_memory_contexts()
ORDER BY total_bytes DESC
LIMIT 20;
```

### WAL 설정

| 파라미터 | 권장값 | 설명 |
|----------|--------|------|
| `wal_buffers` | 64MB (또는 `-1` 자동) | WAL 버퍼 크기 |
| `min_wal_size` | 1GB | WAL 최소 크기 |
| `max_wal_size` | 4-8GB | 체크포인트 간 최대 WAL |
| `checkpoint_completion_target` | 0.9 | 체크포인트 분산 비율 |

### Connection 설정

| 파라미터 | 권장값 | 설명 |
|----------|--------|------|
| `max_connections` | 100-200 | PgBouncer 사용 시 낮게 설정 |
| `idle_in_transaction_session_timeout` | 30s-5min | 유휴 트랜잭션 자동 종료 |

**변경 적용:**

```bash
# Restart 필요 (shared_buffers, huge_pages, max_connections)
sudo systemctl restart postgresql

# Reload만 필요 (work_mem, effective_cache_size)
sudo systemctl reload postgresql
# 또는 psql에서
SELECT pg_reload_conf();
```

## 2. Autovacuum 튜닝

Autovacuum은 dead tuple 제거와 통계 갱신을 수행하는 핵심 프로세스.
비활성화하면 table bloat, transaction ID wraparound 위험.

### 글로벌 설정

```ini
# postgresql.conf
autovacuum = on                          # 절대 끄지 말 것
autovacuum_max_workers = 3               # 동시 worker 수
autovacuum_vacuum_scale_factor = 0.1     # dead tuple 10% 시 vacuum
autovacuum_analyze_scale_factor = 0.05   # 변경 5% 시 analyze
autovacuum_vacuum_cost_delay = 10ms      # I/O throttling
autovacuum_vacuum_cost_limit = 1000      # cost 한도
```

### 대형 테이블 개별 설정

대형 테이블은 scale_factor 기본값(0.2)으로는 vacuum이 너무 늦게 시작됨.
예: 1억 행 테이블에서 0.2 = 2천만 행 변경 후에야 vacuum 실행.

```sql
-- 대형 테이블에 개별 autovacuum 설정
ALTER TABLE large_orders SET (
    autovacuum_vacuum_scale_factor = 0.01,     -- 1%로 축소
    autovacuum_vacuum_threshold = 1000,        -- 최소 1000행 변경 시
    autovacuum_analyze_scale_factor = 0.005    -- analyze도 조정
);

-- 현재 autovacuum 활동 확인
SELECT
    schemaname, relname,
    n_live_tup, n_dead_tup,
    ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

### Autovacuum 처리 속도 계산

```
# 기본 설정에서의 초당 처리량
# cost_delay=20ms → 50 wake-ups/초
# cost_limit=200 (기본)
#
# shared_buffers에 있는 페이지: 50 * 200 * 8KB = ~78 MB/초
# 디스크에서 읽는 페이지:       50 * (200/10) * 8KB = ~7.8 MB/초
# 더티 페이지 쓰기:             50 * (200/20) * 8KB = ~3.9 MB/초
#
# 대형 테이블에서는 cost_limit을 1000-2000으로 올려 속도 향상
```

### Transaction ID Wraparound 방지

```sql
-- wraparound 위험 테이블 확인
SELECT
    c.oid::regclass AS table_name,
    age(c.relfrozenxid) AS xid_age,
    pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
    ROUND(age(c.relfrozenxid)::numeric / 2147483647 * 100, 2) AS pct_towards_wraparound
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE c.relkind = 'r'
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY age(c.relfrozenxid) DESC
LIMIT 10;
```

## 3. pg_stat_statements 설정

쿼리 성능 모니터링의 핵심 확장.

```sql
-- 확장 설치
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- postgresql.conf에 추가
-- shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.track = all
-- pg_stat_statements.max = 10000
```

```sql
-- 총 실행 시간 기준 Top 10 쿼리
SELECT
    queryid,
    LEFT(query, 80) AS query_preview,
    calls,
    ROUND(total_exec_time::numeric, 2) AS total_ms,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms,
    ROUND((100 * total_exec_time / SUM(total_exec_time) OVER())::numeric, 2) AS pct,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- 통계 리셋
SELECT pg_stat_statements_reset();
```

## 4. PostgreSQL 고유 인덱스 심화

### BRIN (Block Range INdex)

시계열/로그 데이터처럼 물리적 순서와 값 순서가 일치하는 대형 테이블에 적합.
B-Tree 대비 100-1000배 작은 크기.

```sql
-- 시계열 테이블에 BRIN 인덱스
CREATE INDEX idx_logs_created_brin ON logs USING BRIN(created_at)
WITH (pages_per_range = 128);

-- correlation 확인 (1.0에 가까울수록 BRIN에 적합)
SELECT
    attname,
    correlation
FROM pg_stats
WHERE tablename = 'logs'
  AND attname = 'created_at';
-- correlation > 0.9 이면 BRIN 추천
```

### GIN (Generalized Inverted Index)

배열, JSONB, 전문 검색(Full-Text Search)에 최적화.

```sql
-- JSONB 인덱스 (키 존재 여부 + 값 검색)
CREATE INDEX idx_events_data ON events USING GIN(data);

-- JSONB 경로 기반 인덱스 (특정 키만)
CREATE INDEX idx_events_data_type ON events USING GIN((data -> 'type'));

-- 전문 검색 인덱스
CREATE INDEX idx_articles_search ON articles
USING GIN(to_tsvector('english', title || ' ' || body));

-- 전문 검색 쿼리
SELECT * FROM articles
WHERE to_tsvector('english', title || ' ' || body)
      @@ to_tsquery('english', 'postgresql & optimization');
```

### GiST (Generalized Search Tree)

범위 타입, 지리 데이터, 근접 검색에 적합.

```sql
-- 범위 겹침 검색
CREATE INDEX idx_reservations_period ON reservations
USING GiST(tstzrange(check_in, check_out));

-- PostGIS 공간 인덱스
CREATE INDEX idx_locations_geom ON locations USING GiST(geom);
```

### SP-GiST (Space-Partitioned GiST)

IP 주소 범위, 전화번호, 비균등 분포 데이터에 적합.

```sql
-- IP 주소 범위 검색
CREATE INDEX idx_ip_ranges ON access_log USING SPGIST(ip_addr inet_ops);
```

## 5. CTE 최적화 (PostgreSQL 12+)

PostgreSQL 12부터 CTE가 자동으로 인라인될 수 있음.
Optimization fence가 필요한 경우 `MATERIALIZED` 명시.

```sql
-- 자동 인라인 (PG12+, 기본 동작, 1회만 참조 시)
WITH filtered AS (
    SELECT * FROM orders WHERE status = 'active'
)
SELECT * FROM filtered WHERE total > 100;
-- → 옵티마이저가 WHERE 조건을 합쳐서 최적화

-- 강제 실체화 (중간 결과 재사용 시 유리)
WITH MATERIALIZED order_stats AS (
    SELECT user_id, COUNT(*) AS cnt, SUM(total) AS total_sum
    FROM orders
    GROUP BY user_id
)
SELECT * FROM order_stats WHERE cnt > 10
UNION ALL
SELECT * FROM order_stats WHERE total_sum > 10000;

-- 인라인 강제 (실체화 방지)
WITH NOT MATERIALIZED recent AS (
    SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent WHERE status = 'pending';
```

## 6. JSONB 최적화

```sql
-- JSONB vs JSON
-- JSONB: 파싱 완료 바이너리, 인덱싱 가능, 약간 느린 입력
-- JSON: 텍스트 그대로 저장, 인덱싱 불가, 빠른 입력

-- JSONB 연산자
SELECT * FROM events
WHERE data @> '{"type": "click"}';        -- 포함 (GIN 인덱스 사용)

SELECT * FROM events
WHERE data ? 'user_id';                   -- 키 존재 여부

SELECT * FROM events
WHERE data ->> 'type' = 'click';          -- 값 추출 비교 (인덱스 사용 안됨)

-- jsonb_path 쿼리 (PG12+)
SELECT * FROM events
WHERE jsonb_path_exists(data, '$.tags[*] ? (@ == "important")');
```

## 7. pg_trgm 유사 검색

`LIKE '%keyword%'`와 같은 중간 일치 검색을 인덱스로 가속화.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- trigram 인덱스 생성
CREATE INDEX idx_users_name_trgm ON users USING GIN(name gin_trgm_ops);

-- 유사 검색 (인덱스 사용)
SELECT * FROM users WHERE name LIKE '%john%';
SELECT * FROM users WHERE name ILIKE '%john%';

-- 유사도 검색
SELECT name, similarity(name, 'johnsen') AS sim
FROM users
WHERE name % 'johnsen'  -- similarity > 0.3
ORDER BY sim DESC;
```

## 8. Connection Pooling (PgBouncer)

PostgreSQL의 프로세스 모델에서는 커넥션 하나당 OS 프로세스 하나를 생성.
수백 이상의 동시 커넥션은 PgBouncer로 풀링 필수.

```ini
# pgbouncer.ini
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction        # 트랜잭션 단위 커넥션 공유 (권장)
max_client_conn = 1000         # 클라이언트 최대 커넥션
default_pool_size = 20         # DB당 풀 크기
min_pool_size = 5              # 최소 유지 커넥션
reserve_pool_size = 5          # 예비 풀
reserve_pool_timeout = 3       # 예비 풀 대기 시간(초)
```

| Pool Mode | 설명 | 제약 |
|-----------|------|------|
| `session` | 세션 종료까지 커넥션 유지 | Prepared statement 사용 가능 |
| `transaction` | 트랜잭션 종료 시 반환 (권장) | SET, LISTEN 등 세션 기능 제한 |
| `statement` | 쿼리 단위 반환 | 멀티 스테이트먼트 트랜잭션 불가 |

## 9. Parallel Query

```sql
-- 병렬 쿼리 설정
SET max_parallel_workers_per_gather = 4;    -- Gather 노드당 최대 worker
SET max_parallel_workers = 8;              -- 전체 시스템 최대 worker
SET parallel_tuple_cost = 0.01;            -- 병렬 처리 비용 (낮출수록 적극 사용)
SET min_parallel_table_scan_size = '8MB';  -- 이 크기 이상 테이블에서 병렬 Seq Scan

-- 병렬 인덱스 생성
SET max_parallel_maintenance_workers = 4;
CREATE INDEX CONCURRENTLY idx_orders_date ON orders(created_at);
```

## 10. Table Bloat 감지 및 해결

```sql
-- bloat 추정 쿼리
SELECT
    schemaname || '.' || tablename AS table_full_name,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;

-- 테이블 재구성 (VACUUM FULL은 테이블 잠금)
-- 온라인 대안: pg_repack 확장
-- CREATE EXTENSION pg_repack;
-- pg_repack --table=large_table --no-order mydb
```

## 11. Lock 모니터링

```sql
-- 현재 잠금 대기 확인
SELECT
    blocked.pid AS blocked_pid,
    blocked_activity.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking_activity.query AS blocking_query,
    blocked_activity.wait_event_type
FROM pg_catalog.pg_locks blocked
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked.pid = blocked_activity.pid
JOIN pg_catalog.pg_locks blocking
    ON blocking.locktype = blocked.locktype
    AND blocking.relation = blocked.relation
    AND blocking.pid != blocked.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking.pid = blocking_activity.pid
WHERE NOT blocked.granted;
```

## 12. 유용한 시스템 뷰 요약

| 뷰 | 용도 |
|----|------|
| `pg_stat_statements` | 쿼리 성능 통계 (확장) |
| `pg_stat_user_tables` | 테이블 I/O, vacuum 통계 |
| `pg_stat_user_indexes` | 인덱스 사용 통계 |
| `pg_stat_activity` | 현재 세션/쿼리 상태 |
| `pg_stat_bgwriter` | 체크포인트/버퍼 쓰기 통계 |
| `pg_locks` | 현재 잠금 상태 |
| `pg_class` + `pg_stats` | 테이블/컬럼 통계 |
