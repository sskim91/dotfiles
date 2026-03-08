# Spring Boot + Kotlin

Kotlin-specific patterns for Spring Boot. General Spring Boot/JPA patterns are in the `jpa-patterns` skill.

> **Version reference**: Spring Boot 3.5+ (Kotlin 1.7+), Spring Boot 4.0+ (Kotlin 2.2+)
> Source: [Spring Boot Kotlin Docs](https://docs.spring.io/spring-boot/reference/features/kotlin)

## Compiler Plugins

Kotlin classes are `final` by default — Spring needs `open` classes for proxying. Use compiler plugins instead of manually adding `open`:

| Plugin | Gradle ID | Effect |
|--------|-----------|--------|
| **kotlin-spring** | `org.jetbrains.kotlin.plugin.spring` | Opens `@Component`, `@Service`, `@Repository`, `@Controller`, `@Configuration`, `@Transactional` annotated classes |
| **kotlin-jpa** | `org.jetbrains.kotlin.plugin.jpa` | Generates synthetic no-arg constructor for `@Entity`, `@Embeddable`, `@MappedSuperclass` |

```kotlin
// build.gradle.kts — check latest versions at start.spring.io
plugins {
    kotlin("jvm")
    kotlin("plugin.spring")                // Required
    kotlin("plugin.jpa")                   // If using JPA
    kotlin("plugin.serialization")         // If using kotlinx.serialization
    id("org.springframework.boot")
    id("io.spring.dependency-management")
}
```

**start.spring.io** includes these plugins by default when Kotlin is selected.

## Constructor-Based DI

Primary constructor injection is the idiomatic Kotlin pattern. No `@Autowired` needed when there's a single constructor.

```kotlin
// GOOD: Idiomatic Kotlin — concise, immutable
@Service
class UserService(
    private val userRepository: UserRepository,
    private val emailService: EmailService
) {
    fun getUser(id: Long): User = userRepository.findById(id)
        .orElseThrow { NoSuchElementException("User $id not found") }
}

// BAD: Java-style field injection
@Service
class UserService {
    @Autowired private lateinit var userRepository: UserRepository  // Avoid
}
```

## @ConfigurationProperties with Data Class

Immutable, type-safe configuration binding. Constructor binding is the default — no `@ConstructorBinding` annotation needed (Spring Boot 3.0+).

```kotlin
@ConfigurationProperties("app.mail")
data class MailProperties(
    val host: String,
    val port: Int = 587,
    val auth: AuthProperties = AuthProperties()
) {
    data class AuthProperties(
        val username: String = "",
        val password: String = ""
    )
}

// application.yml
// app:
//   mail:
//     host: smtp.example.com
//     port: 465
//     auth:
//       username: user
//       password: secret
```

For metadata generation (IDE auto-completion), add `kapt`:

```kotlin
// build.gradle.kts
dependencies {
    kapt("org.springframework.boot:spring-boot-configuration-processor")
}
```

## Null Safety Integration

Spring's nullability annotations (`@NonNull`, `@Nullable`) map directly to Kotlin types:

```kotlin
// Spring Data repository — Kotlin null type determines behavior
interface UserRepository : JpaRepository<User, Long> {
    fun findByEmail(email: String): User?       // Returns null if not found
    fun findByUsername(username: String): User   // Throws if not found
}
```

## Router DSL (Functional Endpoints)

Kotlin DSL for defining routes without annotations. Available for both WebFlux and WebMvc.

```kotlin
// WebFlux — router { }
@Configuration
class UserRoutes(private val handler: UserHandler) {

    @Bean
    fun userRouter() = router {
        accept(APPLICATION_JSON).nest {
            GET("/api/users", handler::findAll)
            GET("/api/users/{id}", handler::findById)
            POST("/api/users", handler::create)
        }
    }
}

// WebFlux with coroutines — coRouter { }
@Configuration
class UserRoutes(private val handler: UserHandler) {

    @Bean
    fun userRouter() = coRouter {
        accept(APPLICATION_JSON).nest {
            GET("/api/users", handler::findAll)       // suspend fun
            GET("/api/users/{id}", handler::findById)  // suspend fun
        }
    }
}
```

## Coroutines in Spring

Spring supports `suspend` functions and `Flow` return types.

### WebFlux (reactive)

```kotlin
@RestController
@RequestMapping("/api/users")
class UserController(private val userService: UserService) {

    @GetMapping
    suspend fun findAll(): List<User> = userService.findAll()

    @GetMapping("/{id}")
    suspend fun findById(@PathVariable id: Long): User =
        userService.findById(id)
            ?: throw ResponseStatusException(HttpStatus.NOT_FOUND)

    // Return Flow for streaming responses
    @GetMapping("/stream", produces = [MediaType.TEXT_EVENT_STREAM_VALUE])
    fun streamUsers(): Flow<User> = userService.observeUsers()
}
```

### WebMvc (servlet)

Spring MVC also supports `suspend` functions (Spring Boot 3.2+):

```kotlin
@RestController
class UserController(private val userService: UserService) {

    @GetMapping("/api/users/{id}")
    suspend fun getUser(@PathVariable id: Long): User =
        userService.getUser(id)
}
```

## Data Classes for DTOs

```kotlin
// Request/Response DTOs — immutable, auto-generates equals/hashCode/toString/copy
data class CreateUserRequest(
    @field:NotBlank val name: String,
    @field:Email val email: String,
    @field:Size(min = 8) val password: String
)

data class UserResponse(
    val id: Long,
    val name: String,
    val email: String,
    val createdAt: Instant
)
```

**Note:** Jackson Kotlin module is auto-registered by Spring Boot. It handles data class deserialization (including default parameter values) without additional configuration.

**Validation:** Use `@field:` target for Bean Validation annotations on data class constructor parameters. Without `@field:`, the annotation targets the constructor parameter, not the backing field.

## Logging

```kotlin
// Companion object logger — idiomatic Kotlin pattern
@Service
class UserService(private val repository: UserRepository) {

    fun createUser(request: CreateUserRequest): User {
        logger.info("Creating user: {}", request.email)
        return repository.save(request.toEntity())
    }

    companion object {
        private val logger = LoggerFactory.getLogger(UserService::class.java)
    }
}
```

## Exception Handling

```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(NoSuchElementException::class)
    fun handleNotFound(e: NoSuchElementException) =
        ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ErrorResponse(e.message ?: "Not found"))

    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidation(e: MethodArgumentNotValidException) =
        ResponseEntity.badRequest()
            .body(ErrorResponse(
                message = "Validation failed",
                details = e.bindingResult.fieldErrors.map {
                    "${it.field}: ${it.defaultMessage}"
                }
            ))
}

data class ErrorResponse(
    val message: String,
    val details: List<String> = emptyList()
)
```

## Testing

```kotlin
// Use MockK instead of Mockito for idiomatic Kotlin mocking
// Dependencies: io.mockk:mockk, com.ninja-squad:springmockk

@WebMvcTest(UserController::class)
class UserControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockkBean
    private lateinit var userService: UserService

    @Test
    fun `returns user by id`() {
        every { userService.findById(1L) } returns User(1L, "John")

        mockMvc.get("/api/users/1")
            .andExpect {
                status { isOk() }
                jsonPath("$.name") { value("John") }
            }

        verify { userService.findById(1L) }
    }
}
```

**Test dependencies:**

```kotlin
// build.gradle.kts — check latest versions at Maven Central
dependencies {
    testImplementation("io.mockk:mockk:<latest>")
    testImplementation("com.ninja-squad:springmockk:<latest>")
}
```

## Common Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| `open` errors on Spring beans | Missing kotlin-spring plugin | Add `kotlin("plugin.spring")` |
| JPA entity no-arg constructor | Missing kotlin-jpa plugin | Add `kotlin("plugin.jpa")` |
| Validation annotations ignored | Wrong annotation target | Use `@field:NotBlank` instead of `@NotBlank` |
| Jackson fails on data class | Missing Kotlin module | Auto-configured — check `jackson-module-kotlin` is on classpath |
| `@ConfigurationProperties` not binding | Missing `@EnableConfigurationProperties` | Add `@EnableConfigurationProperties(MyProps::class)` or `@ConfigurationPropertiesScan` |
| `lateinit var` in tests | Kotlin property not initialized | Use `@Autowired` with `lateinit var` in tests — acceptable pattern |
