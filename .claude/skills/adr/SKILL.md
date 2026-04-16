---
name: adr
description: Use when making architectural decisions, choosing between frameworks/libraries/databases, deciding on data models, or recording any decision that would be expensive to reverse. Do NOT use for code documentation (comments belong in code), daily notes (use obsidian-note), or TIL (use til).
---

# Architecture Decision Records (ADR)

결정의 **이유**를 기록. 코드는 *무엇*을 했는지 보여주지만 ADR은 *왜 그렇게 했는지*와 *어떤 대안을 버렸는지*를 보존한다. 이 맥락은 미래의 엔지니어와 에이전트가 재논쟁하지 않도록 한다.

## Quick Start

- **ADR 써야 할까?** → [When to Write](#when-to-write) below
- **템플릿은?** → [ADR Template](#adr-template) below
- **라이프사이클?** → [ADR Lifecycle](#adr-lifecycle) below
- **어디에 저장?** → [Storage & Numbering](#storage--numbering) below

## CRITICAL Rules

1. **ALWAYS record Context, Decision, Alternatives, Consequences** — 4가지 모두 필수. 하나라도 빠지면 ADR이 아니라 메모.
2. **NEVER delete old ADRs** — 결정이 바뀌면 새 ADR을 작성해 이전 ADR을 `Superseded by ADR-NNN`으로 표시. 과거 맥락을 삭제하지 말 것.
3. **ALWAYS list alternatives considered** — "왜 이걸 **안** 골랐는가"가 "왜 이걸 골랐는가"만큼 중요.
4. **NEVER write ADR for trivial decisions** — "함수 이름을 camelCase로 한다" 같은 건 ADR 아님. **되돌리기 비싼** 결정에만.
5. **ALWAYS date the ADR** — 결정 시점의 제약·맥락이 시간에 따라 바뀐다.
6. **PREFER short ADRs** — 1~2페이지. 장황한 ADR은 읽히지 않는다.

## When to Write

### ADR을 작성해야 할 때

- 프레임워크·라이브러리·주요 의존성 선택 (React vs Vue, Prisma vs TypeORM)
- 데이터 모델이나 DB 스키마 설계
- 인증 전략 선택 (JWT vs Session, OAuth 제공자 선택)
- API 아키텍처 결정 (REST vs GraphQL vs tRPC)
- 빌드 도구·호스팅 플랫폼·인프라 선택
- **되돌리기 비싼 결정**이라면 무엇이든

### ADR을 작성하지 말아야 할 때

- 변수명·함수명 같은 일상 코딩 결정
- 쉽게 되돌릴 수 있는 수정
- 이미 코드에서 명확한 "무엇" 설명 — 그건 주석의 영역
- 프로토타입의 일회성 결정

## ADR Template

`docs/decisions/ADR-NNN-짧은-제목.md`:

```markdown
# ADR-001: Primary DB로 PostgreSQL 사용

## Status
Accepted | Superseded by ADR-NNN | Deprecated

## Date
2026-04-16

## Context
태스크 관리 애플리케이션의 primary DB가 필요하다. 주요 요구사항:
- 관계형 데이터 모델 (users, tasks, teams 관계)
- 태스크 상태 변경을 위한 ACID 트랜잭션
- 태스크 내용에 대한 full-text search
- 관리형 호스팅 (소규모 팀, 운영 역량 제한)

## Decision
PostgreSQL + Prisma ORM 사용.

## Alternatives Considered

### MongoDB
- **Pros:** 유연한 스키마, 시작 용이
- **Cons:** 우리 데이터는 본질적으로 관계형. 관계를 수동 관리해야 함
- **Rejected:** 문서 저장소의 관계형 데이터는 복잡한 join 또는 데이터 중복을 초래

### SQLite
- **Pros:** 설정 없음, 임베디드, 읽기 빠름
- **Cons:** 동시 쓰기 제한, 프로덕션 관리형 호스팅 없음
- **Rejected:** 멀티유저 웹 프로덕션에 부적합

### MySQL
- **Pros:** 성숙하고 널리 지원
- **Cons:** PostgreSQL이 JSON·full-text search·ecosystem 툴링에서 우위
- **Rejected:** 우리 기능 요구에 PostgreSQL이 더 적합

## Consequences

### Positive
- Prisma가 타입 안전 DB 접근 + migration 제공
- PostgreSQL의 full-text search로 Elasticsearch 추가 회피
- 관리형 서비스 (Supabase, Neon, RDS)에서 호스팅 가능

### Negative
- 팀이 PostgreSQL 지식 필요 (표준 스킬이라 리스크 낮음)
- Prisma 학습 곡선 (MongoDB 쓴 경험과 다름)

### Neutral
- 마이그레이션이 버전 관리됨 — 롤백 전략 필요
```

## ADR Lifecycle

```
PROPOSED → ACCEPTED → (SUPERSEDED | DEPRECATED)
```

| Status | 의미 |
|---|---|
| **Proposed** | 검토 중, 아직 결정 안 됨 |
| **Accepted** | 결정됨, 구현됨 |
| **Superseded** | 새 ADR이 이 결정을 대체 — 본문에 `Superseded by ADR-NNN` 명시 |
| **Deprecated** | 더 이상 유효하지 않지만 대체가 없음 — 역사적 참조용 |

### 결정이 바뀔 때

ADR-007이 ADR-001을 대체한다면:

1. 새 ADR-007을 쓴다 (Context에 "ADR-001을 대체하는 이유" 포함)
2. ADR-001의 Status를 `Superseded by ADR-007`로 업데이트
3. **ADR-001을 삭제하지 않는다** — 과거 맥락을 보존

> "왜 이렇게 했지?"를 3년 뒤 누군가 물을 때, 원본 ADR의 Context가 답이다.

## Storage & Numbering

- 위치: `docs/decisions/` 또는 `docs/adr/` (프로젝트 관습 따름)
- 네이밍: `ADR-NNN-kebab-case-title.md` (예: `ADR-003-use-postgres.md`)
- 순차 번호 — 절대 재사용 금지
- 새 리포 만들 때 `docs/decisions/README.md`에 ADR 목록 유지 (선택)

## Agent-Specific Notes

AI 에이전트가 코드베이스에서 작업할 때 ADR은 특히 가치가 크다:

- 에이전트가 **이미 결정된 것을 재논쟁**하지 않도록 함
- CLAUDE.md에서 `docs/decisions/`를 읽으라고 지시 가능
- 새 기능 구현 전 관련 ADR 확인으로 일관성 유지

## Common Rationalizations

| 변명 | 반박 |
|---|---|
| "코드가 스스로 문서화된다" | 코드는 **무엇**을 보여준다. **왜** 그렇게 했는지, 어떤 대안을 버렸는지, 어떤 제약이 있었는지는 안 보여준다. |
| "API가 안정화되면 문서화할게요" | API는 문서화할 때 더 빨리 안정화된다. 문서는 설계의 첫 테스트다. |
| "아무도 문서 안 읽어요" | 에이전트는 읽는다. 미래 엔지니어도 읽는다. **3개월 뒤의 당신**도 읽는다. |
| "ADR은 오버헤드예요" | 10분짜리 ADR이 6개월 뒤 같은 결정에 대한 2시간 논쟁을 예방한다. |
| "되돌리면 되잖아요" | 되돌릴 수 있으면 ADR이 필요 없다. 되돌리기 어렵기 때문에 기록한다. |

## Red Flags

- 서면 근거 없는 아키텍처 결정
- 중요 아키텍처 선택이 있는데 ADR이 없는 프로젝트
- "팀이 결정했다"만 있고 이유가 없는 ADR
- Alternatives Considered 섹션이 없는 ADR
- 삭제된 옛 ADR (git 히스토리에만 존재)
- 1년 넘게 `Proposed` 상태로 방치된 ADR

## Verification

ADR 작성 후:

- [ ] Status, Date 명시
- [ ] Context에 제약·요구사항 구체적으로 기록
- [ ] Decision이 한 문장으로 명확히 표현됨
- [ ] 최소 2~3개의 Alternatives Considered 포함
- [ ] 각 대안에 Pros/Cons/Rejected reason
- [ ] Consequences에 Positive·Negative·Neutral 구분
- [ ] 파일명이 `ADR-NNN-kebab-title.md` 형식
- [ ] 관련 ADR 상호 참조 (있을 경우)

## Cross-References

| Topic | Skill |
|---|---|
| 개인 지식 노트 | `obsidian-note` |
| TIL (일일 학습) | `til` |
| 프로젝트 작업 로그 | `devlog` |
| 세션 맥락 전달 | `session-handoff` |
| 코드 리뷰 | `code-review` |

## References

- [Michael Nygard — Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — 원조 ADR 글
- [ThoughtWorks Technology Radar — Lightweight ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
- [adr-tools](https://github.com/npryce/adr-tools) — CLI 도구
- [MADR — Markdown Architecture Decision Records](https://adr.github.io/madr/) — 표준화 노력
