# Modern Go (1.21-1.23+)

## Structured Logging with slog (Go 1.21+)

The `log/slog` package provides structured, leveled logging in the standard library.

### Basic Usage

```go
import "log/slog"

// Default text handler
slog.Info("user logged in", "user_id", 123, "ip", "192.168.1.1")
// Output: 2024/01/15 10:30:00 INFO user logged in user_id=123 ip=192.168.1.1

// JSON handler for production
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))
slog.SetDefault(logger)

// Output: {"time":"2024-01-15T10:30:00Z","level":"INFO","msg":"user logged in","user_id":123,"ip":"192.168.1.1"}
```

### Logger with Context Fields

```go
// Add persistent fields to a logger
logger := slog.Default().With(
    "service", "auth",
    "version", "1.2.0",
)

// Group related fields
logger.Info("request completed",
    slog.Group("request",
        slog.String("method", "GET"),
        slog.String("path", "/users"),
        slog.Int("status", 200),
    ),
    slog.Duration("latency", elapsed),
)
```

### LogValuer for Sensitive Data

```go
// Implement slog.LogValuer to control what gets logged
type User struct {
    ID           string
    Email        string
    PasswordHash string
}

func (u User) LogValue() slog.Value {
    return slog.GroupValue(
        slog.String("id", u.ID),
        // Email and PasswordHash are excluded from logs
    )
}

// Usage: slog.Info("user created", "user", user)
// Output: ... user.id=abc123  (no email or password hash)
```

### Context-Aware Logging Middleware

```go
type ctxKey string

const loggerKey ctxKey = "logger"

func LoggingMiddleware(logger *slog.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            reqLogger := logger.With(
                "request_id", r.Header.Get("X-Request-ID"),
                "method", r.Method,
                "path", r.URL.Path,
            )
            ctx := context.WithValue(r.Context(), loggerKey, reqLogger)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

func LoggerFromContext(ctx context.Context) *slog.Logger {
    if logger, ok := ctx.Value(loggerKey).(*slog.Logger); ok {
        return logger
    }
    return slog.Default()
}
```

### Custom Handler

```go
// Implement slog.Handler interface for custom formatting
type PrettyHandler struct {
    slog.Handler
    w io.Writer
}

func (h *PrettyHandler) Handle(ctx context.Context, r slog.Record) error {
    level := r.Level.String()
    timestamp := r.Time.Format("15:04:05")

    fmt.Fprintf(h.w, "%s [%s] %s", timestamp, level, r.Message)

    r.Attrs(func(a slog.Attr) bool {
        fmt.Fprintf(h.w, " %s=%v", a.Key, a.Value)
        return true
    })
    fmt.Fprintln(h.w)
    return nil
}
```

## Enhanced ServeMux Routing (Go 1.22+)

The `net/http.ServeMux` now supports method matching and path wildcards.

### Method Matching

```go
mux := http.NewServeMux()

// Method-specific routes
mux.HandleFunc("GET /users", listUsers)
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("GET /users/{id}", getUser)
mux.HandleFunc("PUT /users/{id}", updateUser)
mux.HandleFunc("DELETE /users/{id}", deleteUser)

// GET also registers HEAD automatically
// More specific patterns take precedence over less specific
```

### Path Wildcards

```go
mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")  // extract wildcard value
    fmt.Fprintf(w, "User: %s", id)
})

// Catch-all wildcard with {path...}
mux.HandleFunc("GET /files/{path...}", func(w http.ResponseWriter, r *http.Request) {
    filePath := r.PathValue("path")  // matches rest of path
    fmt.Fprintf(w, "File: %s", filePath)
})
```

### Precedence Rules

```go
mux.HandleFunc("GET /posts/{id}", getPost)       // specific
mux.HandleFunc("/posts/{id}", handlePost)         // less specific (any method)
mux.HandleFunc("GET /posts/latest", getLatest)    // most specific (exact match)

// Priority: exact path > method+wildcard > wildcard only
// "GET /posts/latest" matches getLatest (exact)
// "GET /posts/42" matches getPost (method + wildcard)
// "DELETE /posts/42" matches handlePost (wildcard, any method)
```

### Complete HTTP Server Example

```go
func main() {
    logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
    slog.SetDefault(logger)

    mux := http.NewServeMux()

    // Routes
    mux.HandleFunc("GET /health", handleHealth)
    mux.HandleFunc("GET /api/v1/users", handleListUsers)
    mux.HandleFunc("POST /api/v1/users", handleCreateUser)
    mux.HandleFunc("GET /api/v1/users/{id}", handleGetUser)

    // Middleware chain
    handler := LoggingMiddleware(logger)(RecoverMiddleware(mux))

    server := &http.Server{
        Addr:         ":8080",
        Handler:      handler,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 30 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    // Graceful shutdown — see concurrency-patterns.md
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
    defer stop()

    go func() {
        slog.Info("server started", "addr", server.Addr)
        if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            slog.Error("server error", "err", err)
            os.Exit(1)
        }
    }()

    <-ctx.Done()
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(shutdownCtx); err != nil {
        slog.Error("shutdown error", "err", err)
    }
}
```

### Middleware Pattern

```go
// Standard middleware signature
func RecoverMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                slog.Error("panic recovered", "err", err, "stack", string(debug.Stack()))
                http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// Chain middlewares
// handler := middleware1(middleware2(middleware3(finalHandler)))
```

## Generics (Go 1.18+)

### Type Constraints

```go
import "cmp"  // Go 1.21+

// cmp.Ordered replaces golang.org/x/exp/constraints.Ordered
func Max[T cmp.Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}

// Custom constraints with type union
type Number interface {
    ~int | ~int32 | ~int64 | ~float32 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

// ~ prefix: accept underlying type (type MyInt int also matches ~int)
```

### Generic Data Structures

```go
// Generic Set
type Set[T comparable] map[T]struct{}

func NewSet[T comparable](items ...T) Set[T] {
    s := make(Set[T], len(items))
    for _, item := range items {
        s[item] = struct{}{}
    }
    return s
}

func (s Set[T]) Add(item T)           { s[item] = struct{}{} }
func (s Set[T]) Contains(item T) bool { _, ok := s[item]; return ok }
func (s Set[T]) Remove(item T)        { delete(s, item) }

// Generic Result type
type Result[T any] struct {
    Value T
    Err   error
}

func Ok[T any](val T) Result[T]       { return Result[T]{Value: val} }
func Fail[T any](err error) Result[T] { return Result[T]{Err: err} }
```

### Generic Utility Functions

```go
// Map transforms a slice
func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

// Filter selects elements matching predicate
func Filter[T any](s []T, pred func(T) bool) []T {
    result := make([]T, 0)
    for _, v := range s {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

// Keys extracts map keys
func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}
```

### When NOT to Use Generics

```go
// AVOID: Over-generic code. If a simple interface works, use it.
// BAD: Generic for no benefit
func Process[T Processor](items []T) {
    for _, item := range items {
        item.Process()
    }
}

// GOOD: Interface is simpler and clearer
func Process(items []Processor) {
    for _, item := range items {
        item.Process()
    }
}

// USE generics when:
// - Writing data structures (Set, Stack, Queue)
// - Writing utility functions (Map, Filter, Sort)
// - Type safety matters (no interface{} / any casts needed)
// - Multiple types need same algorithm
```

## Iterators (Go 1.23+)

### iter.Seq and iter.Seq2

```go
import "iter"

// iter.Seq[V]  = func(yield func(V) bool)       — single value
// iter.Seq2[K,V] = func(yield func(K, V) bool)   — key-value pair

// Iterator that yields all elements of a set
func (s Set[E]) All() iter.Seq[E] {
    return func(yield func(E) bool) {
        for v := range s {
            if !yield(v) {
                return
            }
        }
    }
}

// Usage
for item := range mySet.All() {
    fmt.Println(item)
}
```

### Building Custom Iterators

```go
// Fibonacci iterator — infinite sequence
func Fibonacci() iter.Seq[int] {
    return func(yield func(int) bool) {
        a, b := 0, 1
        for {
            if !yield(a) {
                return
            }
            a, b = b, a+b
        }
    }
}

// Usage — break stops the iterator
for n := range Fibonacci() {
    if n > 1000 {
        break
    }
    fmt.Println(n)
}
```

### Backward Iteration

```go
// Already in standard library: slices.Backward
func Backward[E any](s []E) iter.Seq2[int, E] {
    return func(yield func(int, E) bool) {
        for i := len(s) - 1; i >= 0; i-- {
            if !yield(i, s[i]) {
                return
            }
        }
    }
}

for i, v := range slices.Backward(mySlice) {
    fmt.Println(i, v)
}
```

### Recursive Iterator (Tree Traversal)

```go
type Tree[E any] struct {
    Val         E
    Left, Right *Tree[E]
}

func (t *Tree[E]) Inorder() iter.Seq[E] {
    return func(yield func(E) bool) {
        t.inorder(yield)
    }
}

func (t *Tree[E]) inorder(yield func(E) bool) bool {
    if t == nil {
        return true
    }
    return t.Left.inorder(yield) &&
        yield(t.Val) &&
        t.Right.inorder(yield)
}

// Usage
for val := range tree.Inorder() {
    fmt.Println(val)
}
```

### Pull Iterators

```go
// Convert push iterator to pull iterator
next, stop := iter.Pull(Fibonacci())
defer stop()

for i := 0; i < 10; i++ {
    val, ok := next()
    if !ok {
        break
    }
    fmt.Println(val)
}
```

### Standard Library Iterator Functions (Go 1.23+)

```go
import (
    "maps"
    "slices"
    "strings"
)

// slices package
for i, v := range slices.All(mySlice) { ... }
for i, v := range slices.Backward(mySlice) { ... }
collected := slices.Collect(myIterator)
sorted := slices.Sorted(myIterator)

// maps package
for k, v := range maps.All(myMap) { ... }
keys := slices.Collect(maps.Keys(myMap))
vals := slices.Collect(maps.Values(myMap))

// strings package
for part := range strings.SplitSeq("a-b-c", "-") { ... }
```

## Range Over Integers (Go 1.22+)

```go
// Range over integers — cleaner than classic for loop
for i := range 10 {
    fmt.Println(i)  // 0, 1, 2, ..., 9
}

// Replaces:
// for i := 0; i < 10; i++ { ... }
```

## Loop Variable Semantics (Go 1.22+)

```go
// Go 1.22+: Loop variables are per-iteration scoped
// No more accidental closure bugs!
for _, v := range values {
    go func() {
        fmt.Println(v)  // SAFE in Go 1.22+ (each iteration gets its own v)
    }()
}

// Before Go 1.22, you needed:
// v := v  // capture loop variable
```

## errors.Join (Go 1.20+)

```go
// Combine multiple errors into one
func validateUser(u User) error {
    var errs []error

    if u.Name == "" {
        errs = append(errs, errors.New("name is required"))
    }
    if u.Email == "" {
        errs = append(errs, errors.New("email is required"))
    }
    if u.Age < 0 {
        errs = append(errs, errors.New("age must be non-negative"))
    }

    return errors.Join(errs...)  // nil if no errors
}

// errors.Is works on joined errors
err := errors.Join(ErrNotFound, ErrTimeout)
errors.Is(err, ErrNotFound)  // true
errors.Is(err, ErrTimeout)   // true
```

## cmp Package (Go 1.21+)

```go
import "cmp"

// cmp.Ordered constraint — replaces x/exp/constraints.Ordered
func Min[T cmp.Ordered](a, b T) T {
    return min(a, b)  // builtin min/max added in Go 1.21
}

// cmp.Compare — three-way comparison
cmp.Compare(1, 2)    // -1
cmp.Compare(2, 2)    //  0
cmp.Compare(3, 2)    // +1

// cmp.Or — returns first non-zero value
name := cmp.Or(userInput, envVar, "default")
```

## Builtin min/max (Go 1.21+)

```go
// No more writing your own min/max!
x := min(3, 5)        // 3
y := max(3, 5)        // 5
z := min(1, 2, 3, 4)  // 1 — variadic
```
