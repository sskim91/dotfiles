---
name: api-design
description: Use when designing API endpoints, reviewing API contracts, adding pagination/filtering, or planning versioning strategy. Do NOT use for API consumption, client-side HTTP, or GraphQL.
---

# API Design Patterns

REST API 리뷰 기준과 새 API에 사용할 개인 기본값을 담는다. 기존 프로젝트의 계약·스키마·ADR·명시적 요구사항이 우선한다. 리뷰 요청만 받았다면 계약을 변경하지 않는다.

## 계약 확인

- 소비자, 공개 범위, 기존 endpoint·응답·오류 형식, 호환성 요구를 먼저 확인한다.
- 아래 기본값과 기존 계약이 다르면 차이를 설명한다. 개인 컨벤션에 맞추기 위한 일괄 변경은 하지 않는다.
- 계약 변경안에는 영향을 받는 소비자와 migration 방법을 함께 적는다.

## 리뷰 기준

- 외부 입력과 신뢰 경계에서 데이터를 검증한다. 내부 데이터 재검증 여부는 경계와 변경 가능성에 따라 판단한다.
- 오류에 stack trace, SQL, 비밀값 등 내부 구현을 노출하지 않는다.
- 목록 API의 최대 반환량과 정렬 기준을 명확히 한다. pagination 방식은 접근 패턴·호환성에 맞춘다.
- 인증·권한 오류와 입력 오류를 구분하고, 상태 코드와 응답 스키마를 일관되게 적용한다.
- 요청량 제한은 공개 범위·호출자·운영 요구에 맞춰 설계한다.

## 새 API의 기본값

프로젝트 규칙이 없고 새 계약을 설계할 때 사용하는 선택이다.

| 항목 | 기본값 |
|---|---|
| 경로 | 복수 명사와 kebab-case: `/team-members/:id`. 행위 endpoint는 `/orders/:id/cancel`처럼 표현 |
| 버전 | URL path `/api/v1/`. 호환성을 깨지 않는 변경에는 새 버전을 만들지 않음 |
| 목록 | 공개 API는 cursor pagination 우선. 정렬의 안정성과 동률 처리도 명시 |
| 성공 응답 | 공개 API는 아래 envelope. 내부 API는 flat 응답도 허용 |
| 오류 | machine-readable `code`, 사용자용 `message`, 필드별 `details` |
| 모델 경계 | 저장 모델과 외부 계약을 분리해 내부 필드나 ORM 상태가 응답에 섞이지 않게 함 |

```json
{
  "data": [],
  "meta": { "has_next": false, "next_cursor": null }
}
```

단건은 `{ "data": { ... } }`, 오류는 `{ "error": { "code": "validation_error", "message": "...", "details": [] } }`를 기본으로 한다.

## 관련 작업

- SQL pagination 성능 분석: `sql-optimization-patterns`
- 응답 형식·버저닝 등 선택의 이유 기록: `adr`
