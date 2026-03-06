# Modern Java API Patterns

Stream Gatherers, Sequenced Collections, and new JDK APIs (Java 21-25).

## Stream Gatherers (JEP 485, Finalized in JDK 24)

Gatherers allow **custom intermediate operations** in stream pipelines. Before Gatherers, only terminal operations could be customized via `Collector`. Now intermediate steps are pluggable too.

### Built-in Gatherers

```java
import java.util.stream.Gatherers;
```

#### `windowFixed(int size)` — Non-overlapping batches

```java
// Batch processing: split 100 items into groups of 10
List<List<String>> batches = items.stream()
    .gather(Gatherers.windowFixed(10))
    .toList();
// [[item1..10], [item11..20], ..., [item91..100]]

// Practical: batch database inserts
items.stream()
    .gather(Gatherers.windowFixed(50))
    .forEach(batch -> repository.saveAll(batch));
```

#### `windowSliding(int size)` — Overlapping sliding window

```java
// Moving average over 3 elements
List<Double> movingAvg = prices.stream()
    .gather(Gatherers.windowSliding(3))
    .map(window -> window.stream()
        .mapToDouble(Double::doubleValue)
        .average()
        .orElse(0))
    .toList();

// [1, 2, 3, 4, 5] with window 3 produces:
// [[1,2,3], [2,3,4], [3,4,5]]
```

#### `fold(Supplier, BiFunction)` — Reduce all elements to a single output

```java
// fold emits ONE element at the end (unlike scan which emits per input)
String csv = names.stream()
    .gather(Gatherers.fold(() -> new StringBuilder(), (sb, name) -> {
        if (!sb.isEmpty()) sb.append(",");
        sb.append(name);
        return sb;
    }))
    .map(StringBuilder::toString)
    .findFirst()
    .orElse("");
// Note: fold() is like reduce() but produces a Stream with one element
```

#### `scan(Supplier, BiFunction)` — Running accumulation (emits one output per input)

```java
// Running sum — scan emits each intermediate state
List<Integer> runningSum = numbers.stream()
    .gather(Gatherers.scan(() -> 0, Integer::sum))
    .toList();
// [1, 2, 3, 4, 5] -> [1, 3, 6, 10, 15]

// Running max
List<Integer> runningMax = numbers.stream()
    .gather(Gatherers.scan(() -> Integer.MIN_VALUE, Math::max))
    .toList();

// Running average — use immutable state (never mutate scan state!)
record Avg(double sum, int count) {
    double value() { return sum / count; }
}
List<Double> runningAvg = prices.stream()
    .gather(Gatherers.scan(() -> new Avg(0, 0),
        (avg, price) -> new Avg(avg.sum() + price, avg.count() + 1)))
    .map(Avg::value)
    .toList();
```

#### `mapConcurrent(int maxConcurrency, Function)` — Parallel map with backpressure

```java
// Call external API with max 10 concurrent virtual threads
List<ApiResponse> responses = urls.stream()
    .gather(Gatherers.mapConcurrent(10, url -> httpClient.fetch(url)))
    .toList();

// Process files with bounded parallelism
List<Result> results = files.stream()
    .gather(Gatherers.mapConcurrent(4, file -> parseFile(file)))
    .filter(Result::isValid)
    .toList();
```

### Custom Gatherer

A `Gatherer<T, A, R>` has four components:
- **Initializer** — creates per-stream state `A`
- **Integrator** — processes each element `T`, emits `R`
- **Combiner** — merges parallel state (optional, for parallel streams)
- **Finisher** — emits remaining elements when stream ends

#### Example: Distinct by Key

```java
// Deduplicate by a key function (keep first seen)
public static <T, K> Gatherer<T, ?, T> distinctBy(Function<T, K> keyExtractor) {
    return Gatherer.ofSequential(
        HashSet::new,  // Initializer: track seen keys
        (seen, element, downstream) -> {
            K key = keyExtractor.apply(element);
            if (seen.add(key)) {
                return downstream.push(element);  // First time seeing this key
            }
            return true;  // Skip duplicate, continue processing
        }
    );
}

// Usage: deduplicate users by email
List<User> unique = users.stream()
    .gather(distinctBy(User::email))
    .toList();
```

#### Example: Chunk by Predicate

```java
// Group consecutive elements that satisfy a predicate
public static <T> Gatherer<T, ?, List<T>> chunkWhile(BiPredicate<T, T> shouldGroup) {
    return Gatherer.ofSequential(
        () -> new ArrayList<T>(),
        (chunk, element, downstream) -> {
            if (!chunk.isEmpty() && !shouldGroup.test(chunk.getLast(), element)) {
                if (!downstream.push(List.copyOf(chunk))) return false;
                chunk.clear();
            }
            chunk.add(element);
            return true;
        },
        (chunk, downstream) -> {
            if (!chunk.isEmpty()) downstream.push(List.copyOf(chunk));
        }
    );
}

// Usage: group consecutive transactions by date
List<List<Transaction>> dailyGroups = transactions.stream()
    .sorted(Comparator.comparing(Transaction::date))
    .gather(chunkWhile((a, b) -> a.date().equals(b.date())))
    .toList();
```

#### Example: Rate Limiter

```java
// Emit at most N elements per time window
public static <T> Gatherer<T, ?, T> rateLimited(int maxPerSecond) {
    return Gatherer.ofSequential(
        () -> new long[]{0, System.nanoTime()},  // [count, windowStart]
        (state, element, downstream) -> {
            long now = System.nanoTime();
            if (now - state[1] >= 1_000_000_000L) {
                state[0] = 0;
                state[1] = now;
            }
            if (state[0] < maxPerSecond) {
                state[0]++;
                return downstream.push(element);
            }
            return true;  // Drop element (rate exceeded)
        }
    );
}
```

### Composing Gatherers

```java
// Chain gatherers for complex pipelines
List<String> result = events.stream()
    .gather(distinctBy(Event::id))                        // Deduplicate
    .gather(Gatherers.windowFixed(100))                   // Batch
    .gather(Gatherers.mapConcurrent(5, batch ->           // Parallel enrich
        enrichmentService.enrich(batch)))
    .flatMap(List::stream)
    .toList();
```

## Sequenced Collections (JEP 431, Finalized in JDK 21)

New interfaces that give **encounter-order** operations to collections.

### Interface Hierarchy

```
SequencedCollection<E> extends Collection<E>
  +-- SequencedSet<E> extends SequencedCollection<E>, Set<E>
  +-- SequencedMap<K,V> extends Map<K,V>

Existing implementations now implement these:
  List           -> SequencedCollection
  LinkedHashSet  -> SequencedSet
  SortedSet      -> SequencedSet
  LinkedHashMap  -> SequencedMap
  SortedMap      -> SequencedMap
```

### Key Operations

```java
SequencedCollection<String> list = new ArrayList<>(List.of("a", "b", "c"));

// Access first/last (no more list.get(0) / list.get(list.size()-1))
String first = list.getFirst();   // "a"
String last  = list.getLast();    // "c"

// Add first/last
list.addFirst("z");  // ["z", "a", "b", "c"]
list.addLast("d");   // ["z", "a", "b", "c", "d"]

// Remove first/last
list.removeFirst();  // removes "z"
list.removeLast();   // removes "d"

// Reversed view (NOT a copy — view backed by original)
SequencedCollection<String> reversed = list.reversed();
// Iterating reversed: "c", "b", "a"
```

### SequencedMap Operations

```java
SequencedMap<String, Integer> map = new LinkedHashMap<>();
map.put("one", 1);
map.put("two", 2);
map.put("three", 3);

// First/last entries
Map.Entry<String, Integer> first = map.firstEntry();  // one=1
Map.Entry<String, Integer> last  = map.lastEntry();   // three=3

// Poll (remove and return)
map.pollFirstEntry();  // removes and returns one=1
map.pollLastEntry();   // removes and returns three=3

// Put at position
map.putFirst("zero", 0);  // Insert at beginning
map.putLast("four", 4);   // Insert at end

// Reversed view
SequencedMap<String, Integer> reversed = map.reversed();
reversed.forEach((k, v) -> System.out.println(k + "=" + v));
// Prints: four=4, two=2, zero=0
```

### Practical Uses

```java
// Processing queue with priority items at front
SequencedCollection<Task> queue = new LinkedList<>();
queue.addFirst(urgentTask);   // Priority
queue.addLast(normalTask);    // Normal
Task next = queue.removeFirst();

// Ordered history with easy access to latest
SequencedCollection<Event> history = new ArrayList<>();
history.addLast(newEvent);
Event latest = history.getLast();
Event oldest = history.getFirst();

// Iterate recent-first
for (Event e : history.reversed()) {
    if (e.timestamp().isBefore(cutoff)) break;
    process(e);
}
```

## Other Notable JDK 21-25 APIs

### Unnamed Variables (JDK 22, Finalized)

```java
// _ can be used for any unused variable

// Try-catch
try { parse(input); } catch (ParseException _) { return fallback; }

// Enhanced for
for (var _ : collection) { count++; }

// Lambda
consumers.forEach((_, value) -> use(value));

// Switch
case SuccessResponse(_, _, var body) -> processBody(body);
```

### Flexible Constructor Bodies (Preview, JDK 22-25)

```java
// Statements BEFORE super() — validation, computation
public class PremiumAccount extends Account {
    public PremiumAccount(BigDecimal balance, String tier) {
        // Can now do work BEFORE calling super!
        if (balance.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Negative balance");
        }
        String normalizedTier = tier.toUpperCase().strip();
        super(balance, normalizedTier);  // Now call super with validated/computed values
    }
}
```

### Stable Values (Preview, JDK 25 — JEP 502)

```java
// Lazy-initialized, thread-safe constants without volatile/synchronized
// Replacement for double-checked locking pattern
// NOTE: API is preview and method names may change across JDK versions
import java.lang.StableValue;

private final StableValue<ExpensiveResource> resource = StableValue.of();

public ExpensiveResource getResource() {
    return resource.computeIfUnset(() -> new ExpensiveResource());
    // Computed at most once, cached forever, thread-safe
}
```

### Module Import Declarations (JDK 25, Finalized)

```java
// Import all public types exported by a module
import module java.base;      // Imports java.util.*, java.io.*, java.time.*, etc.
import module java.sql;       // Imports java.sql.*, javax.sql.*

// Reduces boilerplate import lists in scripts and small programs
```

### Compact Source Files (JDK 25, Finalized — JEP 512)

```java
// No need for explicit class declaration for simple programs
// File: Greeting.java — just write methods directly
import module java.base;

void main() {
    var names = List.of("Alice", "Bob", "Charlie");
    names.stream()
        .map(name -> "Hello, %s!".formatted(name))
        .forEach(IO::println);
}
// Compile & run: java Greeting.java
```

## Migration Cheat Sheet

| Legacy Pattern | Modern Java 21+ | Reference |
|---------------|-----------------|-----------|
| Visitor pattern | Sealed interface + pattern switch | DOP reference |
| `instanceof` + cast chain | Pattern matching `switch` | DOP reference |
| Strategy with interfaces | Sealed interface + records | DOP reference |
| `ThreadLocal` | `ScopedValue` | Concurrency reference |
| Thread pools for I/O | Virtual threads | Concurrency reference |
| `CompletableFuture` chains | Structured concurrency | Concurrency reference |
| `synchronized` blocks | `ReentrantLock` (for virtual threads) | Concurrency reference |
| `list.get(list.size()-1)` | `list.getLast()` | Sequenced Collections |
| Custom `Collector` for intermediate | `Gatherer` | This document |
| `for` loop batch processing | `Gatherers.windowFixed(n)` | This document |
| Imperative running totals | `Gatherers.scan()` | This document |

## Sources

- Viktor Klang — Stream Gatherers design lead, "Deep Dive into Gatherers" (inside.java)
- Stuart Marks — "Sequenced Collections - Deep Dive with the Expert" (inside.java)
- Nicolai Parlog — "All New Java Language Features Since Java 21" (inside.java)
- Nicolai Parlog — "All API Additions From Java 21 to 25" (inside.java)
- JEP 431: Sequenced Collections, JEP 485: Stream Gatherers
- JEP 492: Flexible Constructor Bodies, JEP 502: Stable Values
- JEP 511: Module Import Declarations, JEP 512: Compact Source Files
- DZone: "Stream Gatherers — Game-Changing Addition to Java 24"
