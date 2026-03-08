---
name: api-design
description: REST API design patterns for resource naming, status codes, pagination, filtering, error responses, versioning, and rate limiting. Use when designing new API endpoints, reviewing API contracts, adding pagination or filtering, or planning API versioning strategy. Do NOT use for simple API consumption, client-side HTTP calls, or GraphQL schema design.
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

## Cross-References

| Topic | Skill |
|-------|-------|
| Spring Boot REST controller, exception handling | `springboot-patterns` |
| 언어별 구현 예시 (TypeScript, Python, Go, Spring) | [references/implementation-examples.md](references/implementation-examples.md) |
| SQL 페이지네이션 최적화 | `sql-optimization-patterns` |

## References

- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines) -- Comprehensive guide
- [Google API Design Guide](https://cloud.google.com/apis/design) -- Resource-oriented design
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) -- Enterprise patterns
- [JSON:API Specification](https://jsonapi.org/) -- Standardized response format
- [RFC 7807: Problem Details](https://www.rfc-editor.org/rfc/rfc7807) -- Error response standard
