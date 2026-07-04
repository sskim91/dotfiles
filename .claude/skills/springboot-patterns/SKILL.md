---
name: springboot-patterns
description: Use when building Spring Boot services, configuring profiles, implementing caching/async, setting up Actuator/Micrometer, or creating REST clients. Do NOT use for JPA (use jpa-patterns), API design (use api-design), security (use springboot-security), testing (use springboot-tdd).
paths: "**/*.java, **/build.gradle*, **/pom.xml, **/application*.yml, **/application*.properties"
---

# Spring Boot Core Patterns

버전 경계와 프로덕션 기본값만 담는다. Spring Boot 일반 지식은 모델에 이미 있음.

**버전 컨텍스트**: Spring Boot 4 (현재 GA — Spring Framework 7 기반, Java 17+ / Jakarta EE 11). Boot 3.x는 legacy이나 prod에서 여전히 흔함 (3.5 = 마지막 3.x, Framework 6.2 기반). **코드 생성 전 프로젝트의 Boot 버전을 먼저 확인하라.**

## CRITICAL Rules

1. **ALWAYS** constructor injection — field injection 금지 (테스트 불가, 의존성 숨김)
2. **ALWAYS** `spring.mvc.problemdetails.enabled=true` — RFC 9457 표준 에러 응답 (ProblemDetail)
3. **NEVER** return entity directly from controller — DTO 분리 필수
4. **ALWAYS** externalize secrets — `${ENV_VAR}` 또는 Vault, 절대 하드코딩 금지
5. **PREFER** record for DTOs and @ConfigurationProperties
6. **ALWAYS** graceful shutdown — `server.shutdown=graceful`
7. **NEVER** catch generic Exception silently — 로그 + 적절한 HTTP 상태 반환
8. **ALWAYS** `spring.main.keep-alive=true` when virtual threads enabled — daemon thread로 JVM 조기 종료 방지

## Production Defaults

```yaml
spring:
  mvc:
    problemdetails:
      enabled: true
  jackson:
    default-property-inclusion: non_null
    deserialization:
      fail-on-unknown-properties: false
  lifecycle:
    timeout-per-shutdown-phase: 30s

server:
  shutdown: graceful
```

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@Autowired` 필드 주입 사용 → 생성자 주입 필수
- ❌ application.yml에 민감 정보 하드코딩 → 환경변수 또는 Vault
- ❌ `@Configuration` 클래스에 비즈니스 로직 → 설정만 담을 것
- ❌ virtual threads 켜고 `spring.main.keep-alive` 누락 → 이벤트 없는 앱이 조용히 종료됨
- ❌ HTTP 클라이언트로 RestTemplate 신규 작성 → `RestClient` 또는 HTTP Interface (Boot 3.2+)
- ❌ 구조화(JSON) 로깅에 `logstash-logback-encoder` 의존성 추가 → Boot 3.4+는 내장: `logging.structured.format.console=ecs|logstash|gelf` 한 줄이면 됨

## Cross-References

| Topic | Skill |
|-------|-------|
| JPA/Hibernate, Spring Data | `jpa-patterns` |
| REST API design principles | `api-design` |
| Virtual Threads, Records, Sealed Types | `java-modern-patterns` |
| Spring Security | `springboot-security` |
| TDD, MockMvc, JUnit 5 | `springboot-tdd` |
| PR/deploy verification | `springboot-verification` |
| SQL query optimization | `sql-optimization-patterns` |
