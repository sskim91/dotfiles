---
name: kotlin-patterns
description: Use when writing or refactoring Kotlin code, implementing coroutines/Flow, designing DSLs, or integrating Kotlin with Spring Boot. Do NOT use for JPA (use jpa-patterns), SQL optimization (use sql-optimization-patterns), or Java patterns (use java-modern-patterns).
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

## Pattern Hints

- **Value class 적극 활용**: UserId, Email 같은 primitive wrapper는 `@JvmInline value class`로 감싸서 타입 안전성 확보
- **SharedFlow for one-shot events**: 토스트, 네비게이션 등 일회성 이벤트는 `MutableSharedFlow`로 (StateFlow는 상태 유지용)
- **Multiple sealed interfaces**: UiState 외에 Result, Event 등 별도 sealed interface로 관심사 분리

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

## Output Template

When implementing Kotlin features, provide:

1. Data models (sealed classes, data classes, value classes)
2. Implementation (suspend functions, Flow, extension functions)
3. Test file with coroutine test support
4. Brief explanation of Kotlin-specific patterns used
