# Go Testing Patterns

## Table-Driven Tests

The standard Go testing pattern. Enables comprehensive coverage with minimal code.

### Basic Pattern

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -1, -2, -3},
        {"zero values", 0, 0, 0},
        {"mixed signs", -1, 1, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

### With Error Cases

```go
func TestParseConfig(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *Config
        wantErr bool
    }{
        {
            name:  "valid config",
            input: `{"host": "localhost", "port": 8080}`,
            want:  &Config{Host: "localhost", Port: 8080},
        },
        {
            name:    "invalid JSON",
            input:   `{invalid}`,
            wantErr: true,
        },
        {
            name:    "empty input",
            input:   "",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseConfig(tt.input)

            if tt.wantErr {
                if err == nil {
                    t.Error("expected error, got nil")
                }
                return
            }

            if err != nil {
                t.Fatalf("unexpected error: %v", err)
            }

            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("got %+v; want %+v", got, tt.want)
            }
        })
    }
}
```

## Parallel Tests

```go
func TestParallel(t *testing.T) {
    tests := []struct {
        name  string
        input string
    }{
        {"case1", "input1"},
        {"case2", "input2"},
        {"case3", "input3"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()  // Run subtests concurrently
            result := Process(tt.input)
            _ = result
        })
    }
}
```

Note: As of Go 1.22, loop variable capture in closures is safe. No need for `tt := tt`.

## Test Helpers

```go
func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()  // Error reports point to caller, not this function

    db, err := sql.Open("sqlite3", ":memory:")
    if err != nil {
        t.Fatalf("open database: %v", err)
    }

    t.Cleanup(func() {
        db.Close()
    })

    if _, err := db.Exec(schema); err != nil {
        t.Fatalf("create schema: %v", err)
    }

    return db
}

// Generic assertion helpers
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v; want %v", got, want)
    }
}

func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}

func assertError(t *testing.T, err error) {
    t.Helper()
    if err == nil {
        t.Fatal("expected error, got nil")
    }
}
```

## Interface-Based Mocking

```go
// Interface at consumer
type UserStore interface {
    GetUser(ctx context.Context, id string) (*User, error)
    SaveUser(ctx context.Context, user *User) error
}

// Mock implementation
type MockUserStore struct {
    GetUserFunc  func(ctx context.Context, id string) (*User, error)
    SaveUserFunc func(ctx context.Context, user *User) error
}

func (m *MockUserStore) GetUser(ctx context.Context, id string) (*User, error) {
    return m.GetUserFunc(ctx, id)
}

func (m *MockUserStore) SaveUser(ctx context.Context, user *User) error {
    return m.SaveUserFunc(ctx, user)
}

// Usage in test
func TestUserService_GetProfile(t *testing.T) {
    mock := &MockUserStore{
        GetUserFunc: func(ctx context.Context, id string) (*User, error) {
            if id == "123" {
                return &User{ID: "123", Name: "Alice"}, nil
            }
            return nil, ErrNotFound
        },
    }

    svc := NewService(mock)

    t.Run("found", func(t *testing.T) {
        user, err := svc.GetProfile(context.Background(), "123")
        assertNoError(t, err)
        assertEqual(t, user.Name, "Alice")
    })

    t.Run("not found", func(t *testing.T) {
        _, err := svc.GetProfile(context.Background(), "999")
        if !errors.Is(err, ErrNotFound) {
            t.Errorf("got %v; want ErrNotFound", err)
        }
    })
}
```

## HTTP Handler Testing

```go
func TestGetUserHandler(t *testing.T) {
    tests := []struct {
        name       string
        method     string
        path       string
        body       string
        wantStatus int
        wantBody   string
    }{
        {
            name:       "get existing user",
            method:     http.MethodGet,
            path:       "/users/123",
            wantStatus: http.StatusOK,
            wantBody:   `{"id":"123","name":"Alice"}`,
        },
        {
            name:       "user not found",
            method:     http.MethodGet,
            path:       "/users/999",
            wantStatus: http.StatusNotFound,
        },
        {
            name:       "create user",
            method:     http.MethodPost,
            path:       "/users",
            body:       `{"name":"Bob"}`,
            wantStatus: http.StatusCreated,
        },
    }

    handler := NewHandler(/* dependencies */)

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            var body io.Reader
            if tt.body != "" {
                body = strings.NewReader(tt.body)
            }

            req := httptest.NewRequest(tt.method, tt.path, body)
            req.Header.Set("Content-Type", "application/json")
            w := httptest.NewRecorder()

            handler.ServeHTTP(w, req)

            if w.Code != tt.wantStatus {
                t.Errorf("status = %d; want %d", w.Code, tt.wantStatus)
            }

            if tt.wantBody != "" {
                got := strings.TrimSpace(w.Body.String())
                if got != tt.wantBody {
                    t.Errorf("body = %q; want %q", got, tt.wantBody)
                }
            }
        })
    }
}
```

## Golden Files

Test against expected output files stored in `testdata/`.

```go
var update = flag.Bool("update", false, "update golden files")

func TestRender(t *testing.T) {
    tests := []struct {
        name  string
        input Template
    }{
        {"simple", Template{Name: "test"}},
        {"complex", Template{Name: "test", Items: []string{"a", "b"}}},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Render(tt.input)
            golden := filepath.Join("testdata", tt.name+".golden")

            if *update {
                os.WriteFile(golden, got, 0644)
            }

            want, err := os.ReadFile(golden)
            if err != nil {
                t.Fatalf("read golden: %v", err)
            }

            if !bytes.Equal(got, want) {
                t.Errorf("mismatch:\ngot:\n%s\nwant:\n%s", got, want)
            }
        })
    }
}

// Update golden files: go test -update ./...
```

## Benchmarks

### Basic Benchmark

```go
func BenchmarkProcess(b *testing.B) {
    data := generateTestData(1000)
    b.ResetTimer()  // Exclude setup time

    for i := 0; i < b.N; i++ {
        Process(data)
    }
    // Go 1.24+: can use `for b.Loop()` instead (prevents compiler optimization of dead code)
}

// Run: go test -bench=BenchmarkProcess -benchmem
```

### Benchmark with Different Sizes

```go
func BenchmarkSort(b *testing.B) {
    for _, size := range []int{100, 1000, 10000} {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := generateRandomSlice(size)
            b.ResetTimer()

            for i := 0; i < b.N; i++ {
                tmp := make([]int, len(data))
                copy(tmp, data)
                sort.Ints(tmp)
            }
        })
    }
}
```

### Comparing Implementations

```go
func BenchmarkStringConcat(b *testing.B) {
    parts := []string{"hello", "world", "foo", "bar", "baz"}

    b.Run("plus", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            var s string
            for _, p := range parts {
                s += p
            }
            _ = s
        }
    })

    b.Run("builder", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            var sb strings.Builder
            for _, p := range parts {
                sb.WriteString(p)
            }
            _ = sb.String()
        }
    })

    b.Run("join", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            _ = strings.Join(parts, "")
        }
    })
}
```

## Fuzz Testing (Go 1.18+)

### Basic Fuzz Test

```go
func FuzzParseJSON(f *testing.F) {
    // Seed corpus — known good/edge inputs
    f.Add(`{"name": "test"}`)
    f.Add(`{"count": 123}`)
    f.Add(`[]`)
    f.Add(`""`)
    f.Add(`null`)

    f.Fuzz(func(t *testing.T, input string) {
        var result map[string]any
        err := json.Unmarshal([]byte(input), &result)
        if err != nil {
            return  // Invalid input is expected
        }

        // Property: successful parse → successful marshal
        _, err = json.Marshal(result)
        if err != nil {
            t.Errorf("Marshal failed after Unmarshal: %v", err)
        }
    })
}

// Run: go test -fuzz=FuzzParseJSON -fuzztime=30s
```

### Roundtrip Fuzz Test

```go
func FuzzEncodeDecode(f *testing.F) {
    f.Add("hello world")
    f.Add("")
    f.Add("special chars: !@#$%")

    f.Fuzz(func(t *testing.T, original string) {
        encoded := Encode(original)
        decoded, err := Decode(encoded)
        if err != nil {
            t.Fatalf("Decode(Encode(%q)) failed: %v", original, err)
        }
        if decoded != original {
            t.Errorf("roundtrip: got %q; want %q", decoded, original)
        }
    })
}
```

## TestMain for Setup/Teardown

```go
func TestMain(m *testing.M) {
    // Setup: run before all tests
    db := setupDatabase()

    // Run tests
    code := m.Run()

    // Teardown: run after all tests
    db.Close()

    os.Exit(code)
}
```

## Testing Commands

```bash
# All tests
go test ./...

# Verbose output
go test -v ./...

# Specific test by name
go test -run TestGetUser ./...

# Subtest by name
go test -run "TestUser/Create" ./...

# Race detector
go test -race ./...

# Coverage
go test -cover -coverprofile=coverage.out ./...
go tool cover -html=coverage.out  # view in browser
go tool cover -func=coverage.out  # view by function

# Short mode (skip slow tests)
go test -short ./...

# Benchmarks
go test -bench=. -benchmem ./...

# Fuzz
go test -fuzz=FuzzXxx -fuzztime=30s ./...

# Flaky test detection (run N times)
go test -count=10 ./...

# Timeout
go test -timeout 30s ./...
```

## Coverage Targets

| Code Type | Target |
|-----------|--------|
| Critical business logic | 100% |
| Public APIs | 90%+ |
| General code | 80%+ |
| Generated/boilerplate | Exclude |

## Best Practices

**DO:**
- Use table-driven tests for comprehensive coverage
- Test behavior through public API, not private functions
- Use `t.Helper()` in all test helpers
- Use `t.Parallel()` for independent tests
- Use `t.Cleanup()` for resource cleanup
- Use meaningful test names describing the scenario
- Test error paths, not just happy paths

**DON'T:**
- Use `time.Sleep()` in tests — use channels or sync primitives
- Ignore flaky tests — fix or remove them
- Mock everything — prefer integration tests for I/O boundaries
- Test implementation details — test observable behavior
- Use `assert` libraries without consideration — standard `if/t.Errorf` is idiomatic
