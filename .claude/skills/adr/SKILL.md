---
name: adr
description: Use when making architectural decisions, choosing between frameworks/libraries/databases, deciding on data models, or recording any decision that would be expensive to reverse. Do NOT use for code documentation (comments belong in code), daily notes (use obsidian-note), or TIL (use til).
---

# Architecture Decision Records (ADR)

중요한 선택의 이유·제약·대안을 기록한다. 기존 ADR과 프로젝트 양식을 먼저 확인하고, 조사·설계안은 합의 전까지 `Proposed`로 표시한다.

## 저장 규칙

- 프로젝트 관습을 따른다. 정해진 위치가 없으면 `docs/decisions/ADR-NNN-kebab-case-title.md`를 사용한다.
- 기존 번호를 확인해 다음 번호를 선택한다. 번호를 재사용하지 않는다.
- 결정이 바뀌면 새 ADR에 이전 결정을 대체하는 이유를 적고 상호 링크한다. 이전 ADR은 삭제하지 않는다.
- 요청이 리뷰·초안이면 그 범위까지 작성한다. 문서 작성 자체를 구현이나 승인 완료로 간주하지 않는다.

## 작성 형식

각 항목은 실제 확인한 내용으로 채운다. 검토하지 않은 대안이나 합의를 만들어 넣지 않는다.

```markdown
# ADR-NNN: 결정 제목

## Status
Proposed

## Date
YYYY-MM-DD

## Context
문제, 요구사항, 제약, 확인한 근거

## Decision
선택 또는 제안과 적용 범위

## Alternatives Considered
실제로 검토한 대안과 채택하지 않은 이유

## Consequences
기대 효과, 비용, 위험, 운영 영향, 남은 확인 사항
```

## 상태

| 상태 | 의미 |
|---|---|
| `Proposed` | 검토 중 |
| `Accepted` | 결정이 승인됨. 구현·배포 상태는 별도로 기록 |
| `Superseded by ADR-NNN` | 다른 결정으로 대체됨 |
| `Deprecated` | 더 이상 적용되지 않으며 대체 결정은 없음 |

## 확인

- 결정과 근거가 연결되는지, 날짜·상태·적용 범위가 명확한지 확인한다.
- 대체 ADR이 있으면 양쪽 링크와 상태가 일치해야 한다.
- 재논의할 조건이나 미확인 제약이 있으면 남긴다. 일반 기술 소개와 긴 가상 사례는 생략한다.
