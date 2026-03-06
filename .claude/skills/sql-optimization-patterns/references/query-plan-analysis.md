# Query Plan Analysis - EXPLAIN Deep Dive

PostgreSQL과 MySQL의 EXPLAIN 출력을 읽고 해석하는 상세 가이드.
SKILL.md의 기본 EXPLAIN 사용법을 넘어서는 심화 내용.

## 1. PostgreSQL EXPLAIN 해부

### 실행 옵션

```sql
EXPLAIN                    query;  -- 추정 비용만 (실행 안함)
EXPLAIN ANALYZE            query;  -- 실제 실행 + 통계
EXPLAIN (ANALYZE, BUFFERS) query;  -- + I/O 상세
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) query;  -- + 출력 컬럼 상세
EXPLAIN (ANALYZE, BUFFERS, SETTINGS) query; -- + 비기본 설정 표시
EXPLAIN (FORMAT JSON)      query;  -- JSON 출력 (도구 연동)
EXPLAIN (FORMAT YAML)      query;  -- YAML 출력
```

### 출력 해석

```
Nested Loop Left Join  (cost=0.85..16.92 rows=1 width=550)
                              ↑              ↑       ↑
                        startup..total   추정행수  행 너비(bytes)
  (actual time=0.035..0.041 rows=1 loops=1)
         ↑          ↑       ↑       ↑
    첫 행 시간  마지막 행   실제행수  반복횟수
  Buffers: shared hit=5 read=2 dirtied=1
                   ↑       ↑        ↑
            캐시 히트   디스크 읽기  더티 페이지
```

**주요 필드 설명:**

| 필드 | 설명 | 주의사항 |
|------|------|----------|
| `cost` | `startup..total` 형식의 추정 비용 | 단위는 `seq_page_cost` 기준 (기본 1.0) |
| `rows` | 추정 반환 행 수 | 실제와 크게 다르면 통계 갱신 필요 |
| `width` | 결과 행의 평균 바이트 크기 | |
| `actual time` | 밀리초 단위 실제 시간 | loops > 1이면 1회 기준 |
| `loops` | 노드 실행 반복 횟수 | 실제 총 시간 = actual time × loops |
| `Buffers: shared hit` | Buffer Pool에서 읽은 페이지 수 | |
| `Buffers: shared read` | 디스크에서 읽은 페이지 수 | 많으면 shared_buffers 부족 의심 |
| `Buffers: shared dirtied` | 수정된 페이지 수 | |

### Startup Cost vs Total Cost

```
-- Startup Cost가 높은 노드: Blocking 연산 (모든 입력을 받아야 출력 시작)
Sort (cost=5000.00..5100.00)     -- startup=5000 (정렬 완료까지 대기)
  → Seq Scan ...                 -- total=5000

-- Startup Cost가 낮은 노드: Streaming 연산 (입력을 받으며 바로 출력)
Nested Loop (cost=0.85..16.92)   -- startup=0.85 (바로 시작)
```

| 구분 | Blocking (높은 startup) | Streaming (낮은 startup) |
|------|------------------------|-------------------------|
| 노드 타입 | Sort, HashAggregate, Hash | Nested Loop, Merge Join, Index Scan |
| 특징 | 전체 입력 필요 | 부분 입력으로 시작 가능 |
| 적합 | 배치 처리, 리포트 | 인터랙티브 쿼리, LIMIT |

## 2. PostgreSQL 노드 타입

### Scan 노드 (데이터 접근)

| 노드 | 설명 | 성능 | 언제 사용 |
|------|------|------|-----------|
| **Seq Scan** | 전체 테이블 순차 스캔 | 대형 테이블에서 느림 | 인덱스 없음, 대부분의 행 필요 |
| **Index Scan** | 인덱스 → 테이블 | 선택적 쿼리에 좋음 | WHERE 조건이 인덱스 매칭 |
| **Index Only Scan** | 인덱스만 (테이블 접근 안함) | 가장 빠름 | Covering index, visibility map 최신 |
| **Bitmap Index Scan** | 인덱스 → 비트맵 → 테이블 | 중간 선택성에 적합 | 여러 인덱스 조합, OR 조건 |
| **Bitmap Heap Scan** | 비트맵 → 테이블 | | Bitmap Index Scan 결과 사용 |
| **TID Scan** | 직접 행 접근 | 매우 빠름 | ctid 기반 접근 |

```
-- Bitmap Scan의 동작 원리
Bitmap Heap Scan on orders  (cost=...)
  Recheck Cond: (status = 'active' AND user_id = 123)
  →  BitmapAnd
       →  Bitmap Index Scan on idx_orders_status  (status = 'active')
       →  Bitmap Index Scan on idx_orders_user    (user_id = 123)
-- 두 인덱스의 비트맵을 AND 결합하여 테이블 접근 최소화
```

### Join 노드

| 노드 | 설명 | 메모리 | 적합한 경우 |
|------|------|--------|-------------|
| **Nested Loop** | 외부 루프의 각 행에 대해 내부 탐색 | 낮음 | 소규모 데이터, 내부에 인덱스 있을 때 |
| **Hash Join** | 작은 테이블로 해시 테이블 생성 → 큰 테이블 스캔 | work_mem 의존 | 대규모 equi-join, 인덱스 없을 때 |
| **Merge Join** | 정렬된 두 입력을 병합 | 낮음 | 사전 정렬된 데이터, 대규모 join |

```
-- Hash Join 예시
Hash Join  (cost=...)
  Hash Cond: (o.user_id = u.id)
  →  Seq Scan on orders o        -- Probe: 큰 테이블 스캔
  →  Hash                        -- Build: 작은 테이블로 해시 생성
       →  Seq Scan on users u

-- Nested Loop 예시 (내부에 인덱스 있을 때 효율적)
Nested Loop  (cost=...)
  →  Index Scan on users u       -- 외부 (적은 행)
  →  Index Scan on orders o      -- 내부 (인덱스로 빠른 탐색)
       Index Cond: (o.user_id = u.id)
```

### 기타 주요 노드

| 노드 | 설명 |
|------|------|
| **Sort** | ORDER BY, Merge Join 입력 정렬 |
| **HashAggregate** | GROUP BY (해시 기반) |
| **GroupAggregate** | GROUP BY (정렬 기반) |
| **Materialize** | 하위 결과를 메모리에 저장 (재사용) |
| **Gather** / **Gather Merge** | 병렬 worker 결과 수집 |
| **Append** | UNION ALL, 파티션 테이블 결합 |
| **Limit** | LIMIT 절 |
| **Unique** | DISTINCT |
| **WindowAgg** | Window Function 처리 |
| **CTE Scan** | WITH절 실체화된 결과 스캔 |
| **Subquery Scan** | 서브쿼리 결과 스캔 |

## 3. MySQL EXPLAIN 해부

### EXPLAIN 형식

```sql
-- 전통 테이블 형식
EXPLAIN SELECT * FROM orders WHERE user_id = 123;

-- TREE 형식 (8.0.16+, 가장 읽기 좋음)
EXPLAIN FORMAT=TREE SELECT * FROM orders WHERE user_id = 123;

-- JSON 형식 (도구 연동, 상세 비용)
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE user_id = 123;

-- 실제 실행 (8.0.18+)
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
```

### EXPLAIN 컬럼 해석 (테이블 형식)

| 컬럼 | 설명 | 주의사항 |
|------|------|----------|
| `id` | SELECT 식별자 | 같은 id = 같은 SELECT에서 JOIN |
| `select_type` | SELECT 유형 | SIMPLE, PRIMARY, SUBQUERY, DERIVED 등 |
| `table` | 접근 테이블 | `<derived2>` = id=2의 파생 테이블 |
| `type` | 접근 방법 (**가장 중요**) | 아래 상세 표 참조 |
| `possible_keys` | 사용 가능한 인덱스 | NULL이면 인덱스 후보 없음 |
| `key` | 실제 사용된 인덱스 | NULL이면 Full Table Scan |
| `key_len` | 사용된 인덱스 길이 (bytes) | 복합 인덱스에서 몇 컬럼 사용했는지 판단 |
| `ref` | 인덱스 비교 대상 | const, 컬럼명 등 |
| `rows` | 추정 검사 행 수 | 실제와 다를 수 있음 |
| `filtered` | WHERE 조건으로 필터링 후 남는 비율(%) | 낮으면 인덱스 개선 필요 |
| `Extra` | 추가 정보 (**중요**) | 아래 상세 표 참조 |

### Access Type (type 컬럼) - 성능 순서

| type | 설명 | 성능 |
|------|------|------|
| `system` | 테이블에 행이 1개 | 최고 |
| `const` | PK/Unique로 1행 접근 | 최고 |
| `eq_ref` | JOIN에서 PK/Unique로 1행 | 매우 좋음 |
| `ref` | 비고유 인덱스로 다수 행 | 좋음 |
| `fulltext` | 전문 검색 인덱스 | 좋음 |
| `ref_or_null` | ref + NULL 검색 | 좋음 |
| `index_merge` | 여러 인덱스 병합 | 보통 |
| `range` | 인덱스 범위 스캔 | 보통 |
| `index` | 전체 인덱스 스캔 (데이터 안 봄) | 나쁨 |
| `ALL` | 전체 테이블 스캔 | 최악 |

**목표: `ref` 이상을 유지. `ALL`은 반드시 개선 대상.**

### Extra 컬럼 주요 값

| Extra 값 | 의미 | 대응 |
|-----------|------|------|
| `Using index` | Covering index (테이블 접근 안함) | 좋음, 유지 |
| `Using where` | 스토리지 엔진 결과를 서버에서 필터링 | 인덱스 개선 검토 |
| `Using temporary` | 임시 테이블 생성 | GROUP BY/ORDER BY 인덱스 검토 |
| `Using filesort` | 정렬 연산 발생 | ORDER BY 인덱스 검토 |
| `Using index condition` | ICP (Index Condition Pushdown) | 좋음 |
| `Using join buffer` | 조인 버퍼 사용 (인덱스 없음) | 조인 컬럼 인덱스 추가 |
| `Backward index scan` | 역방향 인덱스 스캔 | DESC 인덱스 고려 |
| `Using MRR` | Multi-Range Read 최적화 | 좋음 |

### EXPLAIN FORMAT=TREE 읽기

```
-> Limit: 10 row(s)  (actual time=0.5..12.3 rows=10 loops=1)
    -> Nested loop inner join  (cost=1234 rows=100)
        -> Index range scan on o using idx_date  (cost=567 rows=50)
            (actual time=0.3..5.1 rows=50 loops=1)
        -> Single-row index lookup on c using PRIMARY (id=o.customer_id)
            (cost=0.25 rows=1)
            (actual time=0.01..0.01 rows=1 loops=50)
```

**읽는 순서: 가장 안쪽(깊은 들여쓰기)부터 바깥으로.**

1. `idx_date` 인덱스로 orders 50행 범위 스캔
2. 각 행마다 customers PK로 1행 조회 (50회 반복)
3. 결과에서 10행만 반환

## 4. 문제 패턴 식별

### 패턴 1: 추정치와 실제 행 수 불일치

```
Seq Scan on orders  (cost=0.00..25000.00 rows=100 width=100)
                                              ↑
                                         추정: 100행
  (actual time=0.1..500.0 rows=500000 loops=1)
                                  ↑
                             실제: 50만행!
```

**원인**: 오래된 통계 정보
**해결**: `ANALYZE orders;` 실행

### 패턴 2: Seq Scan on 대형 테이블

```
Seq Scan on orders  (cost=0.00..125000.00 rows=5000000 width=100)
  Filter: (status = 'active')
  Rows Removed by Filter: 4900000
```

**원인**: 적절한 인덱스 없음 또는 옵티마이저가 Seq Scan 선택
**해결**: 인덱스 생성 또는 `random_page_cost` 조정

### 패턴 3: Nested Loop의 높은 loops

```
Nested Loop  (cost=0.43..250000.00 rows=1000)
  →  Seq Scan on users  (rows=10000 loops=1)
  →  Index Scan on orders  (rows=5 loops=10000)
                                       ↑
                              10000번 반복! 총 50000행 스캔
```

**원인**: 외부 테이블이 너무 크거나 Hash Join이 더 적합
**해결**: `SET enable_nestloop = off;`로 다른 조인 확인, 또는 인덱스 개선

### 패턴 4: Sort + 높은 메모리 사용

```
Sort  (cost=50000.00..50500.00)
  Sort Key: created_at
  Sort Method: external merge  Disk: 256000kB
                               ↑
                          디스크 spill 발생!
```

**원인**: work_mem 부족
**해결**: `SET work_mem = '256MB';` 또는 정렬 인덱스 추가

### 패턴 5: Bitmap Heap Scan의 Lossy 비트맵

```
Bitmap Heap Scan on events
  Recheck Cond: (type = 'click')
  Rows Removed by Recheck: 50000
                            ↑
                   재확인으로 제거된 행이 많음
```

**원인**: work_mem 부족으로 비트맵이 lossy (정확한 행 위치 대신 페이지 위치만 저장)
**해결**: work_mem 증가

## 5. 시각화 도구

### PostgreSQL

| 도구 | URL | 특징 |
|------|-----|------|
| **explain.dalibo.com** | https://explain.dalibo.com | 무료, EXPLAIN 시각화 |
| **pganalyze** | https://pganalyze.com | 상용, 자동 모니터링 |
| **auto_explain** | 내장 확장 | 느린 쿼리 자동 EXPLAIN 로깅 |

```sql
-- auto_explain 설정 (느린 쿼리 자동 로깅)
LOAD 'auto_explain';
SET auto_explain.log_min_duration = '1s';
SET auto_explain.log_analyze = true;
SET auto_explain.log_buffers = true;
```

### MySQL

| 도구 | 특징 |
|------|------|
| **MySQL Workbench** | Visual EXPLAIN 내장 |
| **Percona PMM** | 무료, 종합 모니터링 |
| **pt-query-digest** | Percona Toolkit, slow log 분석 |

## 6. 분석 체크리스트

EXPLAIN 결과를 볼 때 순서대로 확인:

1. **전체 테이블 스캔 여부**: Seq Scan (PG) / type=ALL (MySQL)
2. **추정 vs 실제 행 수 차이**: 10배 이상 차이나면 ANALYZE 필요
3. **인덱스 사용 여부**: 적절한 인덱스가 사용되고 있는지
4. **Join 타입**: 대형 테이블 간 Nested Loop은 위험 신호
5. **정렬/임시 테이블**: Sort + disk spill, Using temporary
6. **Buffers (PG)**: shared read가 shared hit보다 많으면 캐시 부족
7. **loops 곱하기**: actual time × loops = 실제 총 시간
8. **Filter로 제거된 행**: Rows Removed by Filter가 많으면 인덱스 부족
