# Coroutines & Flow API

## Structured Concurrency

```kotlin
// coroutineScope — all children must succeed (cancels siblings on failure)
suspend fun fetchUserWithPosts(userId: String): UserWithPosts = coroutineScope {
    val user = async { api.getUser(userId) }
    val posts = async { api.getPosts(userId) }
    UserWithPosts(user.await(), posts.await())
}

// supervisorScope — children fail independently
suspend fun fetchMultiple(ids: List<String>): List<Result<Data>> = supervisorScope {
    ids.map { id ->
        async {
            try { Result.success(api.fetch(id)) }
            catch (e: Exception) { Result.failure(e) }
        }
    }.awaitAll()
}
```

**When to use which:**

| Scope | Child failure | Use case |
|-------|--------------|----------|
| `coroutineScope` | Cancels all siblings | All-or-nothing (parallel fetch) |
| `supervisorScope` | Other children continue | Independent operations (multi-source) |

## Scopes & Dispatchers

```kotlin
// Android ViewModel — use viewModelScope (auto-cancelled)
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            val data = withContext(Dispatchers.IO) {
                repository.fetchData()  // IO dispatcher
            }
            _state.value = data  // Back to Main
        }
    }
}

// Custom scope with SupervisorJob (for services)
class MyService : Service() {
    private val scope = CoroutineScope(
        Dispatchers.IO + SupervisorJob() + CoroutineExceptionHandler { _, e ->
            Log.e("MyService", "Uncaught: ${e.message}", e)
        }
    )

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
```

**Dispatchers:**

| Dispatcher | Thread pool | Use case |
|-----------|-------------|----------|
| `Dispatchers.Main` | UI thread | UI updates |
| `Dispatchers.IO` | Shared elastic pool | Network, DB, file I/O |
| `Dispatchers.Default` | CPU core count | CPU-intensive (sorting, parsing) |
| `Dispatchers.Unconfined` | Caller thread | Testing only |

## Flow Basics

```kotlin
// Cold flow — starts on collection, each collector gets fresh data
fun getUsers(): Flow<List<User>> = flow {
    val users = api.fetchUsers()
    emit(users)
    delay(5000)
    emit(api.fetchUsers())  // Refresh after 5s
}.flowOn(Dispatchers.IO)

// StateFlow — hot, always has a value, conflates
class UserStore {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()

    suspend fun refresh() {
        _users.value = api.getUsers()
    }
}

// SharedFlow — hot, configurable buffer, no initial value
class EventBus {
    private val _events = MutableSharedFlow<Event>(
        replay = 0,
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<Event> = _events.asSharedFlow()

    suspend fun emit(event: Event) { _events.emit(event) }
}
```

**StateFlow vs SharedFlow:**

| Feature | StateFlow | SharedFlow |
|---------|-----------|------------|
| Initial value | Required | Optional (replay) |
| Duplicate emission | Conflated (skips equal) | All emitted |
| Subscribers | Get current value immediately | Get only new emissions (+ replay) |
| Use case | UI state | Events, commands |

## Flow Operators

### Transformation

```kotlin
// map, filter — basic transformation
userFlow
    .filter { it.isActive }
    .map { UserDto(it.id, it.name) }

// flatMapLatest — cancel previous, switch to new (search)
searchQuery
    .debounce(300)
    .distinctUntilChanged()
    .flatMapLatest { query -> repository.search(query) }

// flatMapConcat — sequential, preserves order
eventIds
    .flatMapConcat { id -> repository.fetchEvent(id) }

// flatMapMerge — concurrent, order not guaranteed
relays.asFlow()
    .flatMapMerge(concurrency = 10) { relay -> relay.subscribe(filters) }
```

### Combination

```kotlin
// combine — re-emits when ANY source emits (latest from all)
combine(accountFlow, settingsFlow, connectivityFlow) { account, settings, conn ->
    AppState(account, settings, conn)
}

// merge — single stream from multiple sources
merge(source1, source2, source3).collect { handle(it) }

// zip — pair values in order (waits for both)
zip(requestFlow, responseFlow) { req, res -> Pair(req, res) }
```

### Hot Flow Conversion

```kotlin
// shareIn — share expensive upstream with multiple collectors
val sharedEvents: SharedFlow<Event> = repository.observeEvents()
    .shareIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        replay = 0
    )

// stateIn — convert Flow to StateFlow
val uiState: StateFlow<UiState> = repository.observeData()
    .map { UiState.Success(it) }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = UiState.Loading
    )
```

**SharingStarted strategies:**

| Strategy | Behavior |
|----------|----------|
| `Eagerly` | Start immediately, never stop |
| `Lazily` | Start on first subscriber, never stop |
| `WhileSubscribed(stopTimeout)` | Stop after last unsubscribe + timeout |

## callbackFlow

Bridge callback-based APIs to Flow:

```kotlin
// Generic pattern: wrap any callback API as Flow
fun observeConnectivity(context: Context): Flow<Boolean> = callbackFlow {
    val callback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) { trySend(true) }
        override fun onLost(network: Network) { trySend(false) }
    }

    val manager = context.getSystemService<ConnectivityManager>()!!  // Safe: always available on Android
    manager.registerDefaultNetworkCallback(callback)

    // Emit initial state
    trySend(manager.activeNetwork != null)

    // CRITICAL: always include awaitClose for cleanup
    awaitClose { manager.unregisterNetworkCallback(callback) }
}
    .distinctUntilChanged()
    .debounce(200)  // Stabilize rapid changes
    .flowOn(Dispatchers.IO)
```

**callbackFlow checklist:**
1. Register callback in flow body
2. Use `trySend()` (non-blocking) from callbacks
3. Emit initial state if applicable
4. **Always** include `awaitClose { cleanup() }`

## Backpressure

```kotlin
// buffer — decouple producer/consumer speed
fastProducer
    .buffer(capacity = 64, onBufferOverflow = BufferOverflow.DROP_OLDEST)
    .collect { slowConsumer(it) }

// conflate — skip intermediate, keep latest only (UI updates)
locationFlow
    .conflate()
    .collect { updateMap(it) }

// debounce — wait for quiet period (search input)
searchInput
    .debounce(300)
    .flatMapLatest { search(it) }

// sample — periodic sampling (sensor data)
sensorData
    .sample(1000)
    .collect { process(it) }
```

| Strategy | Behavior | Use case |
|----------|----------|----------|
| `buffer(DROP_OLDEST)` | Drop oldest in buffer | Real-time feeds |
| `buffer(DROP_LATEST)` | Drop newest emission | Priority queues |
| `buffer(SUSPEND)` | Slow down producer | Critical events (default) |
| `conflate()` | Latest only | UI updates |
| `debounce(ms)` | Wait for quiet period | Search input |
| `sample(ms)` | Periodic sampling | High-frequency sensors |

## Exception Handling

```kotlin
// Flow error handling — catch only affects UPSTREAM
repository.fetchData()
    .retry(3) { cause -> cause is IOException }
    .catch { e -> emit(emptyList()) }  // Fallback
    .collect { updateUI(it) }

// Retry with exponential backoff
fun <T> Flow<T>.retryWithBackoff(
    maxRetries: Int = 3,
    initialDelay: Long = 1000L
): Flow<T> = retryWhen { cause, attempt ->
    if (attempt >= maxRetries || cause !is IOException) false
    else {
        delay(initialDelay * (1L shl attempt.toInt()))
        true
    }
}

// Coroutine exception handling — ALWAYS rethrow CancellationException
suspend fun loadSafely(): Result<Data> = supervisorScope {
    try {
        Result.success(async { api.getData() }.await())
    } catch (e: CancellationException) {
        throw e  // Never swallow!
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```

## Cancellation

```kotlin
// Cooperative cancellation — check isActive or use yield()
suspend fun processItems(items: List<Item>) {
    for (item in items) {
        ensureActive()  // Throws CancellationException if cancelled
        process(item)
    }
}

// Timeout
val result = withTimeout(5000) {
    api.fetchData()
}

// Cleanup with NonCancellable context
suspend fun withCleanup() {
    try {
        longRunningTask()
    } finally {
        withContext(NonCancellable) {
            cleanup()  // Always runs, even if cancelled
        }
    }
}
```

## Testing

### runTest — standard coroutine testing

```kotlin
@Test
fun `loads user successfully`() = runTest {
    val viewModel = UserViewModel(FakeRepository())

    viewModel.loadUser("123")
    advanceUntilIdle()  // Run all pending coroutines

    assertEquals(UiState.Success(expectedUser), viewModel.state.value)
}

@Test
fun `debounce triggers after delay`() = runTest {
    val viewModel = SearchViewModel()

    viewModel.search("a")
    advanceTimeBy(100)
    viewModel.search("ab")
    advanceTimeBy(100)
    viewModel.search("abc")
    advanceTimeBy(300)  // Debounce completes

    assertEquals(listOf("abc"), viewModel.searchQueries)
}
```

**Time control:**

| Function | Effect |
|----------|--------|
| `advanceTimeBy(ms)` | Move virtual time forward |
| `advanceUntilIdle()` | Run all pending work |
| `runCurrent()` | Run only currently scheduled tasks |

### Turbine — Flow testing library

```kotlin
@Test
fun `flow emits expected sequence`() = runTest {
    repository.observeUsers().test {
        assertEquals(UiState.Loading, awaitItem())
        assertEquals(UiState.Success(users), awaitItem())
        awaitComplete()
    }
}

@Test
fun `error handling emits fallback`() = runTest {
    val errorFlow = flow {
        emit(1)
        throw IOException("Network error")
    }.catch { emit(-1) }

    errorFlow.test {
        assertEquals(1, awaitItem())
        assertEquals(-1, awaitItem())
        awaitComplete()
    }
}
```

**Turbine assertions:**

| Function | Purpose |
|----------|---------|
| `awaitItem()` | Get next emission or fail |
| `awaitComplete()` | Verify flow completed |
| `awaitError()` | Verify flow threw exception |
| `expectNoEvents()` | Assert no emissions |
| `cancelAndIgnoreRemainingEvents()` | Stop test |

### Best practices

1. Use `runTest` for all coroutine tests — provides virtual time
2. Use **Turbine** for Flow testing — clearer assertions
3. Create **fakes over mocks** — simpler, more realistic
4. Test both success and error paths
5. Test cancellation behavior — verify cleanup happens

## Quick Reference

| Pattern | Use case |
|---------|----------|
| `launch` | Fire-and-forget coroutine |
| `async/await` | Parallel computation with result |
| `flow { }` | Cold stream of values |
| `StateFlow` | Hot flow with current state |
| `SharedFlow` | Hot flow for events |
| `callbackFlow` | Bridge callbacks to Flow |
| `withContext` | Switch dispatcher |
| `supervisorScope` | Independent child failures |
| `coroutineScope` | All children must succeed |
| `flowOn` | Change upstream dispatcher |
| `catch` | Handle upstream flow errors |
| `retry/retryWhen` | Retry on failure |
| `combine` | Latest from multiple flows |
| `merge` | Single stream from multiple |
| `shareIn` | Share cold flow with multiple collectors |
| `stateIn` | Convert cold flow to StateFlow |
| `buffer` | Decouple producer/consumer |
| `conflate` | Skip intermediate, keep latest |
| `debounce` | Wait for quiet period |
