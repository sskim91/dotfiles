---
name: springboot-tdd
description: Use when writing tests, adding features TDD-style, or setting up test infrastructure for Spring Boot. Do NOT use for JPA/Testcontainers testing (use jpa-patterns), general TDD (use superpowers test-driven-development), or verification (use springboot-verification).
paths: "**/*.java, **/build.gradle*, **/pom.xml"
---

# Spring Boot TDD Workflow

버전 경계와 실수 잦은 지점만 담는다. MockMvc/Mockito/AssertJ 일반 지식은 모델에 이미 있음. JPA/Testcontainers 테스트는 `jpa-patterns` 참조.

## CRITICAL Rules

1. **Use `@MockitoBean` / `@MockitoSpyBean`** — Boot 4에서 `@MockBean`/`@SpyBean`은 **제거됨** (3.4 deprecated → 4.0 removal). 학습 데이터엔 구버전이 압도적이니 주의. import 경로: `org.springframework.test.context.bean.override.mockito.*`
2. **NEVER `@Transactional` on `@SpringBootTest`** — 실제 트랜잭션 동작을 왜곡, 테스트에서만 통과하는 코드 발생. `@BeforeEach`에서 데이터 정리로 격리
3. **Test behavior, not implementation** — 내부 구현이 아닌 입출력/부수효과 검증
4. **Fast unit tests, slow integration tests** — 단위 테스트는 DB/네트워크 없이
5. **PREFER `@ServiceConnection`** (Boot 3.1+) — Testcontainers 연결 시 `@DynamicPropertySource` 보일러플레이트 제거
6. **Context reuse** — 통합 테스트는 abstract base class로 ApplicationContext 공유 (테스트마다 새 컨텍스트 = 최악의 속도 저하)

## Test Slice Guide

| What to Test | Annotation | Loads | Speed |
|-------------|-----------|-------|-------|
| Service logic | `@ExtendWith(MockitoExtension.class)` | Nothing | Fast |
| Controller + validation | `@WebMvcTest(Controller.class)` | Web layer | Medium |
| Security rules | `@WebMvcTest` + `@Import(SecurityConfig.class)` + `@WithMockUser` | Web + Security | Medium |
| JSON serialization | `@JsonTest` | Jackson only | Fast |
| REST clients | `@RestClientTest` | RestClient | Medium |
| JPA repository | `@DataJpaTest` | **→ jpa-patterns** | Medium |
| Full stack | `@SpringBootTest` | Everything | Slow |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@MockBean`/`@SpyBean` 사용 (Boot 4에서 제거됨) → `@MockitoBean`/`@MockitoSpyBean`
- ❌ `@SpringBootTest`에 `@Transactional` 추가 → 테스트 간 격리 문제 + 실제 동작 왜곡
- ❌ `@WebMvcTest`로 security 테스트 시 `@Import(SecurityConfig.class)` 누락 → 기본 설정으로 테스트되어 false pass
- ❌ MockMvc에서 한글 응답 깨짐 → `.accept(MediaType.APPLICATION_JSON)` 설정
- ❌ 테스트마다 새 ApplicationContext 로딩 → Base 클래스로 context 재사용

## Cross-References

| Topic | Skill |
|-------|-------|
| @DataJpaTest, Testcontainers, Repository testing | `jpa-patterns` |
| TDD methodology (Red-Green-Refactor general) | `test-driven-development` superpowers |
| Build + lint + security verification | `springboot-verification` |
| Security configuration being tested | `springboot-security` |

## References

- [Spring Boot Testing](https://docs.spring.io/spring-boot/reference/testing/) — Official guide
- [How I test production-ready Spring Boot applications](https://www.wimdeblauwe.com/blog/2025/07/30/how-i-test-production-ready-spring-boot-applications/) — Wim Deblauwe
