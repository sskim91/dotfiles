---
name: api-design
description: Use when designing API endpoints, reviewing API contracts, adding pagination/filtering, or planning versioning strategy. Do NOT use for API consumption, client-side HTTP, or GraphQL.
---

# API Design Patterns

이 프로젝트들의 API 컨벤션(선택)과 리뷰 기준만 담는다. REST 일반 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **ALWAYS** plural nouns, kebab-case, no verbs — `/team-members/:id` (예외: actions `/orders/:id/cancel`)
2. **ALWAYS** semantic status codes — 200 for everything 금지, created는 `201 + Location`
3. **ALWAYS** pagination for list endpoints — unbounded list 금지. **Public API는 cursor 기본**
4. **NEVER** expose internal details in errors — stack trace, SQL 쿼리 금지
5. **ALWAYS** validate at boundaries — 외부 입력·**써드파티 응답**·env/config 로딩은 검증, 이미 검증된 내부 데이터는 재검증 금지
6. **ALWAYS** rate limiting — 내부 API 포함
7. 버저닝: URL path (`/api/v1/`) 방식. breaking change 없이는 새 버전 만들지 않음

## Response Envelope (컨벤션)

```json
// Success:    { "data": {...} }  /  { "data": [...], "meta": { "has_next": true, "next_cursor": "..." } }
// Error:      { "error": { "code": "validation_error", "message": "...", "details": [...] } }
```

- `code`: machine-readable snake_case / `message`: human-readable / `details`: field-level errors
- Public API는 envelope 필수, internal API는 flat 허용

## Common Rationalizations

코드 리뷰에서 자주 나오는 변명과 반박. 나 자신의 설계 리뷰에도 적용하라.

| 변명 | 반박 |
|---|---|
| "나중에 문서화할게요" | **타입이 곧 문서**다. DTO/스키마를 먼저 정의하면 OpenAPI가 자동 생성된다. |
| "지금은 pagination 필요 없어요" | 100개 넘는 순간 필요해진다. 레거시 엔드포인트에 pagination 추가하는 게 3배 힘들다. |
| "버저닝은 필요해질 때 하죠" | versioning 없는 breaking change = 소비자 파괴. `v1/` 프리픽스만 먼저 박아도 비용이 거의 없다. |
| "아무도 그 미문서화된 동작 안 써요" | Hyrum's Law. 관찰 가능한 건 누군가 의존한다. |
| "Controller에서 Entity 바로 반환해도 돼요" (Spring) | Entity 노출 = 내부 구조 유출 + JPA proxy 직렬화 시 `LazyInitializationException`. DTO 분리는 협상 불가. |
| "내부용이라 rate limiting 안 해도 돼요" | 내부 배치 작업이 prod DB 터뜨리는 사례가 가장 흔하다. |
| "프론트가 검증하니 서버는 생략해도 돼요" | 프론트 검증은 UX, 서버 검증은 **보안**. curl 한 번이면 프론트 우회. |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ 인증 실패에 404 반환 → 403 (authenticated) / 401 (not authenticated)
- ❌ validation 에러에 500 → 400 (malformed) / 422 (valid JSON, invalid data)
- ❌ 써드파티 응답을 무검증 사용 → 사용자 입력과 동일하게 스키마 검증 (Pydantic / Zod / `@Valid`)

## Cross-References

| Topic | Skill |
|-------|-------|
| Spring Boot REST controller, exception handling | `springboot-patterns` |
| SQL 페이지네이션 최적화 | `sql-optimization-patterns` |
| REST/GraphQL·auth 방식 등 아키텍처 결정 기록 | `adr` |
