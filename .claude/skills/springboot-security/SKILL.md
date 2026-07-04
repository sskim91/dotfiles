---
name: springboot-security
description: Use when configuring Spring Security, implementing JWT/OAuth2 auth, adding role-based access control, or hardening Spring Boot APIs. Do NOT use for general patterns (use springboot-patterns), JPA (use jpa-patterns), or testing (use springboot-tdd).
paths: "**/*.java, **/build.gradle*, **/pom.xml, **/application*.yml, **/application*.properties"
---

# Spring Boot Security Patterns

버전 경계(Security 6 → 7)와 판단 규칙만 담는다. Spring Security 일반 구현 지식은 모델에 이미 있음.

**버전 컨텍스트**: Spring Security 7 (Boot 4 기반) — **lambda DSL 전용**. 학습 데이터에 흔한 구버전 관용구를 쓰지 말 것 (아래 migration 표).

## CRITICAL Rules

1. **Deny by default** — 명시적으로 허용한 경로만 접근 가능
2. **Never store plaintext passwords** — BCrypt(12+) 또는 Argon2 사용
3. **Never hardcode secrets** — `${ENV_VAR}` 또는 Vault
4. **Never trust X-Forwarded-For directly** — ForwardedHeaderFilter + trusted proxy 설정 필수 (rate limiting의 `getRemoteAddr()`도 동일)
5. **Never log tokens, passwords, PII** — 구조화된 로깅에서 민감 필드 제외
6. **PREFER** OAuth2 Resource Server (`oauth2ResourceServer().jwt()`) over custom JWT filter — 외부 IdP든 자체 발급이든 검증엔 공식 권장 방식. 커스텀 `OncePerRequestFilter`는 자체 토큰 **발급**까지 해야 할 때만

## Security 7 / Boot 4 Migration

Security 6에서 deprecated였던 API가 SS7에서 **제거됨**. 컴파일 에러 나는 지점:

| 제거됨 (SS6 deprecated → SS7 removed) | 대체 |
|--------------------------------------|------|
| 비-lambda chained DSL `.and()` | lambda DSL (`http.csrf(c -> ...)` 형태) |
| `authorizeRequests()` | `authorizeHttpRequests()` |
| custom DSL의 `HttpSecurity#apply(...)` | `.with(...)` |
| `@EnableGlobalMethodSecurity` | `@EnableMethodSecurity` |
| `antMatchers()` / `mvcMatchers()` | `requestMatchers()` |

## CSRF Strategy

| App Type | CSRF | Reason |
|----------|------|--------|
| Stateless API (JWT/Bearer) | Disable | Token itself prevents CSRF |
| Session-based web app | Enable | Browser auto-sends cookies |
| Mixed (API + web) | Enable for web paths | Selective protection |

## Security Checklist

- [ ] Auth tokens validated with expiry and signature
- [ ] Authorization guards on every sensitive endpoint
- [ ] All user inputs validated (@Valid + DTO constraints)
- [ ] No string-concatenated SQL
- [ ] CSRF posture matches app type (stateless vs session)
- [ ] Secrets externalized, none in source
- [ ] Security headers configured (CSP, X-Frame-Options)
- [ ] CORS restricted to known origins (`*` 금지, `allowCredentials(true)`면 specific origin 필수)
- [ ] Rate limiting on public/expensive endpoints
- [ ] Dependencies scanned for CVEs (OWASP/Snyk)
- [ ] No secrets, tokens, PII in logs
- [ ] HTTPS enforced in production

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `authorizeRequests()`, `antMatchers()`, `.and()` 생성 (SS7에서 제거됨) → migration 표 참조
- ❌ `permitAll()`을 넓은 매처 뒤에 선언 → 순서 중요, 구체적 매칭 먼저
- ❌ `@PreAuthorize`에서 하드코딩된 role 문자열 → 상수 또는 enum 사용
- ❌ JWT 비밀키를 application.yml에 직접 작성 → 환경변수 필수
- ❌ 커스텀 JWT 필터부터 작성 → OAuth2 Resource Server가 기본 선택지

## References

- [Spring Security Reference](https://docs.spring.io/spring-security/reference/) — Official documentation
- [OAuth2 Resource Server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/) — JWT validation
