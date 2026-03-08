# Configuration & Profiles

## Type-Safe Configuration with Records

```java
@ConfigurationProperties(prefix = "app.order")
public record OrderProperties(
    @DefaultValue("20") int pageSize,
    @DefaultValue("PT30S") Duration cacheTtl,
    @NotBlank String apiKey,
    Retry retry) {

    public record Retry(
        @DefaultValue("3") int maxAttempts,
        @DefaultValue("PT1S") Duration backoff) {}
}
```

```yaml
# application.yml
app:
  order:
    page-size: 50
    cache-ttl: PT1M
    api-key: ${ORDER_API_KEY}
    retry:
      max-attempts: 5
      backoff: PT2S
```

Enable: `@EnableConfigurationProperties(OrderProperties.class)` or `@ConfigurationPropertiesScan`

### Usage in Service

```java
@Service
public class OrderService {
    private final OrderProperties props;

    public OrderService(OrderProperties props) {
        this.props = props;
    }

    public Page<Order> list(int page) {
        return repo.findAll(PageRequest.of(page, props.pageSize()));
    }
}
```

## Profile Management

### Profile Groups

```yaml
# application.yml
spring:
  profiles:
    group:
      local: "local,dev-db,mock-external"
      staging: "staging,staging-db,monitoring"
      prod: "prod,prod-db,monitoring,security"
```

Activate: `SPRING_PROFILES_ACTIVE=prod` or `--spring.profiles.active=prod`

### Profile-Specific Configuration

```yaml
# application-local.yml
spring:
  jpa:
    show-sql: true
logging:
  level:
    com.example: DEBUG

# application-prod.yml
spring:
  jpa:
    show-sql: false
logging:
  level:
    com.example: INFO
    org.springframework: WARN
```

### Profile-Conditional Beans

```java
@Configuration
@Profile("prod")
public class ProdCacheConfig {
    @Bean
    public CacheManager cacheManager(RedisConnectionFactory factory) {
        return RedisCacheManager.builder(factory)
            .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10)))
            .build();
    }
}

@Configuration
@Profile("local")
public class LocalCacheConfig {
    @Bean
    public CacheManager cacheManager() {
        return new ConcurrentMapCacheManager("orders", "products");
    }
}
```

## Externalized Configuration Hierarchy

Spring Boot loads properties in this order (later overrides earlier):

1. `application.yml` (classpath)
2. `application-{profile}.yml` (classpath)
3. `application.yml` (outside jar)
4. `application-{profile}.yml` (outside jar)
5. Environment variables (`SPRING_DATASOURCE_URL`)
6. Command-line arguments (`--server.port=9090`)

**Rule:** Secrets always via environment variables or Vault, never in yml files.

## Conditional Configuration

```java
@Configuration
public class FeatureConfig {

    @Bean
    @ConditionalOnProperty(name = "app.feature.notifications", havingValue = "true")
    public NotificationService notificationService() {
        return new NotificationService();
    }

    @Bean
    @ConditionalOnMissingBean(CacheManager.class)
    public CacheManager defaultCacheManager() {
        return new ConcurrentMapCacheManager();
    }
}
```

Common `@Conditional*` annotations:

| Annotation | Use When |
|-----------|----------|
| `@ConditionalOnProperty` | Feature toggle via config |
| `@ConditionalOnMissingBean` | Fallback bean if none defined |
| `@ConditionalOnClass` | Class available on classpath |
| `@Profile` | Specific profile active |

## References

- [Spring Boot Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html) — Property hierarchy, profiles
- [Spring Boot Configuration Properties](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties) — @ConfigurationProperties
