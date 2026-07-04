---
name: java-modern-patterns
description: Use when writing Java 21+ code, refactoring to modern idioms, choosing records vs classes, using virtual threads, or applying pattern matching. Do NOT use for JPA (use jpa-patterns) or SQL optimization (use sql-optimization-patterns).
paths: "**/*.java, **/build.gradle*, **/pom.xml"
---

# Modern Java 21+ Patterns

버전 경계(JDK 21~25)와 실수 잦은 지점만 담는다. 일반 Java 문법·패턴 지식은 모델에 이미 있음.

## CRITICAL Rules

1. **NEVER** use `synchronized` blocks with I/O inside virtual thread tasks — causes thread pinning (fixed in JDK 24+ via JEP 491, but `ReentrantLock` remains portable)
2. **ALWAYS** prefer `sealed interface` + `record` over class hierarchies for modeling domain alternatives
3. **PREFER** `ScopedValue` over `ThreadLocal` with virtual threads — ThreadLocal works but wastes memory at scale
4. **ALWAYS** handle all cases in pattern-matching `switch` — rely on compiler exhaustiveness, avoid `default`
5. **NEVER** pool virtual threads — create a new one per task via `Thread.startVirtualThread()` or `Executors.newVirtualThreadPerTaskExecutor()`
6. **ALWAYS** use records for DTOs, API responses, and value objects — not for JPA entities
7. **NEVER** add mutable state to records — defensive copies in compact constructors for mutable components
8. **PREFER** `ReentrantLock` over `synchronized` when code may run on virtual threads (required before JDK 24; recommended after for portability)
9. **PREFER** `Gatherers` for custom stream intermediate operations over imperative loops with accumulators

## Version Boundaries

| Feature | JDK | Note |
|---------|-----|------|
| Record patterns, pattern-matching switch | 21 final | |
| Unnamed variables/patterns (`_`) | 22 final | `case Noise(_)`, `catch (Exception _)` |
| Stream Gatherers (`windowFixed`, `scan`, custom) | 24 final (JEP 485) | |
| synchronized pinning fix | 24 (JEP 491) | 이전 버전은 ReentrantLock 필수 |
| `StructuredTaskScope.open()` + `Joiner` API | 25 (JEP 505, **아직 preview** — `--enable-preview` 필요) | JDK 21~23은 `new StructuredTaskScope.ShutdownOnFailure()` + `throwIfFailed()` — API가 다름 |
| `ScopedValue` final | 25 (JEP 506) | 이전엔 preview — `--enable-preview` 필요 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ sealed 타입 switch에 `default` 추가 → exhaustiveness 보장 상실, 새 서브타입 추가 시 컴파일 에러로 못 잡음
- ❌ record에 mutable 필드(List, Map) 직접 저장 → compact constructor에서 방어적 복사
- ❌ virtual thread에서 `synchronized` + I/O → pinning. 탐지: `-Djdk.tracePinnedThreads=full`
- ❌ JDK 21 프로젝트에 JDK 25의 `StructuredTaskScope.open()` 코드 생성 → 버전 확인 먼저
- ❌ CPU-bound 작업에 virtual threads → platform threads / `ForkJoinPool`이 맞음
- ❌ Spring `@Async`가 virtual threads 안 탐 → 커스텀 executor가 기본값 덮어씀, `AsyncConfigurer`에 `newVirtualThreadPerTaskExecutor()` 설정
- ❌ `ScopedValue.get()`이 `NoSuchElementException` → `ScopedValue.where().run()` 바인딩 밖에서 접근, `isBound()`로 확인

## Cross-References

| Topic | Skill |
|-------|-------|
| JPA entities (records 쓰지 말 것) | `jpa-patterns` |
| SQL query optimization | `sql-optimization-patterns` |
