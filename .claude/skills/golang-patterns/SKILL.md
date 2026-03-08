---
name: golang-patterns
description: Go idioms, error handling, concurrency, generics, iterators (Go 1.23), slog, enhanced ServeMux routing, and testing patterns following Effective Go, Uber/Google style guides. Use when writing, reviewing, or refactoring Go code, designing packages, implementing concurrency with goroutines/channels, using generics, writing tests or benchmarks, or building HTTP services. Do NOT use for database-specific optimization (use sql-optimization-patterns skill), REST API design theory (use api-design skill), or CI/CD pipeline setup (use github-actions skill).
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

## Core Patterns

### Error Handling

```go
// Wrap errors with context using %w
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("load config %s: %w", path, err)
    }

    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config %s: %w", path, err)
    }
    return &cfg, nil
}

// Sentinel errors for common cases
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
)

// Custom error types for rich context
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: %s: %s", e.Field, e.Message)
}

// Check errors with errors.Is / errors.As
if errors.Is(err, ErrNotFound) { /* handle */ }

var valErr *ValidationError
if errors.As(err, &valErr) { /* handle */ }

// Join multiple errors (Go 1.20+)
err = errors.Join(err1, err2, err3)
```

### Compile-Time Interface Compliance

```go
// Verify type implements interface at compile time (Uber Go Style)
var _ http.Handler = (*MyHandler)(nil)
var _ io.ReadWriteCloser = (*MyConn)(nil)
```

### Accept Interfaces, Return Structs

```go
// GOOD: Interface defined at consumer, not provider
package service

type UserStore interface {
    GetUser(ctx context.Context, id string) (*User, error)
    SaveUser(ctx context.Context, user *User) error
}

type Service struct {
    store UserStore
}

func New(store UserStore) *Service {
    return &Service{store: store}
}
```

### Functional Options

```go
type Server struct {
    addr    string
    timeout time.Duration
    logger  *slog.Logger
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func WithLogger(l *slog.Logger) Option {
    return func(s *Server) { s.logger = l }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{
        addr:    addr,
        timeout: 30 * time.Second,
        logger:  slog.Default(),
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}
```

### Make Zero Value Useful

```go
// GOOD: Works without initialization
type Counter struct {
    mu    sync.Mutex
    count int  // zero value is 0
}

func (c *Counter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

// BAD: Requires initialization — nil map panics
type Registry struct {
    items map[string]Item  // nil map will panic on write
}
```

## Package Organization

### Standard Project Layout

```
myproject/
├── cmd/
│   └── myapp/
│       └── main.go           # Entry point, wire dependencies
├── internal/
│   ├── handler/              # HTTP handlers
│   ├── service/              # Business logic
│   ├── repository/           # Data access
│   └── config/               # Configuration
├── pkg/                      # Public library code (optional)
├── api/                      # API definitions (proto, OpenAPI)
├── testdata/                 # Test fixtures
├── go.mod
└── Makefile
```

### Package Naming

```go
// GOOD: Short, lowercase, singular noun
package http
package user
package config

// BAD: Verbose, suffixed, or generic
package httpHandler    // redundant suffix
package user_service   // underscores
package utils          // too generic — split into focused packages
package common         // same problem
```

### Avoid Package-Level State

```go
// BAD: Global mutable state
var db *sql.DB

func init() {
    db, _ = sql.Open("postgres", os.Getenv("DATABASE_URL"))
}

// GOOD: Dependency injection
type Server struct {
    db *sql.DB
}

func NewServer(db *sql.DB) *Server {
    return &Server{db: db}
}
```

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

## Anti-Patterns

**Context in struct**
```go
// BAD: Context should not be stored
type Request struct {
    ctx context.Context
    ID  string
}

// GOOD: Context as first parameter
func Process(ctx context.Context, id string) error { ... }
```

**Mixing receivers**
```go
// BAD: Inconsistent receiver types
func (c Counter) Value() int   { return c.count }  // value
func (c *Counter) Inc()        { c.count++ }        // pointer
// Pick one — if any method needs pointer, use pointer for all
```

**Unnecessary else after return**
```go
// BAD
if err != nil {
    return err
} else {
    return nil
}

// GOOD: Return early, keep happy path unindented
if err != nil {
    return err
}
return nil
```

## Tooling

```bash
# Build & run
go build ./...
go run ./cmd/myapp

# Testing
go test ./...
go test -race -cover ./...
go test -bench=. -benchmem ./...
go test -fuzz=FuzzXxx -fuzztime=30s ./...

# Static analysis
go vet ./...
staticcheck ./...
golangci-lint run

# Module management
go mod tidy
go mod verify

# Formatting
gofmt -w .
goimports -w .
```

### Recommended golangci-lint config (.golangci.yml)

```yaml
linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gofmt
    - goimports
    - misspell
    - unconvert
    - unparam
    - gocritic
    - revive

linters-settings:
  errcheck:
    check-type-assertions: true
  govet:
    enable:
      - shadow
  revive:
    rules:
      - name: unexported-return
        disabled: true
```

## Quick Reference: Go Idioms

| Idiom | Description |
|-------|-------------|
| Accept interfaces, return structs | Functions accept interface params, return concrete types |
| Errors are values | Treat errors as first-class values, not exceptions |
| Don't communicate by sharing memory | Share memory by communicating (channels) |
| Make the zero value useful | Types should work without explicit initialization |
| A little copying > a little dependency | Avoid unnecessary external dependencies |
| Clear is better than clever | Prioritize readability over cleverness |
| Return early | Handle errors first, keep happy path unindented |
| gofmt is everyone's friend | Always format with gofmt/goimports |
| Define interfaces at consumer | Not at the package that implements them |

## Output Template

When implementing Go features, provide:

1. Package structure and organization
2. Core types (structs, interfaces, error types)
3. Implementation with proper error handling
4. Test file with table-driven tests
5. Brief explanation of Go-specific patterns used
