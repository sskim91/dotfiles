-- ============================================================
-- Slow Query Analysis Scripts
-- PostgreSQL과 MySQL에서 느린 쿼리를 식별하고 분석하는 스크립트
-- ============================================================

-- ************************************************************
-- SECTION 1: PostgreSQL
-- 사전 요구: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- ************************************************************

-- ------------------------------------------------------------
-- 1.1 총 실행 시간 기준 Top 20 쿼리
-- 시스템 전체 부하에 가장 큰 영향을 주는 쿼리 식별
-- ------------------------------------------------------------
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    ROUND(total_exec_time::numeric, 2) AS total_ms,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms,
    ROUND(min_exec_time::numeric, 2) AS min_ms,
    ROUND(max_exec_time::numeric, 2) AS max_ms,
    ROUND(stddev_exec_time::numeric, 2) AS stddev_ms,
    ROUND((100 * total_exec_time /
        NULLIF(SUM(total_exec_time) OVER(), 0))::numeric, 2) AS pct_total,
    rows
FROM pg_stat_statements
WHERE queryid IS NOT NULL
ORDER BY total_exec_time DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 1.2 평균 실행 시간 기준 Top 20 쿼리
-- 사용자 체감 지연이 가장 큰 쿼리 식별
-- ------------------------------------------------------------
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms,
    ROUND(max_exec_time::numeric, 2) AS max_ms,
    rows AS avg_rows,
    shared_blks_hit + shared_blks_read AS total_blks,
    CASE
        WHEN shared_blks_hit + shared_blks_read > 0
        THEN ROUND(
            shared_blks_hit::numeric /
            (shared_blks_hit + shared_blks_read) * 100, 2
        )
        ELSE 100
    END AS cache_hit_pct
FROM pg_stat_statements
WHERE calls >= 10  -- 최소 10회 이상 실행된 쿼리만
ORDER BY mean_exec_time DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 1.3 디스크 I/O가 많은 쿼리 (캐시 미스율 높은 쿼리)
-- Buffer Pool 부족 또는 인덱스 부재 의심
-- ------------------------------------------------------------
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    shared_blks_read AS disk_reads,
    shared_blks_hit AS cache_hits,
    CASE
        WHEN shared_blks_hit + shared_blks_read > 0
        THEN ROUND(
            shared_blks_read::numeric /
            (shared_blks_hit + shared_blks_read) * 100, 2
        )
        ELSE 0
    END AS disk_read_pct,
    temp_blks_read + temp_blks_written AS temp_blks,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms
FROM pg_stat_statements
WHERE shared_blks_read > 1000  -- 디스크 읽기 1000 블록 이상
ORDER BY shared_blks_read DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 1.4 디스크 spill 발생 쿼리 (temp 파일 사용)
-- work_mem 부족 의심
-- ------------------------------------------------------------
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    temp_blks_read,
    temp_blks_written,
    pg_size_pretty((temp_blks_written * 8192)::bigint) AS temp_size,
    ROUND(mean_exec_time::numeric, 2) AS mean_ms
FROM pg_stat_statements
WHERE temp_blks_written > 0
ORDER BY temp_blks_written DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 1.5 현재 실행 중인 느린 쿼리
-- 실시간 모니터링
-- ------------------------------------------------------------
SELECT
    pid,
    NOW() - pg_stat_activity.query_start AS duration,
    state,
    wait_event_type,
    wait_event,
    LEFT(query, 100) AS query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
  AND NOW() - pg_stat_activity.query_start > INTERVAL '5 seconds'
ORDER BY duration DESC;

-- ------------------------------------------------------------
-- 1.6 테이블별 Sequential Scan 비율
-- 인덱스 부족 테이블 식별
-- ------------------------------------------------------------
SELECT
    schemaname,
    relname AS table_name,
    seq_scan,
    idx_scan,
    CASE
        WHEN seq_scan + idx_scan > 0
        THEN ROUND(seq_scan::numeric / (seq_scan + idx_scan) * 100, 2)
        ELSE 0
    END AS seq_scan_pct,
    seq_tup_read,
    idx_tup_fetch,
    n_live_tup AS estimated_rows
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 100  -- 최소 100회 이상 접근된 테이블
ORDER BY seq_scan_pct DESC, seq_tup_read DESC
LIMIT 20;

-- ------------------------------------------------------------
-- 1.7 Lock 대기 현황
-- 잠금 경합으로 인한 성능 저하 확인
-- ------------------------------------------------------------
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    LEFT(blocked_activity.query, 80) AS blocked_query,
    NOW() - blocked_activity.query_start AS blocked_duration,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    LEFT(blocking_activity.query, 80) AS blocking_query,
    blocking_locks.locktype
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
    ON blocked_locks.pid = blocked_activity.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity
    ON blocking_locks.pid = blocking_activity.pid
WHERE NOT blocked_locks.granted;

-- ------------------------------------------------------------
-- 1.8 Buffer Cache 히트율 (전체)
-- 99% 이상이 정상, 미만이면 shared_buffers 증가 검토
-- ------------------------------------------------------------
SELECT
    ROUND(
        SUM(blks_hit)::numeric /
        NULLIF(SUM(blks_hit + blks_read), 0) * 100, 2
    ) AS buffer_cache_hit_ratio
FROM pg_stat_database
WHERE datname = current_database();

-- ------------------------------------------------------------
-- 1.9 테이블 bloat 추정 (dead tuple 비율)
-- 높으면 VACUUM 필요
-- ------------------------------------------------------------
SELECT
    schemaname || '.' || relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup,
    n_dead_tup,
    ROUND(
        n_dead_tup::numeric /
        NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2
    ) AS dead_pct,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC
LIMIT 20;


-- ************************************************************
-- SECTION 2: MySQL
-- 사전 요구: Performance Schema 활성화 (기본 ON)
-- ************************************************************

-- ------------------------------------------------------------
-- 2.1 총 실행 시간 기준 Top 20 쿼리
-- ------------------------------------------------------------
/*
SELECT
    LEFT(DIGEST_TEXT, 100) AS query_preview,
    COUNT_STAR AS exec_count,
    ROUND(SUM_TIMER_WAIT / 1e12, 2) AS total_sec,
    ROUND(AVG_TIMER_WAIT / 1e12, 4) AS avg_sec,
    ROUND(MAX_TIMER_WAIT / 1e12, 4) AS max_sec,
    SUM_ROWS_EXAMINED AS rows_examined,
    SUM_ROWS_SENT AS rows_sent,
    SUM_NO_INDEX_USED AS no_index_count,
    FIRST_SEEN,
    LAST_SEEN
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.2 Full Table Scan 쿼리 (sys 스키마 사용)
-- ------------------------------------------------------------
/*
SELECT
    db,
    LEFT(query, 100) AS query_preview,
    exec_count,
    total_latency,
    no_index_used_count,
    rows_sent_avg,
    rows_examined_avg
FROM sys.statements_with_full_table_scans
WHERE db NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY no_index_used_count DESC
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.3 95 퍼센타일 느린 쿼리
-- ------------------------------------------------------------
/*
SELECT
    LEFT(query, 100) AS query_preview,
    db,
    exec_count,
    avg_latency,
    max_latency,
    rows_sent_avg,
    rows_examined_avg
FROM sys.statements_with_runtimes_in_95th_percentile
WHERE db NOT IN ('mysql', 'performance_schema', 'sys')
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.4 테이블별 I/O 통계
-- ------------------------------------------------------------
/*
SELECT
    OBJECT_SCHEMA AS db_name,
    OBJECT_NAME AS table_name,
    COUNT_READ,
    COUNT_WRITE,
    ROUND(SUM_TIMER_READ / 1e12, 2) AS read_latency_sec,
    ROUND(SUM_TIMER_WRITE / 1e12, 2) AS write_latency_sec,
    COUNT_FETCH AS selects,
    COUNT_INSERT AS inserts,
    COUNT_UPDATE AS updates,
    COUNT_DELETE AS deletes
FROM performance_schema.table_io_waits_summary_by_table
WHERE OBJECT_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;
*/

-- ------------------------------------------------------------
-- 2.5 현재 실행 중인 느린 쿼리
-- ------------------------------------------------------------
/*
SELECT
    ID AS process_id,
    USER,
    HOST,
    DB,
    COMMAND,
    TIME AS seconds,
    STATE,
    LEFT(INFO, 100) AS query_preview
FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep'
  AND TIME > 5
  AND INFO IS NOT NULL
ORDER BY TIME DESC;
*/

-- ------------------------------------------------------------
-- 2.6 InnoDB Buffer Pool 히트율
-- 99% 이상이 정상
-- ------------------------------------------------------------
/*
SELECT
    (1 - (
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status
         WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
        /
        NULLIF(
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status
             WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'),
        0)
    )) * 100 AS buffer_pool_hit_ratio;
*/

-- ------------------------------------------------------------
-- 2.7 임시 테이블 생성 비율
-- 높으면 tmp_table_size, max_heap_table_size 증가 검토
-- ------------------------------------------------------------
/*
SELECT
    VARIABLE_NAME,
    VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN (
    'Created_tmp_tables',
    'Created_tmp_disk_tables'
);
-- disk_tables / total_tables > 25% 이면 개선 필요
*/
