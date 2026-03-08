# DSL & Kotlin Idioms

## Type-Safe Builders

```kotlin
// Configuration DSL with lambda-with-receiver
class ServerConfig {
    var host: String = "localhost"
    var port: Int = 8080
    var ssl: SslConfig? = null

    fun ssl(init: SslConfig.() -> Unit) {
        ssl = SslConfig().apply(init)
    }
}

class SslConfig {
    var certPath: String = ""
    var keyPath: String = ""
}

fun server(init: ServerConfig.() -> Unit): ServerConfig =
    ServerConfig().apply(init)

// Usage — reads like declarative config
val config = server {
    host = "api.example.com"
    port = 443
    ssl {
        certPath = "/etc/ssl/cert.pem"
        keyPath = "/etc/ssl/key.pem"
    }
}
```

## Lambda with Receiver

```kotlin
// Builder pattern with type-safe DSL
class User private constructor(
    val id: String,
    val name: String,
    val email: String,
    val age: Int?
) {
    class Builder {
        var id: String = ""
        var name: String = ""
        var email: String = ""
        var age: Int? = null

        fun build(): User {
            require(id.isNotBlank()) { "ID is required" }
            require(name.isNotBlank()) { "Name is required" }
            return User(id, name, email, age)
        }
    }
}

fun user(init: User.Builder.() -> Unit): User =
    User.Builder().apply(init).build()

val user = user {
    id = "123"
    name = "John Doe"
    email = "john@example.com"
    age = 30
}
```

## Scope Functions

```kotlin
// let — null check + transform
val displayName = user?.let { "${it.name} (${it.email})" }

// run — execute block, return result
val greeting = run {
    val name = getName()
    val title = getTitle()
    "$title $name"
}

// with — operate on object without receiver repetition
val message = with(user) {
    "User: $name, Email: $email, Active: $isActive"
}

// apply — configure object, returns the object itself
val user = User().apply {
    name = "John"
    email = "john@example.com"
    isActive = true
}

// also — side effects, returns the object itself
val saved = user
    .also { logger.info("Saving user: ${it.name}") }
    .also { validate(it) }
    .also { repository.save(it) }

// takeIf / takeUnless — conditional return
val adult = user.takeIf { it.age >= 18 }
val minor = user.takeUnless { it.age >= 18 }
```

### Scope Function Cheat Sheet

| Function | Object ref | Return value | Use case |
|----------|-----------|--------------|----------|
| `let` | `it` | Lambda result | Null check + transform |
| `run` | `this` | Lambda result | Object config + compute result |
| `with` | `this` | Lambda result | Grouping calls on object |
| `apply` | `this` | Object itself | Object configuration |
| `also` | `it` | Object itself | Side effects (logging, validation) |

## Extension Functions

```kotlin
// String extensions
fun String.isValidEmail(): Boolean =
    matches(Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$"))

fun String.truncate(length: Int, ellipsis: String = "..."): String =
    if (this.length <= length) this
    else "${take(length - ellipsis.length)}$ellipsis"

// Generic conditional extension
inline fun <T> T.applyIf(condition: Boolean, block: T.() -> Unit): T =
    if (condition) apply(block) else this
```

## Delegated Properties

```kotlin
import kotlin.properties.Delegates

// Lazy — computed once on first access
class Repository {
    val database: Database by lazy {
        Database.connect("jdbc:postgresql://localhost/db")
    }
}

// Observable — react to changes
class User {
    var name: String by Delegates.observable("<not set>") { prop, old, new ->
        println("${prop.name} changed from $old to $new")
    }
}

// Vetoable — reject invalid changes
class Account {
    var balance: Double by Delegates.vetoable(0.0) { _, _, new ->
        new >= 0 // Only allow non-negative balance
    }
}

// Map delegation — populate properties from map
class UserData(map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
    val email: String by map
}

val userData = UserData(mapOf("name" to "John", "age" to 30, "email" to "john@example.com"))
```

## Sealed Classes & When

```kotlin
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    data object Loading : Result<Nothing>()
}

// Exhaustive when — compiler error if branch missing
fun <T> handleResult(result: Result<T>): String = when (result) {
    is Result.Success -> "Data: ${result.data}"
    is Result.Error -> "Error: ${result.exception.message}"
    Result.Loading -> "Loading..."
}

// Sealed interface — allows multiple inheritance
sealed interface UiEvent {
    data class Click(val id: String) : UiEvent
    data class Scroll(val position: Int) : UiEvent
    data object Refresh : UiEvent
}
```

## Inline & Reified

```kotlin
// Inline — eliminates lambda overhead
inline fun <T> measureTime(block: () -> T): Pair<T, Long> {
    val start = System.currentTimeMillis()
    val result = block()
    return result to (System.currentTimeMillis() - start)
}

// Reified — access type parameter at runtime
inline fun <reified T> parseJson(json: String): T =
    Json.decodeFromString<T>(json)

// Value class — zero runtime overhead wrapper
@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String) {
    init { require(value.contains("@")) { "Invalid email" } }
}
```

## Infix Functions

```kotlin
// Test assertions
infix fun <T> T.shouldBe(expected: T) {
    if (this != expected) throw AssertionError("Expected $expected but got $this")
}

val result = 2 + 2
result shouldBe 4

// DSL with infix
infix fun String.GET(handler: () -> Unit): RouteDefinition =
    RouteDefinition(this, handler)

val route = "/users" GET { println("Get users") }
```

## Operator Overloading

```kotlin
data class Vector(val x: Double, val y: Double) {
    operator fun plus(other: Vector) = Vector(x + other.x, y + other.y)
    operator fun minus(other: Vector) = Vector(x - other.x, y - other.y)
    operator fun times(scalar: Double) = Vector(x * scalar, y * scalar)
    operator fun unaryMinus() = Vector(-x, -y)
    operator fun get(index: Int): Double = when (index) {
        0 -> x; 1 -> y
        else -> throw IndexOutOfBoundsException()
    }
}

// Invoke operator — call object like function
class Greeter(private val greeting: String) {
    operator fun invoke(name: String) = "$greeting, $name!"
}

val greet = Greeter("Hello")
println(greet("World")) // Hello, World!
```

## Quick Reference

| Idiom | Purpose |
|-------|---------|
| `let` | Transform & null check |
| `run` | Execute block, return result |
| `with` | Operate on object |
| `apply` | Configure object |
| `also` | Side effects |
| `takeIf/takeUnless` | Conditional return |
| `by lazy` | Lazy initialization |
| `by Delegates.observable` | Observe changes |
| `inline fun` | Eliminate lambda overhead |
| `reified` | Access type at runtime |
| `@JvmInline value class` | Zero-cost wrapper |
| `infix` | Custom binary operators |
| `operator` | Operator overloading |
| `sealed class/interface` | Restricted hierarchies |
