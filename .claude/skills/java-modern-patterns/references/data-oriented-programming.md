# Data-Oriented Programming in Java

Patterns for modeling domains with records, sealed types, and pattern matching (Java 21+).

> "The goal of data-oriented programming is to model data as data, and to make it easy to work with plain data."
> — Brian Goetz, Java Language Architect

## Core Concept: Algebraic Data Types (ADTs)

ADTs combine two primitives:
- **Product types** (records): aggregate named components — `record Point(int x, int y)`
- **Sum types** (sealed interfaces): fixed set of alternatives — `sealed interface Shape permits Circle, Rect`

Together they form the "sum of products" pattern — the foundation of data-oriented Java.

### Properties of Java ADTs

| Property | Description |
|----------|-------------|
| **Nominal** | Types and components have human-readable names |
| **Immutable** | Records are transparent, immutable data carriers |
| **Exhaustive** | Sealed hierarchies enable compiler-checked completeness |
| **Deconstructible** | Record patterns extract components in switch/instanceof |
| **Serializable** | Records serialize/deserialize predictably |

## Pattern Catalog

### 1. Result Type Pattern

Replace exceptions or nullable returns with explicit success/failure modeling.

```java
public sealed interface Result<T> permits Result.Ok, Result.Err {
    record Ok<T>(T value) implements Result<T> {}
    record Err<T>(String message, Exception cause) implements Result<T> {}

    // Convenience factories
    static <T> Result<T> ok(T value) { return new Ok<>(value); }
    static <T> Result<T> err(String msg) { return new Err<>(msg, null); }
    static <T> Result<T> err(String msg, Exception e) { return new Err<>(msg, e); }
}

// Usage
public Result<User> findUser(String email) {
    try {
        User user = repository.findByEmail(email);
        return user != null ? Result.ok(user) : Result.err("User not found: " + email);
    } catch (DataAccessException e) {
        return Result.err("Database error", e);
    }
}

// Caller uses pattern matching (null inside record pattern requires guard)
String response = switch (findUser(email)) {
    case Result.Ok(var user)                              -> "Found: " + user.name();
    case Result.Err(var msg, var cause) when cause == null -> "Not found: " + msg;
    case Result.Err(var msg, var cause)                    -> "Error: " + msg + " (" + cause.getMessage() + ")";
};
```

### 2. Command Pattern with ADTs

Model commands/events as sealed hierarchies instead of visitor or strategy patterns.

```java
public sealed interface Command permits Command.CreateOrder, Command.CancelOrder,
        Command.UpdateQuantity, Command.ApplyDiscount {
    record CreateOrder(String customerId, List<LineItem> items) implements Command {}
    record CancelOrder(String orderId, String reason) implements Command {}
    record UpdateQuantity(String orderId, String itemId, int newQty) implements Command {}
    record ApplyDiscount(String orderId, BigDecimal percentage) implements Command {}
}

public record LineItem(String productId, int quantity, BigDecimal price) {}

// Command handler — behavior OUTSIDE the data hierarchy
public OrderResult handle(Command cmd) {
    return switch (cmd) {
        case CreateOrder(var custId, var items)         -> createOrder(custId, items);
        case CancelOrder(var orderId, var reason)       -> cancelOrder(orderId, reason);
        case UpdateQuantity(var oid, var iid, var qty)  -> updateQty(oid, iid, qty);
        case ApplyDiscount(var oid, var pct)            -> applyDiscount(oid, pct);
    };
}
```

### 3. State Machine Pattern

Model finite states as sealed types with allowed transitions.

```java
public sealed interface OrderState permits OrderState.Draft, OrderState.Submitted,
        OrderState.Approved, OrderState.Shipped, OrderState.Cancelled {
    record Draft(List<LineItem> items) implements OrderState {}
    record Submitted(List<LineItem> items, Instant submittedAt) implements OrderState {}
    record Approved(List<LineItem> items, String approver) implements OrderState {}
    record Shipped(String trackingNumber, Instant shippedAt) implements OrderState {}
    record Cancelled(String reason, Instant cancelledAt) implements OrderState {}
}

// OrderEvent should also be sealed for exhaustiveness
public sealed interface OrderEvent permits Submit, Approve, Cancel, Ship {}
record Submit() implements OrderEvent {}
record Approve(String approver) implements OrderEvent {}
record Cancel(String reason) implements OrderEvent {}
record Ship(String tracking) implements OrderEvent {}

public OrderState transition(OrderState current, OrderEvent event) {
    return switch (current) {
        case Draft(var items) -> switch (event) {
            case Submit()           -> new Submitted(items, Instant.now());
            case Cancel(var reason) -> new Cancelled(reason, Instant.now());
            case Approve _, Ship _  -> throw new IllegalStateException("Cannot %s from Draft".formatted(event));
        };
        case Submitted(var items, _) -> switch (event) {
            case Approve(var approver) -> new Approved(items, approver);
            case Cancel(var reason)    -> new Cancelled(reason, Instant.now());
            case Submit _, Ship _      -> throw new IllegalStateException("Cannot %s from Submitted".formatted(event));
        };
        case Approved(_, _) -> switch (event) {
            case Ship(var tracking)          -> new Shipped(tracking, Instant.now());
            case Submit _, Approve _, Cancel _ -> throw new IllegalStateException("Cannot %s from Approved".formatted(event));
        };
        case Shipped _    -> throw new IllegalStateException("Terminal state: Shipped");
        case Cancelled _  -> throw new IllegalStateException("Terminal state: Cancelled");
    };
}
```

### 4. Expression Tree Pattern

Model recursive data structures with nested ADTs.

```java
public sealed interface Expr permits Expr.Num, Expr.Add, Expr.Mul, Expr.Neg {
    record Num(double value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}
    record Neg(Expr operand) implements Expr {}
}

public double evaluate(Expr expr) {
    return switch (expr) {
        case Num(var v)          -> v;
        case Add(var l, var r)   -> evaluate(l) + evaluate(r);
        case Mul(var l, var r)   -> evaluate(l) * evaluate(r);
        case Neg(var e)          -> -evaluate(e);
    };
}

public String prettyPrint(Expr expr) {
    return switch (expr) {
        case Num(var v)        -> String.valueOf(v);
        case Add(var l, var r) -> "(%s + %s)".formatted(prettyPrint(l), prettyPrint(r));
        case Mul(var l, var r) -> "(%s * %s)".formatted(prettyPrint(l), prettyPrint(r));
        case Neg(var e)        -> "-(%s)".formatted(prettyPrint(e));
    };
}
```

### 5. API Response Pattern

Model HTTP/API responses as ADTs for type-safe handling.

```java
public sealed interface ApiResponse<T> permits ApiResponse.Success,
        ApiResponse.NotFound, ApiResponse.ValidationError, ApiResponse.ServerError {
    record Success<T>(T data, Map<String, String> headers) implements ApiResponse<T> {}
    record NotFound<T>(String resource, String identifier) implements ApiResponse<T> {}
    record ValidationError<T>(List<FieldError> errors) implements ApiResponse<T> {}
    record ServerError<T>(String message, String traceId) implements ApiResponse<T> {}
}

public record FieldError(String field, String message) {}

// Controller maps ADT to HTTP response
public ResponseEntity<?> toHttp(ApiResponse<?> response) {
    return switch (response) {
        case Success(var data, var headers) -> {
            var builder = ResponseEntity.ok();
            headers.forEach(builder::header);
            yield builder.body(data);
        }
        case NotFound(var res, var id)       -> ResponseEntity.status(404)
            .body(Map.of("error", "%s not found: %s".formatted(res, id)));
        case ValidationError(var errors)     -> ResponseEntity.badRequest().body(errors);
        case ServerError(var msg, var trace) -> ResponseEntity.status(500)
            .body(Map.of("error", msg, "traceId", trace));
    };
}
```

## Refactoring from OOP to DOP

### Before: Classic OOP with Visitor

```java
// Scattered behavior across many files
interface Shape { double area(); String describe(); }
class Circle implements Shape {
    double radius;
    public double area() { return Math.PI * radius * radius; }
    public String describe() { return "Circle r=" + radius; }
}
class Rect implements Shape {
    double w, h;
    public double area() { return w * h; }
    public String describe() { return "Rect %sx%s".formatted(w, h); }
}
// Adding new operations requires modifying every class
```

### After: Data-Oriented with ADTs

```java
// Data definition — stable, rarely changes
sealed interface Shape permits Circle, Rect {}
record Circle(Point center, double radius) implements Shape {}
record Rect(Point topLeft, double width, double height) implements Shape {}
record Point(double x, double y) {}

// Operations — easy to add without touching data classes
class ShapeOps {
    static double area(Shape s) {
        return switch (s) {
            case Circle(_, var r) -> Math.PI * r * r;
            case Rect(_, var w, var h) -> w * h;
        };
    }

    static String describe(Shape s) {
        return switch (s) {
            case Circle(var c, var r) -> "Circle at (%s,%s) r=%s".formatted(c.x(), c.y(), r);
            case Rect(var tl, var w, var h) -> "Rect at (%s,%s) %sx%s".formatted(tl.x(), tl.y(), w, h);
        };
    }
}
```

**When to choose DOP over OOP:**
- Types are **stable** (rarely add new variants), operations **change frequently** → DOP
- Types **change frequently** (open for extension), operations are **stable** → OOP (polymorphism)

## Record Best Practices

### Compact Constructors for Validation

```java
public record Email(String value) {
    public Email {
        if (value == null || !value.contains("@")) {
            throw new IllegalArgumentException("Invalid email: " + value);
        }
        value = value.toLowerCase().strip();  // Normalization
    }
}
```

### Records as Value Objects

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount, "amount must not be null");
        Objects.requireNonNull(currency, "currency must not be null");
        if (amount.scale() > currency.getDefaultFractionDigits()) {
            amount = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.HALF_UP);
        }
    }

    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch: %s vs %s".formatted(currency, other.currency));
        }
        return new Money(this.amount.add(other.amount), currency);
    }
}
```

### Records with Interfaces

```java
// Records can implement interfaces — but NOT extend classes
public interface Identifiable { String id(); }
public interface Timestamped { Instant createdAt(); }

public record UserEvent(String id, String userId, String action, Instant createdAt)
        implements Identifiable, Timestamped {}
```

## Pattern Matching Advanced Patterns

### Nested Deconstruction

```java
record Address(String city, String country) {}
record Customer(String name, Address address) {}

String greeting(Customer c) {
    return switch (c) {
        case Customer(var name, Address(_, "KR")) -> "안녕하세요, " + name;
        case Customer(var name, Address(_, "US")) -> "Hello, " + name;
        case Customer(var name, _)                -> "Hi, " + name;
    };
}
```

### Guards for Complex Conditions

```java
String classify(Object obj) {
    return switch (obj) {
        case Integer i when i < 0           -> "negative int";
        case Integer i when i == 0          -> "zero";
        case Integer i                      -> "positive int: " + i;
        case String s when s.isBlank()      -> "blank string";
        case String s when s.length() > 100 -> "long string (%d chars)".formatted(s.length());
        case String s                       -> "string: " + s;
        case null                           -> "null";
        default                             -> "other: " + obj.getClass().getSimpleName();
    };
}
```

### Unnamed Patterns in Practice

```java
// Only need the amount, not the transaction ID
case Success(_, var amount) -> process(amount);

// Catch and suppress, don't need the exception variable
try { resource.close(); } catch (IOException _) {}

// Only care about map values
cache.forEach((_, value) -> evictIfExpired(value));

// Record deconstruction where you only need some fields
record Config(String host, int port, String user, String password, boolean ssl) {}

void connect(Config config) {
    switch (config) {
        case Config(var host, var port, _, _, true)  -> connectSsl(host, port);
        case Config(var host, var port, _, _, false)  -> connectPlain(host, port);
    }
}
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| `default` on sealed switch | Loses exhaustiveness checking | Remove `default`; handle all subtypes explicitly |
| Mutable fields in records | Breaks immutability contract | Use immutable collections; create new records for changes |
| `@Data` on records (Lombok) | Redundant; conflicts with record semantics | Records already have equals/hashCode/toString |
| Giant records (10+ fields) | Hard to read and maintain | Split into nested records or compose with interfaces |
| Sealed type with `non-sealed` everywhere | Defeats the purpose of sealing | Keep hierarchy tight; use `non-sealed` only for extension points |
| OOP-style methods inside records | Mixes data and behavior | Keep records as data; put behavior in separate service/utility |

## Sources

- Brian Goetz, "Data Oriented Programming in Java" — infoq.com/articles/data-oriented-programming-java
- Brian Goetz, "Java Feature Spotlight: Sealed Classes" — infoq.com/articles/java-sealed-classes
- Brian Goetz, "Java Feature Spotlight: Pattern Matching" — infoq.com/articles/java-pattern-matching
- InfoQ, "Java Explores Carrier Classes to Extend Data-Oriented Programming" (2026)
- Jose Paumard, "Clean Code with Records, Sealed Classes and Pattern Matching" — inside.java
- JEP 440: Record Patterns, JEP 441: Pattern Matching for switch
- JEP 456: Unnamed Variables & Patterns
