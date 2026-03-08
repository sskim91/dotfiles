# Observability & HTTP Clients

## Structured Logging

### Built-in Structured Logging (Spring Boot 3.4+)

Spring Boot 3.4+는 별도 의존성 없이 구조화된 로깅을 지원한다.

```yaml
# application.yml — 한 줄로 JSON 구조화 로깅 활성화
logging:
  structured:
    format:
      console: ecs        # Elastic Common Schema
      # console: logstash  # Logstash JSON format
      # console: gelf      # Graylog Extended Log Format
```

**지원 포맷:**

| Format | Property Value | Use With |
|--------|---------------|----------|
| Elastic Common Schema | `ecs` | ELK Stack (Elasticsearch) |
| Logstash JSON | `logstash` | Logstash pipeline |
| Graylog Extended | `gelf` | Graylog |

Stack trace 커스터마이징 (Spring Boot 3.5+):
```yaml
logging:
  structured:
    json:
      stacktrace:
        max-length: 2048
        # format: short
```

> **Note:** Built-in 구조화 로깅 사용 시 `logstash-logback-encoder` 의존성 불필요.
> 기존 `logback-spring.xml` 커스텀 설정은 아래 MDC 패턴 참조.

### MDC Filter for Request Tracing

```java
@Component
public class MdcFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
            FilterChain chain) throws ServletException, IOException {
        String requestId = Optional.ofNullable(req.getHeader("X-Request-ID"))
            .orElse(UUID.randomUUID().toString().substring(0, 8));
        MDC.put("requestId", requestId);
        MDC.put("method", req.getMethod());
        MDC.put("uri", req.getRequestURI());
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.clear();
        }
    }
}
```

### Logback Configuration

```xml
<!-- logback-spring.xml -->
<configuration>
  <springProfile name="prod">
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
      <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
    </appender>
    <root level="INFO">
      <appender-ref ref="STDOUT"/>
    </root>
  </springProfile>

  <springProfile name="local">
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
      <encoder>
        <pattern>%d{HH:mm:ss} [%thread] %-5level %logger{36} [%X{requestId}] - %msg%n</pattern>
      </encoder>
    </appender>
    <root level="DEBUG">
      <appender-ref ref="STDOUT"/>
    </root>
  </springProfile>
</configuration>
```

### Logging Best Practices

```java
@Service
public class PaymentService {
    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    public PaymentResult process(Long orderId, BigDecimal amount) {
        log.info("payment_start orderId={} amount={}", orderId, amount);
        try {
            PaymentResult result = gateway.charge(amount);
            log.info("payment_success orderId={} txId={}", orderId, result.transactionId());
            return result;
        } catch (PaymentException ex) {
            log.error("payment_failed orderId={} reason={}", orderId, ex.getMessage(), ex);
            throw ex;
        }
    }
}
```

**Rules:**
- Use structured key=value format for machine parsing
- Never log secrets, tokens, passwords, PII
- `log.error` with exception as last argument (stack trace captured)
- Avoid string concatenation in log — use `{}` placeholders

## Actuator & Micrometer

### Configuration

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: when_authorized
  metrics:
    tags:
      application: ${spring.application.name}
```

### Custom Metrics

```java
@Service
public class OrderService {
    private final Counter orderCounter;
    private final Timer orderTimer;

    public OrderService(MeterRegistry registry, /* other deps */) {
        this.orderCounter = Counter.builder("orders.created")
            .description("Number of orders created")
            .tag("type", "standard")
            .register(registry);
        this.orderTimer = Timer.builder("orders.processing")
            .description("Order processing duration")
            .register(registry);
    }

    public Order create(CreateOrderRequest req) {
        return orderTimer.record(() -> {
            Order order = // create logic
            orderCounter.increment();
            return order;
        });
    }
}
```

### Custom Health Indicator

```java
@Component
public class ExternalApiHealthIndicator implements HealthIndicator {
    private final ExternalApiClient client;

    @Override
    public Health health() {
        try {
            client.ping();
            return Health.up()
                .withDetail("service", "external-api")
                .build();
        } catch (Exception ex) {
            return Health.down()
                .withDetail("service", "external-api")
                .withException(ex)
                .build();
        }
    }
}
```

### Kubernetes Health Probes

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true     # Enables /actuator/health/liveness, /actuator/health/readiness
      group:
        liveness:
          include: livenessState
        readiness:
          include: readinessState,db,redis
```

K8s manifest:
```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 10
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 5
```

### OpenTelemetry & @Observed

Spring Boot는 Micrometer Observation을 통해 OTel을 자동 구성한다.

```yaml
# application.yml
management:
  tracing:
    sampling:
      probability: 1.0     # 0.0 ~ 1.0 (production: 0.1 권장)
  otlp:
    tracing:
      endpoint: http://localhost:4318/v1/traces
  observations:
    annotations:
      enabled: true         # @Observed, @Timed, @Counted 활성화
    key-values:
      region: ap-northeast-2
```

```java
// Declarative observation — Spring이 자동으로 메트릭+트레이스 생성
@Observed(name = "order.process", contextualName = "process-order")
public Order process(Long orderId) {
    // business logic
}
```

> **주의:** Spring MVC controllers, Spring Data repositories는 이미 자동 instrumented.
> 이런 클래스에 `@Observed`를 추가하면 **중복 observation** 발생.

### Key Actuator Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/actuator/health` | Liveness/readiness checks |
| `/actuator/health/liveness` | K8s liveness probe (requires probes.enabled) |
| `/actuator/health/readiness` | K8s readiness probe |
| `/actuator/metrics` | All registered metrics |
| `/actuator/prometheus` | Prometheus scrape format |
| `/actuator/info` | App info (git, build) |

## HTTP Clients (Spring Boot 3.2+)

### RestClient (Imperative)

Replacement for `RestTemplate`. Fluent API with better error handling.

```java
@Configuration
public class HttpClientConfig {

    @Bean
    public RestClient paymentClient(RestClient.Builder builder) {
        return builder
            .baseUrl("https://api.payment.example.com")
            .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
            .requestInterceptor((req, body, execution) -> {
                req.getHeaders().set("X-API-Key", apiKey);
                return execution.execute(req, body);
            })
            .defaultStatusHandler(HttpStatusCode::is4xxClientError, (req, res) -> {
                throw new ExternalApiException("Payment API error: " + res.getStatusCode());
            })
            .build();
    }
}

@Service
public class PaymentClient {
    private final RestClient restClient;

    public PaymentClient(@Qualifier("paymentClient") RestClient restClient) {
        this.restClient = restClient;
    }

    public PaymentResult charge(ChargeRequest request) {
        return restClient.post()
            .uri("/charges")
            .body(request)
            .retrieve()
            .body(PaymentResult.class);
    }

    public Optional<PaymentResult> findCharge(String chargeId) {
        return restClient.get()
            .uri("/charges/{id}", chargeId)
            .retrieve()
            .body(new ParameterizedTypeReference<>() {});
    }
}
```

### HTTP Interface (Declarative, Spring Boot 3.2+)

Define API as Java interface — Spring generates the implementation.

```java
public interface PaymentApi {

    @GetExchange("/charges/{id}")
    PaymentResult getCharge(@PathVariable String id);

    @PostExchange("/charges")
    PaymentResult createCharge(@RequestBody ChargeRequest request);

    @GetExchange("/charges")
    List<PaymentResult> listCharges(
        @RequestParam("status") String status,
        @RequestParam("limit") int limit);
}

@Configuration
public class HttpInterfaceConfig {

    @Bean
    public PaymentApi paymentApi(RestClient.Builder builder) {
        RestClient client = builder
            .baseUrl("https://api.payment.example.com")
            .build();
        return HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(client))
            .build()
            .createClient(PaymentApi.class);
    }
}
```

### When to Use Which

| Client | Use When |
|--------|----------|
| `RestClient` | Dynamic URLs, complex request building, fine-grained error handling |
| HTTP Interface | Clean API contracts, multiple endpoints on same service, OpenAPI-like usage |
| `WebClient` | Reactive/WebFlux applications only |

### Retry with Resilience4j

```java
@Service
public class ResilientPaymentClient {
    private final PaymentApi paymentApi;

    @Retry(name = "payment", fallbackMethod = "fallback")
    @CircuitBreaker(name = "payment")
    public PaymentResult getCharge(String id) {
        return paymentApi.getCharge(id);
    }

    private PaymentResult fallback(String id, Exception ex) {
        log.warn("payment_fallback chargeId={} reason={}", id, ex.getMessage());
        return PaymentResult.unavailable();
    }
}
```

```yaml
# application.yml
resilience4j:
  retry:
    instances:
      payment:
        max-attempts: 3
        wait-duration: 1s
        exponential-backoff-multiplier: 2
  circuitbreaker:
    instances:
      payment:
        sliding-window-size: 10
        failure-rate-threshold: 50
        wait-duration-in-open-state: 30s
```

## References

- [Spring Boot Logging](https://docs.spring.io/spring-boot/reference/features/logging.html) — Structured logging (ECS, Logstash, GELF)
- [Spring Boot Actuator](https://docs.spring.io/spring-boot/reference/actuator/) — Production-ready features
- [Spring Boot Observability](https://docs.spring.io/spring-boot/reference/actuator/observability.html) — Micrometer + OpenTelemetry
- [Baeldung: Structured Logging in Spring Boot](https://www.baeldung.com/spring-boot-structured-logging)
