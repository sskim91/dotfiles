# Query Optimization Checklist

느린 쿼리를 체계적으로 최적화하는 4단계 프로세스.

## 최적화 프로세스 개요

```
Phase 1: Identify (식별)
    ↓
Phase 2: Analyze (분석)
    ↓
Phase 3: Optimize (최적화)
    ↓
Phase 4: Verify (검증)
    ↓
반복 (목표 달성까지)
```

---

## Phase 1: Identify (느린 쿼리 식별)

### 체크리스트

- [ ] Slow query log 활성화 및 확인
- [ ] APM 도구에서 느린 DB 호출 식별
- [ ] 가장 빈번하게 실행되는 쿼리 확인
- [ ] 총 실행 시간이 가장 긴 쿼리 확인

### 도구

```sql
-- PostgreSQL: 총 시간 기준 Top 쿼리
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- MySQL: Performance Schema
SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT/1e12 AS total_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

### 우선순위 결정

| 기준 | 가중치 | 설명 |
|------|--------|------|
| 총 실행 시간 (calls × mean_time) | 최고 | 시스템 전체 부하 기여도 |
| 평균 실행 시간 | 높음 | 사용자 체감 지연 |
| 호출 빈도 | 중간 | 작은 개선도 큰 효과 |
| 비즈니스 영향도 | 중간 | 핵심 기능의 쿼리 우선 |

---

## Phase 2: Analyze (쿼리 분석)

### 체크리스트

- [ ] EXPLAIN (ANALYZE, BUFFERS) 실행
- [ ] 전체 테이블 스캔 확인 (Seq Scan / type=ALL)
- [ ] 추정 행 수 vs 실제 행 수 비교
- [ ] 인덱스 사용 여부 확인
- [ ] Join 방식 확인 (Nested Loop / Hash Join / Merge Join)
- [ ] 정렬/임시 테이블 확인
- [ ] 디스크 spill 확인 (Disk sort, temp files)
- [ ] 테이블 통계가 최신인지 확인 (ANALYZE 실행 시점)

### EXPLAIN 빨간 신호

| 신호 | PostgreSQL | MySQL | 의미 |
|------|-----------|-------|------|
| Full Table Scan | `Seq Scan` | `type: ALL` | 인덱스 없음/미사용 |
| 행 추정 오류 | estimated vs actual 10x+ 차이 | `rows` vs 실제 큰 차이 | 통계 갱신 필요 |
| 디스크 정렬 | `Sort Method: external merge Disk` | `Using filesort` + 대량 행 | work_mem/sort_buffer 부족 |
| 임시 테이블 | `Sort`, `HashAggregate` | `Using temporary` | GROUP BY/DISTINCT 최적화 필요 |
| 높은 loops | `loops=10000+` | N/A | Nested Loop 비효율 |
| 재확인 제거 | `Rows Removed by Filter: 대량` | `rows × (1-filtered/100)` | 인덱스 부족 |

---

## Phase 3: Optimize (최적화 적용)

### 3.1 인덱스 최적화

- [ ] WHERE 절 컬럼에 적절한 인덱스 존재?
- [ ] 복합 인덱스 컬럼 순서가 올바른가? (Equality → Range → Sort)
- [ ] Covering index로 테이블 접근 제거 가능?
- [ ] Partial index로 인덱스 크기 축소 가능?
- [ ] 불필요한/중복 인덱스 제거?

### 3.2 쿼리 리라이팅

**SELECT 최적화:**
- [ ] `SELECT *` → 필요한 컬럼만 명시
- [ ] 불필요한 DISTINCT 제거
- [ ] 불필요한 ORDER BY 제거 (서브쿼리 내부 등)

**WHERE 최적화:**
- [ ] 인덱스 컬럼에 함수 적용 제거 (`WHERE YEAR(date)` → `WHERE date >= '2025-01-01'`)
- [ ] 암묵적 타입 변환 제거 (문자열 컬럼에 숫자 비교 등)
- [ ] OR 조건 → UNION ALL 변환 검토
- [ ] `NOT IN (subquery)` → `NOT EXISTS` 또는 `LEFT JOIN ... IS NULL` 변환
- [ ] `IN (대량 리스트)` → 임시 테이블 JOIN 변환

**JOIN 최적화:**
- [ ] JOIN 컬럼에 인덱스 존재?
- [ ] JOIN 컬럼의 데이터 타입/collation 일치?
- [ ] 불필요한 JOIN 제거 (사용하지 않는 테이블)
- [ ] 서브쿼리 → JOIN 변환 검토

**집계 최적화:**
- [ ] COUNT(*) → 추정값 사용 가능? (대시보드 등)
- [ ] GROUP BY 컬럼에 인덱스?
- [ ] HAVING → WHERE로 이동 가능한 조건?

**페이지네이션 최적화:**
- [ ] OFFSET 기반 → Cursor 기반 변환
- [ ] 커서 컬럼에 인덱스 존재?

### 3.3 N+1 쿼리 해결

- [ ] ORM 쿼리 로그에서 반복 패턴 확인
- [ ] Lazy Loading → Eager Loading (JOIN/Batch) 변환
- [ ] DataLoader/Batch 패턴 적용

### 3.4 스키마 최적화

- [ ] 적절한 데이터 타입 사용? (VARCHAR(255) 대신 실제 필요 길이)
- [ ] 정규화/비정규화 균형?
- [ ] 파티셔닝 검토? (대형 테이블, 시계열 데이터)

### 3.5 설정 최적화

- [ ] work_mem/sort_buffer_size 적절?
- [ ] 연결 풀링 사용?
- [ ] 통계 자동 갱신 설정 적절? (autovacuum/ANALYZE)

---

## Phase 4: Verify (검증)

### 체크리스트

- [ ] EXPLAIN (ANALYZE, BUFFERS) 재실행 → 개선 확인
- [ ] 실행 시간 비교 (before vs after)
- [ ] 반환 결과가 동일한지 확인 (기능 무결성)
- [ ] 프로덕션 유사 데이터셋에서 테스트
- [ ] Write 성능 영향 확인 (인덱스 추가 시)
- [ ] 동시성 테스트 (락 경합 등)
- [ ] 모니터링 설정 (개선 효과 지속 확인)

### Before/After 비교 템플릿

```
=== Query Optimization Report ===

Query: [쿼리 설명]

Before:
  - Execution Time: ___ms
  - Plan: [Seq Scan / Index Scan / ...]
  - Rows Scanned: ___
  - Buffers Read: ___

After:
  - Execution Time: ___ms (↓ __% 개선)
  - Plan: [변경된 플랜]
  - Rows Scanned: ___ (↓ __% 감소)
  - Buffers Read: ___ (↓ __% 감소)

Changes Applied:
  - [ ] 인덱스 추가/변경: ___
  - [ ] 쿼리 리라이팅: ___
  - [ ] 설정 변경: ___
```

---

## 빠른 참조: 일반적 최적화 변환

| 문제 패턴 | 최적화 | 기대 효과 |
|-----------|--------|-----------|
| Full Table Scan | 적절한 인덱스 추가 | 100x-10000x |
| N+1 쿼리 | JOIN 또는 Batch 로딩 | N배 감소 |
| OFFSET 페이지네이션 | Cursor 기반 | 일정한 성능 |
| SELECT * | 필요 컬럼만 + Covering Index | 2-10x |
| 함수로 감싼 WHERE | Expression Index 또는 쿼리 변환 | 10-100x |
| OR 조건 | UNION ALL | 2-10x |
| Correlated Subquery | JOIN 변환 | 10-1000x |
| COUNT(*) 전체 | 추정값 또는 캐시 | 100x+ |
| 대형 테이블 정렬 | 인덱스 또는 work_mem 증가 | 2-50x |
| 타입 불일치 JOIN | 타입 통일 | 10-100x |

---

## 최적화 Anti-Patterns

해서는 안 되는 것들:

| Anti-Pattern | 왜 위험한가 | 대안 |
|-------------|------------|------|
| EXPLAIN 없이 인덱스 추가 | 효과 없는 인덱스가 Write 성능만 저하 | 반드시 EXPLAIN 먼저 |
| 모든 컬럼에 인덱스 | INSERT/UPDATE 극도로 느려짐 | 쿼리 패턴 기반 선별 |
| Query hint 남용 | 옵티마이저가 더 나은 선택 못함 | 통계 갱신, 인덱스 개선 우선 |
| 프로덕션에서 바로 EXPLAIN ANALYZE | 실제 쿼리 실행으로 부하 발생 | 스테이징에서 먼저 |
| 인덱스 추가 후 모니터링 안함 | 시간 지나면 효과 변화 | 정기 점검 스케줄 |
