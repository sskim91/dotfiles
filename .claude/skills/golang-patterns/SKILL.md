---
name: golang-patterns
description: Use when writing or refactoring Go code, designing packages, implementing concurrency, using generics, or building HTTP services. Do NOT use for database optimization (use sql-optimization-patterns), API design (use api-design), or CI/CD (use github-actions).
---

# Go Development Patterns

Idiomatic Go patterns and best practices for building robust, efficient, and maintainable applications. Based on Effective Go, Go Code Review Comments, Uber Go Style Guide, and Google Go Style Guide.

## Quick Start

- **Concurrency needed?** → [Concurrency Patterns reference](references/concurrency-patterns.md), check CRITICAL Rules #1-#5
- **Using Go 1.21+ features?** → [Modern Go reference](references/modern-go.md) (slog, iterators, ServeMux, generics)
- **Writing tests?** → [Testing Patterns reference](references/testing-patterns.md) (table-driven, fuzz, benchmarks)
- **Error handling?** → See [Error Handling](#error-handling) below
- **Package design?** → See [Package Organization](#package-organization) below

## When to Activate

- Writing new Go code
- Reviewing or refactoring Go code
- Designing Go packages/modules
- Implementing concurrency patterns
- Building HTTP services with net/http
- Writing tests, benchmarks, or fuzz tests
- Using generics or iterators

## CRITICAL Rules

### MUST DO

1. **Handle every error** — Never use `_` for errors unless explicitly justified with comment
2. **Wrap errors with context** — `fmt.Errorf("operation %s: %w", name, err)` always
3. **Pass context.Context as first param** — Never store in struct fields
4. **Use structured concurrency** — Every goroutine must have clear ownership and shutdown path
5. **Close resources with defer** — `defer f.Close()` immediately after successful open
6. **Accept interfaces, return structs** — Define interfaces at consumer, not provider
7. **Make zero values useful** — Design types to work without explicit initialization
8. **Format with gofmt/goimports** — Non-negotiable, run before every commit
9. **Preallocate slices** — `make([]T, 0, knownLen)` when capacity is known
10. **Use `errors.Is`/`errors.As`** — Never compare errors with `==` (except sentinel errors pre-1.13)

### MUST NOT DO

1. **`panic` for control flow** — Only for truly unrecoverable programmer errors
2. **Naked returns in long functions** — Only acceptable in very short functions (< 5 lines)
3. **`init()` with side effects** — Avoid init(); prefer explicit initialization via constructors
4. **Global mutable state** — Use dependency injection instead of package-level vars
5. **Goroutine leaks** — Always provide cancellation path (context, done channel, or buffered channel)
6. **`sync.Mutex` copying** — Never copy a Mutex; embed as pointer or use pointer receiver
7. **`interface{}` when generics fit** — Use type parameters for type-safe collections (Go 1.18+)
8. **Log AND return error** — Handle errors once: either log or return, never both (Uber Guide)
9. **`math/rand` for security** — Use `crypto/rand` for keys, tokens, and secrets
10. **`fmt.Sprintf` for int-to-string** — Use `strconv.Itoa`/`strconv.FormatInt` (3x faster)

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Concurrency | [references/concurrency-patterns.md](references/concurrency-patterns.md) | goroutines, channels, sync, errgroup, context, graceful shutdown |
| Modern Go (1.21-1.23+) | [references/modern-go.md](references/modern-go.md) | slog, iterators, enhanced ServeMux, generics, range-over-int |
| Testing | [references/testing-patterns.md](references/testing-patterns.md) | table-driven tests, fuzz, benchmarks, mocking, golden files, HTTP handler tests |

## Decision Tree

```
Writing Go code?
├─ Error handling?
│  ├─ Known error condition       → sentinel error (var ErrXxx = errors.New(...))
│  ├─ Error needs context         → fmt.Errorf("context: %w", err)
│  ├─ Multiple errors             → errors.Join (Go 1.20+)
│  └─ Rich error info needed      → custom error type implementing error interface
├─ Concurrency needed?
│  ├─ Fire-and-forget task        → references/concurrency-patterns.md (Worker Pool)
│  ├─ Multiple concurrent ops     → errgroup.Group
│  ├─ Shared state                → sync.Mutex or channel
│  ├─ Cancellation/timeout        → context.WithCancel / WithTimeout
│  └─ Graceful shutdown           → signal.Notify + context
├─ HTTP service?
│  ├─ Method + path routing       → Enhanced ServeMux (references/modern-go.md)
│  ├─ Middleware pattern           → func(http.Handler) http.Handler
│  └─ Structured logging          → slog (references/modern-go.md)
├─ Type-safe collection?
│  ├─ Simple generic func         → references/modern-go.md (Generics)
│  ├─ Iterator pattern            → iter.Seq / iter.Seq2 (Go 1.23+)
│  └─ Type constraint             → interface with ~type union
├─ Testing?
│  ├─ Multiple inputs             → Table-driven tests
│  ├─ Input validation            → Fuzz tests
│  ├─ Performance measurement     → Benchmarks
│  └─ Expected output files       → Golden files
└─ Configuration?
   ├─ Many optional params        → Functional Options pattern
   ├─ Simple required params      → Constructor function
   └─ External config             → struct + json/yaml/env tags
```

## Verification

코드 작성 후 반드시 실행:
```bash
go build ./...                    # 컴파일 확인
go test ./... -v                  # 테스트 실행
go vet ./...                      # 정적 분석
golangci-lint run                 # 린터 (설치된 경우)
```

## Output Template

When implementing Go features, provide:

1. Package structure and organization
2. Core types (structs, interfaces, error types)
3. Implementation with proper error handling
4. Test file with table-driven tests
5. Brief explanation of Go-specific patterns used
