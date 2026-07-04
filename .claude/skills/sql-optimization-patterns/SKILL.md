---
name: sql-optimization-patterns
description: Use when debugging slow queries, designing indexes, analyzing EXPLAIN output, resolving N+1 problems, or tuning database performance. Do NOT use for basic SQL, simple CRUD, or JPA entity design (use jpa-patterns).
---

# SQL Optimization Patterns

진단 스크립트와 판단 규칙만 담는다. 인덱스·EXPLAIN 일반 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **ALWAYS** `EXPLAIN ANALYZE` before optimizing — 추측 금지, 실측 기반
2. **ALWAYS** `ANALYZE` after bulk data changes — "인덱스 있는데 Seq Scan"의 최다 원인은 낡은 통계
3. **NEVER** OFFSET for deep pagination — keyset/cursor 사용
4. **NEVER** function on indexed column in WHERE — expression index 또는 정규화 저장
5. **NEVER** over-index — 인덱스마다 쓰기 비용. 미사용 인덱스 주기적 제거 (`scripts/index-recommendations.sql`)
6. **ALWAYS** monitor slow query log — 문제는 코드가 아닌 운영에서 발견됨

## Diagnostic Scripts

실행 가능한 진단 SQL (PG/MySQL):

- [scripts/analyze-slow-queries.sql](scripts/analyze-slow-queries.sql) — 슬로우 쿼리 진단 (`pg_stat_statements` 필요)
- [scripts/index-recommendations.sql](scripts/index-recommendations.sql) — 미사용/중복 인덱스 탐지

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ "인덱스 있는데 안 쓰임"을 버그로 판단 → 행 비율 높으면 옵티마이저가 Seq Scan 선택하는 게 정상. 통계부터 갱신(`ANALYZE`)
- ❌ rows estimate vs actual 10x+ 차이 방치 → `ANALYZE` 또는 `ALTER TABLE ... SET STATISTICS` 높이기
- ❌ CTE를 optimization fence로 가정 → PostgreSQL 12+는 inline됨. 필요시 `MATERIALIZED` 명시
- ❌ 복합 인덱스에 range 컬럼을 앞에 → equality first, range last
- ❌ `WHERE id = '123'` (implicit cast) → 타입 일치시키기, 인덱스 무시될 수 있음

## Cross-References

| Topic | Skill |
|-------|-------|
| JPA entity, repository, N+1 in Hibernate | `jpa-patterns` |

## References

- [Use The Index, Luke](https://use-the-index-luke.com/) — SQL indexing bible
- [PostgreSQL EXPLAIN docs](https://www.postgresql.org/docs/current/using-explain.html)
