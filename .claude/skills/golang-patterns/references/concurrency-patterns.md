# Go Concurrency Patterns

## Goroutine Lifecycle Management

Every goroutine must have:
1. Clear ownership (who starts it)
2. Clear shutdown path (how it stops)
3. Error propagation (how errors are reported)

## Worker Pool

```go
func WorkerPool[T any, R any](ctx context.Context, jobs <-chan T, process func(T) R, numWorkers int) <-chan R {
    results := make(chan R, numWorkers)
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobs:
                    if !ok {
                        return
                    }
                    results <- process(job)
                case <-ctx.Done():
                    return
                }
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}
```

## errgroup for Coordinated Goroutines

```go
import "golang.org/x/sync/errgroup"

func FetchAll(ctx context.Context, urls []string) ([][]byte, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([][]byte, len(urls))

    for i, url := range urls {
        g.Go(func() error {
            data, err := fetch(ctx, url)
            if err != nil {
                return fmt.Errorf("fetch %s: %w", url, err)
            }
            results[i] = data  // safe: each goroutine writes to unique index
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

Note: As of Go 1.22, loop variables are per-iteration scoped, so the `i, url := i, url` capture trick is no longer needed.

## errgroup with Concurrency Limit

```go
func ProcessAll(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(10)  // max 10 concurrent goroutines

    for _, item := range items {
        g.Go(func() error {
            return process(ctx, item)
        })
    }

    return g.Wait()
}
```

## Context for Cancellation and Timeouts

```go
func FetchWithTimeout(ctx context.Context, url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("fetch %s: %w", url, err)
    }
    defer resp.Body.Close()

    return io.ReadAll(resp.Body)
}
```

### Context Best Practices

- **First parameter**: `func DoWork(ctx context.Context, ...) error`
- **Never store in struct**: Pass through function parameters
- **Don't pass nil**: Use `context.TODO()` if unsure
- **Derive child contexts**: `context.WithCancel`, `WithTimeout`, `WithValue`
- **context.WithValue sparingly**: Only for request-scoped data (request ID, auth token), not for function parameters

## Graceful Shutdown

```go
func main() {
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
    defer stop()

    server := &http.Server{Addr: ":8080", Handler: mux}

    // Start server in goroutine
    go func() {
        if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            slog.Error("server error", "err", err)
        }
    }()

    slog.Info("server started", "addr", ":8080")

    // Wait for interrupt signal
    <-ctx.Done()
    slog.Info("shutting down...")

    // Give outstanding requests 30s to complete
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(shutdownCtx); err != nil {
        slog.Error("shutdown error", "err", err)
    }
}
```

## Avoiding Goroutine Leaks

```go
// BAD: Goroutine leaks if context cancelled — unbuffered channel blocks forever
func leaky(ctx context.Context) <-chan Result {
    ch := make(chan Result)
    go func() {
        result := expensiveWork()
        ch <- result  // blocks forever if no receiver
    }()
    return ch
}

// GOOD: Buffered channel + select on ctx.Done
func safe(ctx context.Context) <-chan Result {
    ch := make(chan Result, 1)  // buffered: won't block
    go func() {
        result := expensiveWork()
        select {
        case ch <- result:
        case <-ctx.Done():
        }
    }()
    return ch
}
```

## Channel Patterns

### Fan-out / Fan-in

```go
// Fan-out: distribute work to multiple goroutines
func fanOut[T any](input <-chan T, n int) []<-chan T {
    outputs := make([]<-chan T, n)
    for i := 0; i < n; i++ {
        ch := make(chan T)
        outputs[i] = ch
        go func() {
            defer close(ch)
            for v := range input {
                ch <- v
            }
        }()
    }
    return outputs
}

// Fan-in: merge multiple channels into one
func fanIn[T any](channels ...<-chan T) <-chan T {
    var wg sync.WaitGroup
    merged := make(chan T)

    for _, ch := range channels {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for v := range ch {
                merged <- v
            }
        }()
    }

    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}
```

### Pipeline

```go
func generate(ctx context.Context, nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case out <- n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

// Usage: pipeline composes naturally
// results := square(ctx, generate(ctx, 1, 2, 3, 4))
```

## sync Primitives

### sync.Once for Lazy Initialization

```go
type Client struct {
    once sync.Once
    conn *grpc.ClientConn
}

func (c *Client) getConn() *grpc.ClientConn {
    c.once.Do(func() {
        var err error
        c.conn, err = grpc.Dial("localhost:50051",
            grpc.WithTransportCredentials(insecure.NewCredentials()))
        if err != nil {
            panic(fmt.Sprintf("failed to connect: %v", err))
        }
    })
    return c.conn
}
```

### sync.Pool for Frequent Allocations

```go
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func Process(data []byte) []byte {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()

    buf.Write(data)
    // process...

    // IMPORTANT: Copy bytes before returning!
    // buf.Bytes() returns a reference to internal storage.
    // After defer runs (Reset + Put), another goroutine may overwrite it.
    result := make([]byte, buf.Len())
    copy(result, buf.Bytes())
    return result
}
```

### sync.Map for Concurrent Map Access

```go
// Use sync.Map ONLY when:
// 1. Keys are stable (written once, read many)
// 2. Multiple goroutines read/write disjoint key sets
// Otherwise, prefer sync.Mutex + regular map

var cache sync.Map

func Get(key string) (Value, bool) {
    v, ok := cache.Load(key)
    if !ok {
        return Value{}, false
    }
    return v.(Value), true
}

func Set(key string, val Value) {
    cache.Store(key, val)
}
```

## Rate Limiting

```go
func rateLimitedWorker(ctx context.Context, jobs <-chan Job, rps int) {
    limiter := time.NewTicker(time.Second / time.Duration(rps))
    defer limiter.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-limiter.C:
            select {
            case job, ok := <-jobs:
                if !ok {
                    return
                }
                process(job)
            case <-ctx.Done():
                return
            }
        }
    }
}
```

## Semaphore Pattern

```go
// Using a buffered channel as a semaphore
type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(Semaphore, n)
}

func (s Semaphore) Acquire() { s <- struct{}{} }
func (s Semaphore) Release() { <-s }

// Or use golang.org/x/sync/semaphore for weighted semaphore
```
