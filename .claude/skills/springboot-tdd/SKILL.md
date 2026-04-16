---
name: springboot-tdd
description: Use when writing tests, adding features TDD-style, or setting up test infrastructure for Spring Boot. Do NOT use for JPA/Testcontainers testing (use jpa-patterns), general TDD (use superpowers test-driven-development), or verification (use springboot-verification).
paths: "**/*.java, **/build.gradle*, **/pom.xml"
---

# Spring Boot TDD Workflow

Red-Green-Refactor for Spring Boot. JPA/Testcontainers 테스트는 `jpa-patterns` 스킬 참조.

## When to Activate

- Spring Boot 서비스에 새 기능 추가
- 버그 수정 시 regression test 작성
- Controller, Service 레이어 테스트
- Security 규칙 테스트 (@WithMockUser)
- 테스트 커버리지 설정 (JaCoCo)

## CRITICAL Rules

1. **Test behavior, not implementation** — 내부 구현이 아닌 입출력/부수효과 검증
2. **One assertion concept per test** — 하나의 테스트가 하나의 행위 검증
3. **No test interdependence** — 테스트 순서 무관하게 독립 실행
4. **AAA pattern** — Arrange-Act-Assert 구조 엄수
5. **Fast unit tests, slow integration tests** — 단위 테스트는 DB/네트워크 없이
6. **NEVER `@Transactional` on `@SpringBootTest`** — 실제 트랜잭션 동작을 왜곡, 테스트에서만 통과하는 코드 발생
7. **Use `@MockitoBean` not `@MockBean`** — Spring Framework 6.2+ / Boot 3.4+ (기존 `@MockBean`은 deprecated)

## TDD Cycle

```
1. RED    — Write failing test for desired behavior
2. GREEN  — Write minimal code to pass
3. REFACTOR — Clean up with tests green
4. REPEAT
```

## Test Slice Guide

| What to Test | Annotation | Loads | Speed |
|-------------|-----------|-------|-------|
| Service logic | `@ExtendWith(MockitoExtension.class)` | Nothing | Fast |
| Controller + validation | `@WebMvcTest(Controller.class)` | Web layer | Medium |
| Full stack | `@SpringBootTest` | Everything | Slow |
| Security rules | `@WebMvcTest` + `@WithMockUser` | Web + Security | Medium |
| JSON serialization | `@JsonTest` | Jackson only | Fast |
| REST clients | `@RestClientTest` | RestClient | Medium |
| JPA repository | `@DataJpaTest` | **→ jpa-patterns** | Medium |

## Service Unit Tests (Mockito)

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock OrderRepository orderRepo;
    @Mock PaymentClient paymentClient;
    @InjectMocks OrderService orderService;

    @Test
    void createOrder_validRequest_savesAndReturnsOrder() {
        // Arrange
        var request = new CreateOrderRequest("item", BigDecimal.TEN);
        when(orderRepo.save(any(Order.class)))
            .thenAnswer(inv -> {
                Order o = inv.getArgument(0);
                return new Order(1L, o.getName(), o.getAmount(), OrderStatus.CREATED);
            });

        // Act
        Order result = orderService.create(request);

        // Assert
        assertThat(result.getName()).isEqualTo("item");
        assertThat(result.getStatus()).isEqualTo(OrderStatus.CREATED);
        verify(orderRepo).save(any(Order.class));
        verifyNoInteractions(paymentClient);
    }

    @Test
    void createOrder_duplicateName_throwsException() {
        var request = new CreateOrderRequest("existing", BigDecimal.TEN);
        when(orderRepo.existsByName("existing")).thenReturn(true);

        assertThatThrownBy(() -> orderService.create(request))
            .isInstanceOf(DuplicateOrderException.class)
            .hasMessageContaining("existing");
    }
}
```

### Parametrized Tests

```java
@ParameterizedTest
@CsvSource({
    "100, STANDARD",
    "1000, PREMIUM",
    "10000, VIP"
})
void determinesTierByAmount(BigDecimal amount, OrderTier expected) {
    assertThat(orderService.determineTier(amount)).isEqualTo(expected);
}
```

## Controller Tests (@WebMvcTest)

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;

    @Test
    void createOrder_validInput_returns201() throws Exception {
        var order = new OrderDto(1L, "item", BigDecimal.TEN, "CREATED");
        when(orderService.create(any())).thenReturn(order);

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"name": "item", "amount": 10}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("item"))
            .andExpect(jsonPath("$.status").value("CREATED"));
    }

    @Test
    void createOrder_blankName_returns400() throws Exception {
        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"name": "", "amount": 10}
                    """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.title").value("Validation Failed"));
    }

    @Test
    void getOrder_notFound_returns404() throws Exception {
        when(orderService.getById(999L))
            .thenThrow(new EntityNotFoundException("Order 999"));

        mockMvc.perform(get("/api/orders/999"))
            .andExpect(status().isNotFound());
    }
}
```

## Security Layer Tests

```java
@WebMvcTest(AdminController.class)
@Import(SecurityConfig.class)
class AdminControllerSecurityTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean AdminService adminService;

    @Test
    void listUsers_unauthenticated_returns401() throws Exception {
        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "USER")
    void listUsers_nonAdmin_returns403() throws Exception {
        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void listUsers_admin_returns200() throws Exception {
        when(adminService.listUsers()).thenReturn(List.of());

        mockMvc.perform(get("/api/admin/users"))
            .andExpect(status().isOk());
    }
}
```

## JSON Serialization Tests (@JsonTest)

```java
@JsonTest
class OrderDtoJsonTest {

    @Autowired JacksonTester<OrderDto> json;

    @Test
    void serialize() throws Exception {
        var dto = new OrderDto(1L, "item", BigDecimal.TEN, "CREATED");
        assertThat(json.write(dto))
            .extractingJsonPathStringValue("@.name").isEqualTo("item");
    }

    @Test
    void deserialize() throws Exception {
        String content = """
            {"id": 1, "name": "item", "amount": 10, "status": "CREATED"}
            """;
        assertThat(json.parse(content)).isEqualTo(
            new OrderDto(1L, "item", BigDecimal.TEN, "CREATED"));
    }
}
```

## Integration Tests (@SpringBootTest)

### With @ServiceConnection (Spring Boot 3.1+)

`@DynamicPropertySource` 보일러플레이트를 제거하는 권장 방식:

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Testcontainers
class OrderIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");

    @Container
    @ServiceConnection
    static GenericContainer<?> redis =
        new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

    @Autowired MockMvc mockMvc; // requires @AutoConfigureMockMvc
```

> **JPA 테스트 상세** (Entity, Repository, Testcontainers 패턴)는 `jpa-patterns` 스킬 참조.

### Anti-pattern: @Transactional on @SpringBootTest

```java
// BAD: 테스트 트랜잭션이 실제 앱 트랜잭션 동작을 왜곡
@SpringBootTest
@Transactional  // 테스트 후 롤백되지만, 실제 앱에서는 트랜잭션이 없을 수 있음
class OrderTest { /* ... */ }

// GOOD: @BeforeEach에서 데이터 정리
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class OrderIntegrationTest {

    @Autowired OrderRepository orderRepo;

    @BeforeEach
    void cleanup() {
        orderRepo.deleteAll();
    }
```

### Basic Integration Test

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class OrderIntegrationTest {

    @Autowired MockMvc mockMvc;

    @Test
    void fullOrderWorkflow() throws Exception {
        // Create
        String response = mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"name": "integration-test", "amount": 100}
                    """))
            .andExpect(status().isCreated())
            .andReturn().getResponse().getContentAsString();

        Long orderId = JsonPath.parse(response).read("$.id", Long.class);

        // Read
        mockMvc.perform(get("/api/orders/{id}", orderId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("integration-test"));
    }
}
```

### Context Reuse (Base Class Pattern)

여러 통합 테스트가 같은 컨텍스트를 공유하면 실행 속도가 크게 향상된다:

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Testcontainers
abstract class BaseIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");
}

// 구체 테스트들은 base class 상속
class OrderIntegrationTest extends BaseIntegrationTest { /* ... */ }
class UserIntegrationTest extends BaseIntegrationTest { /* ... */ }
```

## Test Data Builders

```java
public class OrderFixture {
    public static CreateOrderRequest.Builder aCreateRequest() {
        return CreateOrderRequest.builder()
            .name("Test Order")
            .amount(BigDecimal.valueOf(100));
    }

    public static Order.Builder anOrder() {
        return Order.builder()
            .id(1L)
            .name("Test Order")
            .amount(BigDecimal.valueOf(100))
            .status(OrderStatus.CREATED);
    }
}

// Usage in tests
var request = OrderFixture.aCreateRequest().name("Custom").build();
var order = OrderFixture.anOrder().status(OrderStatus.COMPLETED).build();
```

## AssertJ Patterns

```java
// Collection
assertThat(orders)
    .hasSize(3)
    .extracting(Order::getStatus)
    .containsExactly(CREATED, PROCESSING, COMPLETED);

// Exception
assertThatThrownBy(() -> service.process(null))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessageContaining("must not be null");

// Soft assertions (report all failures at once)
SoftAssertions.assertSoftly(softly -> {
    softly.assertThat(order.getName()).isEqualTo("Test");
    softly.assertThat(order.getStatus()).isEqualTo(CREATED);
    softly.assertThat(order.getAmount()).isPositive();
});
```

## JaCoCo Coverage

```xml
<!-- pom.xml -->
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.14</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>verify</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>check</id>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

## CI Commands

```bash
# Maven
mvn -T 4 test                          # Run tests (parallel)
mvn verify                              # Tests + JaCoCo check
mvn jacoco:report                       # Generate HTML report

# Gradle
./gradlew test                          # Run tests
./gradlew jacocoTestReport              # Generate report
./gradlew jacocoTestCoverageVerification # Check thresholds
```

## Coverage Gap Analysis Template

기존 코드의 테스트 커버리지를 분석할 때 사용하는 출력 형식. JaCoCo 리포트와 함께 사용.

```markdown
## Test Coverage Analysis

### Current Coverage
- Tests: [X] tests covering [Y] classes/methods
- Line coverage: [Z]% (JaCoCo)
- Coverage gaps: [list of uncovered areas]

### Recommended Tests
1. **[TestClass#testMethod]** — [What it verifies, why it matters]
2. **[TestClass#testMethod]** — [What it verifies, why it matters]

### Priority
- Critical: [Tests that catch data loss or security issues]
- High: [Tests for core business logic]
- Medium: [Tests for edge cases and error handling]
- Low: [Tests for utility functions and formatting]
```

## Cross-References

| Topic | Skill |
|-------|-------|
| @DataJpaTest, Testcontainers, Repository testing | `jpa-patterns` |
| TDD methodology (Red-Green-Refactor general) | `test-driven-development` superpowers |
| Build + lint + security verification | `springboot-verification` |
| Security configuration being tested | `springboot-security` |
| 테스트 실패 triage, 근본 원인 분석, git bisect | `debugging` |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `@MockBean` 사용 (Spring Boot 3.4+ deprecated) → `@MockitoBean` 사용
- ❌ `@SpringBootTest`에 `@Transactional` 추가 → 테스트 간 격리 문제 발생
- ❌ MockMvc에서 한글 응답 깨짐 → `.accept(MediaType.APPLICATION_JSON)` 설정
- ❌ 테스트마다 새 ApplicationContext 로딩 → Base 클래스로 context 재사용

## References

- [Spring Boot Testing](https://docs.spring.io/spring-boot/reference/testing/) — Official guide
- [Spring Framework Testing](https://docs.spring.io/spring-framework/reference/testing.html) — `@MockitoBean`, MockMvc
- [How I test production-ready Spring Boot applications](https://www.wimdeblauwe.com/blog/2025/07/30/how-i-test-production-ready-spring-boot-applications/) — Wim Deblauwe
- [Testcontainers Java Guide](https://testcontainers.com/guides/testing-spring-boot-rest-api-using-testcontainers/) — Integration testing
- [JetBrains: Testing with Testcontainers](https://blog.jetbrains.com/idea/2024/12/testing-spring-boot-applications-using-testcontainers/)
