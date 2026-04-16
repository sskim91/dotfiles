---
name: api-design
description: Use when designing API endpoints, reviewing API contracts, adding pagination/filtering, or planning versioning strategy. Do NOT use for API consumption, client-side HTTP, or GraphQL.
---

# API Design Patterns

판단 기준과 규칙 중심. REST API 설계의 **올바른 결정**을 안내.

## Quick Start

- **엔드포인트 설계?** --> [Resource Design](#resource-design) below
- **상태 코드 선택?** --> [Status Code Decision](#status-code-decision) below
- **페이지네이션 전략?** --> [Pagination Decision](#pagination-decision) below
- **버저닝 전략?** --> [Versioning Decision](#versioning-decision) below
- **출시 전 점검?** --> [API Design Checklist](#api-design-checklist) below
- **언어별 구현 예시?** --> [references/implementation-examples.md](references/implementation-examples.md)

## CRITICAL Rules

1. **ALWAYS** plural nouns for resources -- `/users` NOT `/user`
2. **NEVER** verbs in URLs -- `/users/:id` NOT `/getUser/:id` (예외: actions `/orders/:id/cancel`)
3. **ALWAYS** kebab-case for multi-word URLs -- `/team-members` NOT `/team_members`
4. **ALWAYS** use HTTP status codes semantically -- 200 for everything 금지
5. **ALWAYS** `201 Created` + `Location` header for POST -- 리소스 URL 반환
6. **NEVER** expose internal details in errors -- stack trace, SQL 쿼리 금지
7. **ALWAYS** validate input with schema -- Zod, Pydantic, Bean Validation
8. **ALWAYS** pagination for list endpoints -- unbounded list 금지
9. **PREFER** cursor-based pagination for public APIs -- consistent performance
10. **ALWAYS** rate limiting -- Anonymous, Authenticated, Premium 티어 분리

## Resource Design

```
# Standard CRUD
GET    /api/v1/users              # List
GET    /api/v1/users/:id          # Get
POST   /api/v1/users              # Create
PUT    /api/v1/users/:id          # Full replace
PATCH  /api/v1/users/:id          # Partial update
DELETE /api/v1/users/:id          # Delete

# Sub-resources (ownership)
GET    /api/v1/users/:id/orders   # User's orders
POST   /api/v1/users/:id/orders   # Create user's order

# Actions (verbs, sparingly)
POST   /api/v1/orders/:id/cancel
POST   /api/v1/auth/login
```

### Method Semantics

| Method | Idempotent | Safe | Use For |
|--------|:---------:|:----:|---------|
| GET | Yes | Yes | Retrieve |
| POST | No | No | Create, trigger action |
| PUT | Yes | No | Full replacement |
| PATCH | No* | No | Partial update |
| DELETE | Yes | No | Remove |

## Status Code Decision

```
Request successful?
+-- Resource returned --> 200 OK
+-- Resource created --> 201 Created + Location header
+-- Accepted but processing later --> 202 Accepted
+-- No body to return --> 204 No Content

Client error?
+-- Malformed JSON/syntax --> 400 Bad Request
+-- Not authenticated --> 401 Unauthorized
+-- Authenticated but forbidden --> 403 Forbidden
+-- Resource not found --> 404 Not Found
+-- Duplicate/conflict --> 409 Conflict
+-- Valid JSON but invalid data --> 422 Unprocessable Entity
+-- Rate limit exceeded --> 429 Too Many Requests

Server error?
+-- Unexpected failure --> 500 (never expose details)
+-- Upstream failed --> 502 Bad Gateway
+-- Temporary overload --> 503 + Retry-After header
```

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| 200 + `{"success": false}` | Use proper HTTP status code |
| 500 for validation errors | 400 or 422 |
| 200 for created resource | 201 + Location |
| Stack trace in error response | Generic message + error code |
| 404 for authorization failure | 403 (authenticated) or 401 (not) |

## Response Format

### Standard Envelope

```json
// Success (single)
{ "data": { "id": "abc-123", "name": "Alice" } }

// Success (collection)
{ "data": [...], "meta": { "total": 142, "page": 1, "per_page": 20 } }

// Error
{ "error": { "code": "validation_error", "message": "...", "details": [...] } }
```

**Rule:** Public API는 envelope (`data` wrapper) 사용. Internal API는 flat response OK (status code로 구분).

### Error Response Rules

- `code`: machine-readable (snake_case) -- `not_found`, `validation_error`
- `message`: human-readable -- 사용자에게 보여줄 수 있는 메시지
- `details`: field-level errors (validation) -- `[{"field": "email", "message": "...", "code": "..."}]`

## Pagination Decision

| Use Case | Type | Why |
|----------|------|-----|
| Admin dashboard, <10K rows | Offset | "Jump to page N" 가능 |
| Infinite scroll, feeds, large data | Cursor | Position-independent performance |
| Public API | Cursor (default) | Stable with concurrent writes |
| Search results | Offset | Users expect page numbers |

### Cursor-Based Pattern

```json
{
  "data": [...],
  "meta": { "has_next": true, "next_cursor": "eyJpZCI6MTQzfQ" }
}
```

### Offset-Based Pattern

```json
{
  "data": [...],
  "meta": { "total": 142, "page": 1, "per_page": 20, "total_pages": 8 },
  "links": { "next": "/api/v1/users?page=2&per_page=20" }
}
```

## Filtering, Sorting, Search

```
# Filtering
GET /api/v1/orders?status=active&customer_id=abc-123
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/products?category=electronics,clothing

# Sorting (prefix - for DESC)
GET /api/v1/products?sort=-created_at,price

# Search
GET /api/v1/products?q=wireless+headphones

# Sparse fieldsets (reduce payload)
GET /api/v1/users?fields=id,name,email
```

## Versioning Decision

```
Need versioning?
+-- First API? --> Start with /api/v1/, don't version until needed
+-- Breaking change?
|    +-- Removing/renaming fields --> New version required
|    +-- Changing field types --> New version required
|    +-- Changing URL structure --> New version required
+-- Non-breaking change?
     +-- Adding new response fields --> No new version
     +-- Adding optional query params --> No new version
     +-- Adding new endpoints --> No new version
```

| Strategy | Pros | Cons | Recommendation |
|----------|------|------|---------------|
| URL path (`/v1/`) | Explicit, cacheable | URL changes | **Recommended** |
| Header (`Accept: vnd.app.v2+json`) | Clean URLs | Hidden, hard to test | Internal APIs |

**Deprecation process:**
1. Announce (6 months for public APIs)
2. Add `Sunset` header
3. Return `410 Gone` after sunset date
4. Maintain max 2 versions (current + previous)

## Security Boundaries

### Validation 위치 규칙

내부 코드는 타입 계약을 신뢰하고, **외부에서 들어오는 값만 검증**하라.

| 검증해야 할 위치 | 이유 |
|---|---|
| API route/controller handler (사용자 입력) | 외부 입력 = 신뢰 불가 |
| 폼 제출 핸들러 | 동일 |
| **외부 서비스 응답 파싱** | 써드파티도 신뢰 불가 |
| 환경변수/설정 로딩 | 설정 오류 조기 발견 |

| 검증하면 안 되는 위치 | 이유 |
|---|---|
| 이미 검증된 데이터를 받는 내부 함수 | 중복, 성능 손실 |
| DB에서 막 읽은 데이터 | 내 시스템이 썼으니 신뢰 |
| 유틸 함수 (검증된 호출자가 호출) | 동일 |

### 써드파티 응답 = 신뢰할 수 없는 입력

> 외부 API 응답은 사용자 입력과 동일하게 다뤄야 한다.

감염되거나 오동작하는 외부 서비스는 예상 밖 타입, 악의적 콘텐츠, 프롬프트 인젝션형 텍스트를 반환할 수 있다. 렌더링·비즈니스 로직·판단에 사용하기 **전에 형태와 내용을 모두 검증**하라.

- **Spring**: WebClient 응답 → DTO 매핑 + `@Valid` 또는 수동 검증
- **Python**: Pydantic으로 외부 응답도 파싱 (`httpx` response → `Model.model_validate`)
- **Node**: Zod `safeParse` 후 사용

## Rate Limiting

| Tier | Limit | Window | Headers |
|------|-------|--------|---------|
| Anonymous | 30/min | Per IP | `X-RateLimit-Limit`, `X-RateLimit-Remaining` |
| Authenticated | 100/min | Per user | + `X-RateLimit-Reset` |
| Premium | 1000/min | Per API key | Same |

When exceeded: `429 Too Many Requests` + `Retry-After` header.

## API Design Checklist

Before shipping:

- [ ] Resource URL: plural, kebab-case, no verbs
- [ ] Correct HTTP method (GET reads, POST creates, etc.)
- [ ] Semantic status codes (not 200 for everything)
- [ ] Input validated with schema
- [ ] Error responses: standard format with codes + messages
- [ ] Pagination on list endpoints (cursor or offset)
- [ ] Authentication required (or explicitly public)
- [ ] Authorization checked (ownership verification)
- [ ] Rate limiting configured
- [ ] No internal details leaked (stack traces, SQL)
- [ ] Consistent naming with existing endpoints
- [ ] OpenAPI/Swagger spec updated

## Common Rationalizations

코드 리뷰에서 자주 나오는 변명과 반박. 나 자신의 설계 리뷰에도 적용하라.

| 변명 | 반박 |
|---|---|
| "나중에 문서화할게요" | **타입이 곧 문서**다. DTO/스키마를 먼저 정의하면 OpenAPI가 자동 생성된다. |
| "지금은 pagination 필요 없어요" | 100개 넘는 순간 필요해진다. 레거시 엔드포인트에 pagination 추가하는 게 3배 힘들다. |
| "PATCH 복잡하니 PUT으로 통일하죠" | PUT은 매번 전체 객체를 요구한다. 클라이언트가 실제로 원하는 건 PATCH다. |
| "버저닝은 필요해질 때 하죠" | versioning 없는 breaking change = 소비자 파괴. `v1/` 프리픽스만 먼저 박아도 비용이 거의 없다. |
| "아무도 그 미문서화된 동작 안 써요" | Hyrum's Law. 관찰 가능한 건 누군가 의존한다. 테스트 커버리지와 무관. |
| "내부 API는 계약 필요 없어요" | 내부 소비자도 소비자. 계약 없이는 팀 간 병렬 작업 불가능. |
| **"Controller에서 Entity 바로 반환해도 돼요"** (Spring) | Entity 노출 = 내부 구조 유출 + Hyrum's Law. JPA proxy 직렬화 시 `LazyInitializationException`까지 터진다. DTO 분리는 협상 불가. |
| **"내부용이라 rate limiting 안 해도 돼요"** | 내부 배치 작업이 prod DB 터뜨리는 사례가 가장 흔하다. 같은 회사 다른 팀도 실수로 "공격자"가 된다. |
| **"프론트가 검증하니 서버는 생략해도 돼요"** | 프론트 검증은 UX, 서버 검증은 **보안**. curl 한 번이면 프론트 우회. 둘은 서로를 절대 대체할 수 없다. |

## Cross-References

| Topic | Skill |
|-------|-------|
| Spring Boot REST controller, exception handling | `springboot-patterns` |
| 언어별 구현 예시 (TypeScript, Python, Go, Spring) | [references/implementation-examples.md](references/implementation-examples.md) |
| SQL 페이지네이션 최적화 | `sql-optimization-patterns` |
| REST/GraphQL·auth 방식 등 아키텍처 결정 기록 | `adr` |

## References

- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines) -- Comprehensive guide
- [Google API Design Guide](https://cloud.google.com/apis/design) -- Resource-oriented design
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) -- Enterprise patterns
- [JSON:API Specification](https://jsonapi.org/) -- Standardized response format
- [RFC 7807: Problem Details](https://www.rfc-editor.org/rfc/rfc7807) -- Error response standard
