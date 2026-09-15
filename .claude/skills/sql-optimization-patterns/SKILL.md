---
name: sql-optimization-patterns
description: Use when debugging slow queries, designing indexes, analyzing EXPLAIN output, resolving N+1 problems, or tuning database performance. Do NOT use for basic SQL, simple CRUD.
---

# SQL Optimization Patterns

실행 계획을 읽는 판단 기준과 PostgreSQL/MySQL 진단 SQL을 제공한다. DB별 명령과 통계 컬럼은 버전·확장·권한에 의존한다.

## 진단 전 확인

- DB 종류·버전, 대상 환경, 쿼리·파라미터, 테이블 규모와 인덱스를 확인한다. 로컬 checkout과 실제 DB 상태를 구분한다.
- 기존 로그·통계·실행 계획부터 읽는다. 지원되는 옵션은 대상 버전의 공식 문서로 확인한다.
- `EXPLAIN ANALYZE`는 쿼리를 실제로 실행한다. 쓰기나 부하가 발생하는 실행은 이미 승인된 범위에서만 수행한다. 읽기 전용 리뷰라면 기존 계획이나 실행하지 않는 `EXPLAIN`을 활용한다.
- 통계 갱신, 인덱스 생성·삭제, 설정 변경은 진단 결과와 구분해 영향·적용 범위를 제시한다.

## 판단 기준

- 변경 전후를 같은 조건에서 비교한다. 실행 시간, 처리 행 수, I/O, 추정과 실제 행 수 차이를 함께 기록한다.
- Seq Scan만으로 장애를 단정하지 않는다. 데이터 분포·선택도·통계의 최신성을 확인한다.
- 깊은 OFFSET이 병목이면 keyset/cursor를 검토하되 정렬·소비자 계약을 함께 확인한다.
- 컬럼 함수·형 변환과 복합 인덱스 순서는 실제 계획으로 평가한다. 인덱스의 읽기 이득과 쓰기·공간 비용을 비교한다.
- 미사용 통계만으로 인덱스를 삭제하지 않는다. 관측 기간·통계 초기화·제약조건·주기 작업을 확인한다.
- 대량 변경 후 통계가 낡았는지 확인하고 필요하면 대상 DB의 통계 갱신을 제안한다.

## 진단 SQL 선택

파일 전체를 실행하지 말고 대상 DB와 목적에 맞는 쿼리를 읽어 선택한다. 샘플 이름·임계값·통계 컬럼을 실제 환경에 맞춰 확인한다.

| 자원 | 용도와 전제 |
|---|---|
| [analyze-slow-queries.sql](scripts/analyze-slow-queries.sql) | 느린 쿼리 분석. PostgreSQL의 해당 구간은 `pg_stat_statements`가 필요 |
| [index-recommendations.sql](scripts/index-recommendations.sql) | 미사용·중복 인덱스 후보 조사. 결과는 삭제 명령이 아닌 검토 자료 |

## 버전별 재확인

CTE의 inline/materialization은 DB·버전·쿼리 조건에 따라 달라진다. 특정 버전 이상이면 모든 CTE가 inline된다고 가정하지 않는다. 실행 계획과 대상 버전 문서를 대조한다.

## 결과 보고

확인한 환경과 실행한 쿼리, 관측 결과, 원인 추론, 제안 변경, 미확인 범위를 구분한다. 실행하지 않은 SQL은 검증 완료로 보고하지 않는다.

## 공식 문서

아래는 문서 진입점이다. 실제 DB 버전을 선택해서 읽는다.

- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/sql-explain.html)
- [PostgreSQL WITH Queries](https://www.postgresql.org/docs/current/queries-with.html)
