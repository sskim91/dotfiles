---
name: springboot-patterns
description: Use when building Spring Boot services, configuring profiles, implementing caching/async, setting up Actuator/Micrometer, or creating REST clients. Do NOT use for JPA (use jpa-patterns), API design (use api-design), security (use springboot-security), testing (use springboot-tdd), or Kotlin (use kotlin-patterns).
paths: "**/*.java, **/build.gradle*, **/pom.xml, **/application*.yml, **/application*.properties"
---

# Spring Boot Core Patterns

Spring Boot 3.x/4.x 핵심 패턴. JPA, API 설계, 보안, 테스트는 전용 스킬 참조.

## Quick Start

- **설정/프로파일?** → [Configuration & Profiles reference](references/configuration-profiles.md)
- **캐싱/비동기/이벤트/스케줄링?** → [Caching, Async & Events reference](references/caching-async-events.md)
- **로깅/메트릭/HTTP 클라이언트?** → [Observability & HTTP Clients reference](references/observability-http-clients.md)
- **예외 처리/Validation?** → [Error Handling](#error-handling) below
- **프로젝트 구조?** → [Project Structure](#project-structure) below

## When to Activate

- Spring Boot 서비스 구축 및 구조 설계
- @ConfigurationProperties, Profile 관리
- @ControllerAdvice 예외 처리, Bean Validation
- @Cacheable, @Async, @EventListener 구현
- Actuator, Micrometer 모니터링 설정
- RestClient, HTTP Interface (Spring Boot 3.2+) 사용

## CRITICAL Rules

1. **ALWAYS** constructor injection — field injection 금지 (테스트 불가, 의존성 숨김)
2. **ALWAYS** `spring.mvc.problemdetails.enabled=true` — RFC 7807 표준 에러 응답
3. **NEVER** return entity directly from controller — DTO 분리 필수
4. **ALWAYS** externalize secrets — `${ENV_VAR}` 또는 Vault, 절대 하드코딩 금지
5. **PREFER** record for DTOs and @ConfigurationProperties
6. **ALWAYS** graceful shutdown — `server.shutdown=graceful`
7. **NEVER** catch generic Exception silently — 로그 + 적절한 HTTP 상태 반환
8. **ALWAYS** `spring.main.keep-alive=true` when virtual threads enabled — daemon thread로 JVM 조기 종료 방지

## Project Structure

```
src/main/java/com/example/
├── config/              # @Configuration, @ConfigurationProperties
├── controller/          # @RestController (thin, delegation only)
├── service/             # @Service (business logic, transactions)
├── repository/          # Spring Data interfaces
├── domain/              # Entity, VO, enums
├── dto/                 # Request/Response records
├── exception/           # Custom exceptions + @ControllerAdvice
├── filter/              # OncePerRequestFilter
└── event/               # ApplicationEvent + @EventListener
```

**Rules:**
- Controller는 얇게 — 검증 + 위임 + 응답 변환만
- Service에 비즈니스 로직 집중
- Entity ↔ DTO 변환은 DTO에 `static from()` 팩토리

## Error Handling

### ProblemDetail (RFC 9457 / RFC 7807)

```java
@ControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    ProblemDetail handleNotFound(EntityNotFoundException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Resource Not Found");
        pd.setProperty("timestamp", Instant.now());
        return pd;
    }

    @ExceptionHandler(BusinessException.class)
    ProblemDetail handleBusiness(BusinessException ex) {
        return ProblemDetail.forStatusAndDetail(
            HttpStatus.UNPROCESSABLE_ENTITY, ex.getMessage());
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex, HttpHeaders headers,
            HttpStatusCode status, WebRequest request) {
        ProblemDetail pd = ProblemDetail.forStatus(status);
        pd.setTitle("Validation Failed");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(e -> Map.of("field", e.getField(), "message", e.getDefaultMessage()))
            .toList());
        return ResponseEntity.status(status).body(pd);
    }
}
```

Enable: `spring.mvc.problemdetails.enabled=true`

### Custom Validation

```java
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = FutureBusinessDayValidator.class)
public @interface FutureBusinessDay {
    String message() default "Must be a future business day";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class FutureBusinessDayValidator
        implements ConstraintValidator<FutureBusinessDay, LocalDate> {
    @Override
    public boolean isValid(LocalDate value, ConstraintValidatorContext ctx) {
        if (value == null) return true; // @NotNull handles null
        return value.isAfter(LocalDate.now())
            && value.getDayOfWeek().getValue() <= 5;
    }
}
```

### DTO with Validation (Record)

```java
public record CreateOrderRequest(
    @NotBlank @Size(max = 200) String name,
    @NotNull @Positive BigDecimal amount,
    @NotNull @FutureBusinessDay LocalDate dueDate,
    @NotEmpty List<@NotBlank String> items) {}
```

## Production Defaults

```yaml
# application-prod.yml
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
  tomcat:
    max-threads: 200
    accept-count: 100
    connection-timeout: 5s
```

## Cross-References

| Topic | Skill |
|-------|-------|
| JPA/Hibernate, Spring Data | `jpa-patterns` |
| REST API design principles | `api-design` |
| Virtual Threads, Records, Sealed Types | `java-modern-patterns` |
| Spring Security | `springboot-security` |
| TDD, MockMvc, JUnit 5 | `springboot-tdd` |
| PR/deploy verification | `springboot-verification` |
| Kotlin + Spring Boot | `kotlin-patterns` |
| SQL query optimization | `sql-optimization-patterns` |

## Verification

코드 작성 후 반드시 실행:
```bash
./gradlew build                  # 컴파일 + 테스트
./gradlew bootRun                # 로컬 실행 확인 (선택)
```

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@Autowired` 필드 주입 사용 → 생성자 주입 필수
- ❌ application.yml에 민감 정보 하드코딩 → 환경변수 또는 Vault
- ❌ `@RestController`에서 엔티티 직접 반환 → DTO로 변환 필수
- ❌ `@Configuration` 클래스에 비즈니스 로직 → 설정만 담을 것
