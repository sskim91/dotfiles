---
name: kotlin-patterns
description: Kotlin idioms, coroutines, Flow API, DSL design, sealed classes, scope functions, and Spring Boot integration patterns. Use when writing, reviewing, or refactoring Kotlin code, implementing coroutines or Flow-based async operations, designing type-safe DSLs, choosing between sealed classes vs enums, or integrating Kotlin with Spring Boot. Do NOT use for JPA/Hibernate entity patterns (use jpa-patterns skill), raw SQL optimization (use sql-optimization-patterns skill), or general Java patterns (use java-modern-patterns skill).
---

# Kotlin Development Patterns

Idiomatic Kotlin patterns for building robust, type-safe, and concurrent applications.

## Quick Start

- **Async operation needed?** → [Coroutines & Flow reference](references/coroutines-flow.md), check CRITICAL Rules #1-#6
- **Spring Boot + Kotlin project?** → [Spring Boot reference](references/kotlin-springboot.md) (compiler plugins, gotchas)
- **Building a DSL or API?** → [DSL & Idioms reference](references/dsl-idioms.md)
- **Data modeling?** → See [Decision Tree](#decision-tree) below

## When to Activate

- Writing new Kotlin code
- Reviewing or refactoring Kotlin code
- Implementing coroutines or Flow-based async operations
- Designing type-safe DSLs or builders
- Using Kotlin with Spring Boot
- Choosing between sealed classes, enums, data classes

## CRITICAL Rules

### MUST DO

1. **Null safety** — Use `?`, `?.`, `?:` consistently. Prefer safe calls over `!!`
2. **Structured concurrency** — Always use scoped coroutines (`viewModelScope`, `coroutineScope`, `supervisorScope`)
3. **Immutability** — Prefer `val` over `var`, `List` over `MutableList` in public APIs
4. **Sealed types for state** — Use `sealed class`/`sealed interface` for UI state, results, errors
5. **Flow for reactive streams** — Use `Flow` for cold streams, `StateFlow`/`SharedFlow` for hot streams
6. **Scope functions correctly** — `let` for null check + transform, `apply` for configuration, `also` for side effects
7. **Explicit API mode for libraries** — Use `explicit` API mode in library modules
8. **KDoc for public APIs** — Document public functions and classes

### MUST NOT DO

1. **`GlobalScope.launch`** — Leaks coroutines, no structured concurrency
2. **`!!` without justification** — Prefer `?.`, `?:`, or `requireNotNull` with message
3. **`runBlocking` in production** — Blocks the thread, defeats coroutines purpose
4. **Block in Flow operators** — `Thread.sleep()` in `map`/`filter` — use `delay()` + `flowOn`
5. **Ignore cancellation** — Never catch `CancellationException` (rethrow it)
6. **Forget `awaitClose` in `callbackFlow`** — Causes resource leaks
7. **Mix platform code in common modules** (KMP) — Use `expect`/`actual`

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Coroutines & Flow | [references/coroutines-flow.md](references/coroutines-flow.md) | Async operations, structured concurrency, Flow operators, backpressure, testing coroutines |
| Spring Boot + Kotlin | [references/kotlin-springboot.md](references/kotlin-springboot.md) | Spring Boot Kotlin compiler plugins, constructor DI, Router DSL, coroutines in Spring |
| DSL & Idioms | [references/dsl-idioms.md](references/dsl-idioms.md) | Type-safe builders, scope functions, extension functions, delegated properties, inline/reified |

## Core Patterns

### Sealed interface for state modeling

```kotlin
sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}

// Exhaustive when — compiler enforces all branches
fun <T> render(state: UiState<T>) = when (state) {
    is UiState.Loading -> showLoading()
    is UiState.Success -> showData(state.data)
    is UiState.Error -> showError(state.message)
}
```

### StateFlow in ViewModel

```kotlin
class UserViewModel(private val repository: UserRepository) : ViewModel() {
    private val _state = MutableStateFlow<UiState<User>>(UiState.Loading)
    val state: StateFlow<UiState<User>> = _state.asStateFlow()

    fun loadUser(id: String) {
        viewModelScope.launch {
            _state.value = UiState.Loading
            try {
                _state.value = UiState.Success(repository.getUser(id))
            } catch (e: CancellationException) {
                throw e  // Never swallow cancellation
            } catch (e: Exception) {
                _state.value = UiState.Error(e.message ?: "Unknown error")
            }
        }
    }
}
```

### Value class (zero-cost wrapper)

```kotlin
@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String) {
    init { require(value.contains("@")) { "Invalid email: $value" } }
}
```

## Decision Tree

```
Writing Kotlin code?
├─ Async operation needed?
│  ├─ Simple suspend function       → references/coroutines-flow.md
│  ├─ Reactive stream               → Flow API (references/coroutines-flow.md)
│  ├─ Callback to Flow              → callbackFlow (references/coroutines-flow.md)
│  └─ Multiple concurrent ops       → supervisorScope (references/coroutines-flow.md)
├─ Spring Boot project?
│  ├─ Kotlin-specific setup         → references/kotlin-springboot.md
│  └─ JPA entities                  → jpa-patterns skill
├─ Building DSL or API?
│  ├─ Type-safe builder             → references/dsl-idioms.md
│  ├─ Scope functions               → references/dsl-idioms.md
│  └─ Operator overloading          → references/dsl-idioms.md
└─ Data modeling?
   ├─ Fixed variants                → sealed class/interface
   ├─ Plain data holder             → data class
   ├─ Type-safe ID/wrapper          → value class (@JvmInline)
   └─ Platform-specific             → expect/actual (KMP)
```

## Anti-Patterns

**GlobalScope**

```kotlin
// BAD: Leaks, no lifecycle management
GlobalScope.launch { fetchData() }

// GOOD: Cancelled with ViewModel
viewModelScope.launch { fetchData() }
```

**Blocking in Flow**

```kotlin
// BAD: Blocks the collector thread
flow.map { Thread.sleep(1000); process(it) }

// GOOD: Suspend + offload to background
flow.map { delay(1000); process(it) }.flowOn(Dispatchers.Default)
```

**Swallowing CancellationException**

```kotlin
// BAD: Prevents coroutine cancellation
try { suspendWork() } catch (e: Exception) { log(e) }

// GOOD: Rethrow CancellationException
try {
    suspendWork()
} catch (e: CancellationException) {
    throw e
} catch (e: Exception) {
    log(e)
}
```

## Output Template

When implementing Kotlin features, provide:

1. Data models (sealed classes, data classes, value classes)
2. Implementation (suspend functions, Flow, extension functions)
3. Test file with coroutine test support
4. Brief explanation of Kotlin-specific patterns used
