-- ============================================================
-- Index Recommendations Scripts
-- PostgreSQL과 MySQL에서 인덱스 문제를 진단하고 추천하는 스크립트
-- ============================================================

-- ************************************************************
-- SECTION 1: PostgreSQL
-- ************************************************************

-- ------------------------------------------------------------
-- 1.1 미사용 인덱스 탐지
-- idx_scan = 0 인 인덱스는 Write 비용만 유발
-- PK/Unique 제약 인덱스는 제외
-- ------------------------------------------------------------
SELECT
    s.schemaname,
    s.relname AS table_name,
    s.indexrelname AS index_name,
    s.idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(s.indexrelid)) AS index_size,
    pg_size_pretty(pg_relation_size(s.relid)) AS table_size
FROM pg_stat_user_indexes s
JOIN pg_index i ON s.indexrelid = i.indexrelid
WHERE s.idx_scan = 0           -- 한 번도 사용되지 않은 인덱스
  AND NOT i.indisunique        -- Unique 제약 인덱스 제외
  AND NOT i.indisprimary       -- PK 제외
  AND s.schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(s.indexrelid) DESC;

-- 참고: pg_stat_user_indexes는 마지막 통계 리셋 이후의 사용량
-- 리셋 시점 확인:
-- SELECT stats_reset FROM pg_stat_database WHERE datname = current_database();

-- ------------------------------------------------------------
-- 1.2 인덱스 부족 테이블 탐지
-- Sequential scan이 많고 index scan이 적은 테이블
-- ------------------------------------------------------------
SELECT
    schemaname,
    relname AS table_name,
    seq_scan,
    idx_scan,
    CASE
        WHEN seq_scan + idx_scan > 0
        THEN ROUND(
            idx_scan::numeric / (seq_scan + idx_scan) * 100, 2
        )
        ELSE 0
    END AS idx_scan_pct,
    n_live_tup AS estimated_rows,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_stat_user_tables
WHERE n_live_tup > 10000       -- 만 행 이상 테이블만
  AND seq_scan > idx_scan      -- seq scan이 더 많은 경우
  AND seq_scan > 100           -- 최소 100회 이상 스캔
ORDER BY seq_tup_read DESC     -- 읽은 행 수 기준 정렬
LIMIT 20;

-- ------------------------------------------------------------
-- 1.3 인덱스 Bloat 추정
-- dead tuple이 많은 인덱스 식별
-- 참고: 정확한 bloat 분석은 pgstattuple 확장 필요
-- ------------------------------------------------------------
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    ROUND(
        pg_relation_size(indexrelid)::numeric /
        NULLIF(pg_relation_size(relid), 0) * 100, 2
    ) AS index_to_table_pct,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
JOIN pg_index i ON pg_stat_user_indexes.indexrelid = i.indexrelid
WHERE pg_relation_size(indexrelid) > 10 * 1024 * 1024  -- 10MB 이상 인덱스
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- pgstattuple 확장으로 정확한 bloat 확인:
-- CREATE EXTENSION IF NOT EXISTS pgstattuple;
-- SELECT * FROM pgstatindex('index_name');
-- avg_leaf_density < 50% 이면 REINDEX 고려

-- ------------------------------------------------------------
-- 1.4 중복 인덱스 탐지
-- 동일한 컬럼 조합의 인덱스가 중복 존재하는 경우
-- 예: (a, b)와 (a, b, c)가 있으면 (a, b)는 대부분 불필요
-- ------------------------------------------------------------
SELECT
    a.indrelid::regclass AS table_name,
    a.indexrelid::regclass AS index_1,
    b.indexrelid::regclass AS index_2,
    pg_size_pretty(pg_relation_size(a.indexrelid)) AS index_1_size,
    pg_size_pretty(pg_relation_size(b.indexrelid)) AS index_2_size
FROM pg_index a
JOIN pg_index b
    ON a.indrelid = b.indrelid
    AND a.indexrelid != b.indexrelid
    AND a.indkey::text IS NOT NULL
WHERE
    -- a의 키 컬럼이 b의 키 컬럼의 prefix인 경우
    (
        a.indkey::text = ANY(
            ARRAY(
                SELECT string_agg(x, ' ')
                FROM (
                    SELECT unnest(b.indkey::int[])::text AS x
                    LIMIT array_length(a.indkey, 1)
                ) sub
            )
        )
    )
    AND a.indisunique = false   -- 고유 인덱스는 제외
    AND b.indisunique = false
    AND a.indexrelid::regclass::text < b.indexrelid::regclass::text  -- 중복 제거
ORDER BY pg_relation_size(a.indexrelid) DESC;

-- 참고: 위 쿼리는 간단한 prefix 중복만 탐지
-- 복잡한 케이스는 수동 확인 필요

-- ------------------------------------------------------------
-- 1.5 인덱스 효율성 분석
-- 인덱스 사용 빈도 대비 크기 비율
-- ------------------------------------------------------------
SELECT
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan AS scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    CASE
        WHEN idx_scan > 0
        THEN ROUND(idx_tup_read::numeric / idx_scan, 2)
        ELSE 0
    END AS avg_tuples_per_scan
FROM pg_stat_user_indexes
WHERE pg_relation_size(indexrelid) > 1024 * 1024  -- 1MB 이상
ORDER BY
    CASE WHEN idx_scan = 0 THEN 0 ELSE 1 END,  -- 미사용 우선
    pg_relation_size(indexrelid) DESC
LIMIT 30;

-- ------------------------------------------------------------
-- 1.6 인덱스 추천: 자주 필터링되는 컬럼
-- pg_stat_statements에서 WHERE 절에 자주 등장하는 패턴 확인
-- (수동 분석 보조용)
-- ------------------------------------------------------------
SELECT
    queryid,
    LEFT(query, 200) AS query_preview,
    calls,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms,
    rows
FROM pg_stat_statements
WHERE query ILIKE '%seq scan%'           -- 실행 계획이 아닌 쿼리 텍스트
   OR (shared_blks_read > shared_blks_hit  -- 디스크 읽기가 캐시 히트보다 많은
       AND calls > 10)
ORDER BY total_exec_time DESC
LIMIT 20;

-- 위 결과에서 느린 쿼리의 WHERE 절을 분석하여 인덱스 추천
-- EXPLAIN ANALYZE로 각 쿼리를 개별 확인 필요


-- ************************************************************
-- SECTION 2: MySQL
-- ************************************************************

-- ------------------------------------------------------------
-- 2.1 미사용 인덱스 탐지 (sys 스키마)
-- ------------------------------------------------------------
/*
SELECT
    object_schema AS db_name,
    object_name AS table_name,
    index_name
FROM sys.schema_unused_indexes
WHERE object_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY object_schema, object_name;
*/

-- ------------------------------------------------------------
-- 2.2 중복 인덱스 탐지 (sys 스키마)
-- 완전히 중복이거나 prefix가 겹치는 인덱스
-- ------------------------------------------------------------
/*
SELECT
    table_schema AS db_name,
    table_name,
    redundant_index_name,
    redundant_index_columns,
    dominant_index_name,
    dominant_index_columns,
    subpart_exists,
    sql_drop_index
FROM sys.schema_redundant_indexes
WHERE table_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY table_schema, table_name;
*/

-- ------------------------------------------------------------
-- 2.3 인덱스별 사용 통계
-- ------------------------------------------------------------
/*
SELECT
    OBJECT_SCHEMA AS db_name,
    OBJECT_NAME AS table_name,
    INDEX_NAME AS index_name,
    COUNT_READ AS reads,
    COUNT_WRITE AS writes,
    COUNT_FETCH AS fetches,
    COUNT_INSERT AS inserts,
    COUNT_UPDATE AS updates,
    COUNT_DELETE AS deletes,
    ROUND(SUM_TIMER_WAIT / 1e12, 2) AS total_latency_sec
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys')
  AND INDEX_NAME IS NOT NULL
ORDER BY
    CASE WHEN COUNT_READ = 0 THEN 0 ELSE 1 END,  -- 미사용 우선
    SUM_TIMER_WAIT DESC
LIMIT 30;
*/

-- ------------------------------------------------------------
-- 2.4 Full Table Scan이 많은 테이블
-- 인덱스 추가 대상
-- ------------------------------------------------------------
/*
SELECT
    OBJECT_SCHEMA AS db_name,
    OBJECT_NAME AS table_name,
    COUNT_READ AS total_reads,
    COUNT_FETCH AS index_reads,
    COUNT_READ - COUNT_FETCH AS full_scans,
    ROUND(
        (COUNT_READ - COUNT_FETCH) /
        NULLIF(COUNT_READ, 0) * 100, 2
    ) AS full_scan_pct
FROM performance_schema.table_io_waits_summary_by_table
WHERE OBJECT_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys')
  AND COUNT_READ > 1000
  AND COUNT_READ > COUNT_FETCH
ORDER BY full_scan_pct DESC
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.5 인덱스 카디널리티 확인
-- 카디널리티가 낮은 인덱스는 효과가 적을 수 있음
-- ------------------------------------------------------------
/*
SELECT
    TABLE_SCHEMA AS db_name,
    TABLE_NAME AS table_name,
    INDEX_NAME AS index_name,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns,
    CARDINALITY,
    (SELECT TABLE_ROWS FROM information_schema.TABLES t
     WHERE t.TABLE_SCHEMA = s.TABLE_SCHEMA
       AND t.TABLE_NAME = s.TABLE_NAME) AS table_rows,
    ROUND(
        CARDINALITY /
        NULLIF(
            (SELECT TABLE_ROWS FROM information_schema.TABLES t
             WHERE t.TABLE_SCHEMA = s.TABLE_SCHEMA
               AND t.TABLE_NAME = s.TABLE_NAME),
        0) * 100, 2
    ) AS selectivity_pct
FROM information_schema.STATISTICS s
WHERE TABLE_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys',
                           'information_schema')
GROUP BY TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, CARDINALITY
ORDER BY selectivity_pct ASC
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.6 인덱스 크기 확인
-- 인덱스가 데이터보다 큰 경우 과다 인덱싱 의심
-- ------------------------------------------------------------
/*
SELECT
    TABLE_SCHEMA AS db_name,
    TABLE_NAME AS table_name,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) AS data_size_mb,
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS index_size_mb,
    ROUND(INDEX_LENGTH / NULLIF(DATA_LENGTH, 0) * 100, 2) AS index_to_data_pct,
    TABLE_ROWS AS estimated_rows
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys',
                           'information_schema')
  AND TABLE_TYPE = 'BASE TABLE'
  AND DATA_LENGTH > 0
ORDER BY INDEX_LENGTH DESC
LIMIT 20;
-- index_to_data_pct > 200% 이면 과다 인덱싱 검토
*/
