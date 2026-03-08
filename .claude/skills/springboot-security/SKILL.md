---
name: springboot-security
description: Spring Security 6+ patterns for authentication (JWT, OAuth2), authorization (@PreAuthorize), SecurityFilterChain, CORS, CSRF, security headers, password encoding, and secrets management. Use when configuring Spring Security, implementing JWT/OAuth2 auth, adding role-based access control, or hardening Spring Boot APIs. Do NOT use for general Spring Boot patterns (use springboot-patterns), JPA/data access (use jpa-patterns), or testing (use springboot-tdd).
---

# Spring Boot Security Patterns

Spring Security 6+ with lambda DSL. Deny by default, validate inputs, least privilege.

## When to Activate

- SecurityFilterChain 구성
- JWT / OAuth2 인증 구현
- @PreAuthorize 인가 규칙 추가
- CORS, CSRF, 보안 헤더 설정
- 비밀번호 인코딩, 시크릿 관리
- Rate limiting, 의존성 보안 스캔

## CRITICAL Rules

1. **Deny by default** — 명시적으로 허용한 경로만 접근 가능
2. **Never store plaintext passwords** — BCrypt(12+) 또는 Argon2 사용
3. **Never hardcode secrets** — `${ENV_VAR}` 또는 Vault
4. **Never trust X-Forwarded-For directly** — ForwardedHeaderFilter + trusted proxy 설정 필수
5. **Never concatenate SQL strings** — parameterized query 또는 Spring Data 사용
6. **Never log tokens, passwords, PII** — 구조화된 로깅에서 민감 필드 제외

## SecurityFilterChain (Spring Security 6+)

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http,
            JwtAuthFilter jwtAuthFilter) throws Exception {
        return http
            .csrf(csrf -> csrf.disable()) // Stateless API — CSRF not needed
            .sessionManagement(sm ->
                sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .headers(headers -> headers
                .contentSecurityPolicy(csp ->
                    csp.policyDirectives("default-src 'self'"))
                .frameOptions(HeadersConfigurer.FrameOptionsConfig::deny))
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
```

## JWT Authentication

### Approach 1: OAuth2 Resource Server (PREFERRED)

외부 IdP(Keycloak, Auth0, Okta) 또는 자체 발급 JWT를 검증할 때 **공식 권장** 방식.
Spring Boot가 `JwtDecoder`를 자동 구성하므로 커스텀 필터가 불필요하다.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .csrf(csrf -> csrf.disable())
        .sessionManagement(sm ->
            sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2
            .jwt(Customizer.withDefaults()))
        .build();
}
```

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com/realms/myapp
          # 또는 자체 서명 키:
          # public-key-location: classpath:public.pem
```

Spring Boot가 자동으로 JWT 서명 검증, `iss`/`exp`/`aud` 클레임 검증, scope→authority 매핑을 처리한다.

### Approach 2: Custom JWT Filter (자체 토큰 발급 시)

OAuth2 인프라 없이 직접 JWT를 발급/검증해야 할 때만 사용:

```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    public JwtAuthFilter(JwtService jwtService, UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String header = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (header == null || !header.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }

        String token = header.substring(7);
        String username = jwtService.extractUsername(token);

        if (username != null
                && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails user = userDetailsService.loadUserByUsername(username);
            if (jwtService.isValid(token, user)) {
                var auth = new UsernamePasswordAuthenticationToken(
                    user, null, user.getAuthorities());
                auth.setDetails(new WebAuthenticationDetailsSource()
                    .buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(auth);
            }
        }
        chain.doFilter(request, response);
    }
}
```

### JWT Service

```java
@Service
public class JwtService {
    @Value("${app.jwt.secret}")
    private String secret;

    @Value("${app.jwt.expiration:PT1H}")
    private Duration expiration;

    public String generateToken(UserDetails user) {
        return Jwts.builder()
            .subject(user.getUsername())
            .issuedAt(new Date())
            .expiration(Date.from(Instant.now().plus(expiration)))
            .signWith(getSigningKey())
            .compact();
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public boolean isValid(String token, UserDetails user) {
        return extractUsername(token).equals(user.getUsername())
            && !isExpired(token);
    }

    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
    }
}
```

## JWT Role Mapping (Custom Claims)

IdP의 JWT에 커스텀 roles 클레임이 있을 때:

```java
@Bean
public JwtAuthenticationConverter jwtAuthConverter() {
    JwtGrantedAuthoritiesConverter converter = new JwtGrantedAuthoritiesConverter();
    converter.setAuthorityPrefix("ROLE_");
    converter.setAuthoritiesClaimName("roles"); // JWT의 roles 클레임 매핑

    JwtAuthenticationConverter authConverter = new JwtAuthenticationConverter();
    authConverter.setJwtGrantedAuthoritiesConverter(converter);
    return authConverter;
}

// SecurityFilterChain에서 사용
.oauth2ResourceServer(oauth2 -> oauth2
    .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter())))
```

## Method Security

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping
    public List<OrderDto> listAll() { /* ... */ }

    @PreAuthorize("@authz.isOwner(#id, authentication)")
    @GetMapping("/{id}")
    public OrderDto getById(@PathVariable Long id) { /* ... */ }

    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) { /* ... */ }
}

@Component("authz")
public class AuthorizationService {
    private final OrderRepository orderRepo;

    public boolean isOwner(Long orderId, Authentication auth) {
        return orderRepo.findById(orderId)
            .map(order -> order.getUserId().equals(getUserId(auth)))
            .orElse(false);
    }
}
```

## CORS Configuration

```java
@Bean
public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://app.example.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
    config.setAllowCredentials(true);
    config.setMaxAge(3600L);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return source;
}
```

**Rules:**
- Production에서 `*` origin 금지
- `allowCredentials(true)` 사용 시 specific origin 필수
- Security filter level에서 설정 (controller-level 아님)

## CSRF Strategy

| App Type | CSRF | Reason |
|----------|------|--------|
| Stateless API (JWT/Bearer) | Disable | Token itself prevents CSRF |
| Session-based web app | Enable | Browser auto-sends cookies |
| Mixed (API + web) | Enable for web paths | Selective protection |

```java
// Stateless API
http.csrf(csrf -> csrf.disable());

// Session-based with SPA
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    .csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler()));
```

## Secrets Management

```yaml
# BAD
spring:
  datasource:
    password: mySecretPassword123

# GOOD: Environment variable
spring:
  datasource:
    password: ${DB_PASSWORD}

# GOOD: Spring Cloud Vault
spring:
  cloud:
    vault:
      uri: https://vault.example.com
      token: ${VAULT_TOKEN}
      kv:
        backend: secret
        default-context: myapp
```

## Rate Limiting

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        // SECURITY: getRemoteAddr() is correct only when ForwardedHeaderFilter
        // is configured with trusted proxy. See springboot-patterns for details.
        String clientIp = request.getRemoteAddr();
        Bucket bucket = buckets.computeIfAbsent(clientIp, k ->
            Bucket.builder()
                .addLimit(Bandwidth.classic(100,
                    Refill.greedy(100, Duration.ofMinutes(1))))
                .build());

        if (bucket.tryConsume(1)) {
            chain.doFilter(request, response);
        } else {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.getWriter().write(
                "{\"type\":\"about:blank\",\"title\":\"Too Many Requests\",\"status\":429}");
        }
    }
}
```

## Input Validation

```java
// BAD: No validation
@PostMapping("/users")
public User create(@RequestBody UserDto dto) { return userService.create(dto); }

// GOOD: Validated DTO
public record CreateUserRequest(
    @NotBlank @Size(max = 100) String name,
    @NotBlank @Email String email,
    @NotNull @Min(0) @Max(150) Integer age) {}

@PostMapping("/users")
public ResponseEntity<UserDto> create(@Valid @RequestBody CreateUserRequest req) {
    return ResponseEntity.status(HttpStatus.CREATED).body(userService.create(req));
}
```

## SQL Injection Prevention

```java
// BAD: String concatenation
@Query(value = "SELECT * FROM users WHERE name = '" + name + "'", nativeQuery = true)

// GOOD: Parameterized query
@Query(value = "SELECT * FROM users WHERE name = :name", nativeQuery = true)
List<User> findByName(@Param("name") String name);

// GOOD: Spring Data derived query (auto-parameterized)
List<User> findByEmailAndActiveTrue(String email);
```

## HTTPS Enforcement

```yaml
# application.yml — SSL 설정
server:
  port: 8443
  ssl:
    bundle: my-server   # SSL Bundles (Spring Boot 3.1+)
    # 또는 전통적 방식:
    # key-store: classpath:keystore.p12
    # key-store-password: ${SSL_KEYSTORE_PASSWORD}
    # key-store-type: PKCS12
```

HTTP → HTTPS 리다이렉트:
```java
// SecurityFilterChain 내에서
http.requiresChannel(channel ->
    channel.anyRequest().requiresSecure());
```

## Security Checklist

- [ ] Auth tokens validated with expiry and signature
- [ ] Authorization guards on every sensitive endpoint
- [ ] All user inputs validated (@Valid + DTO constraints)
- [ ] No string-concatenated SQL
- [ ] CSRF posture matches app type (stateless vs session)
- [ ] Secrets externalized, none in source
- [ ] Security headers configured (CSP, X-Frame-Options)
- [ ] CORS restricted to known origins
- [ ] Rate limiting on public/expensive endpoints
- [ ] Dependencies scanned for CVEs (OWASP/Snyk)
- [ ] No secrets, tokens, PII in logs
- [ ] HTTPS enforced in production

## References

- [Spring Security Reference](https://docs.spring.io/spring-security/reference/) — Official documentation
- [Spring Security OAuth2 Resource Server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/) — JWT validation
- [Spring Boot Security Properties](https://docs.spring.io/spring-boot/appendix/application-properties/#appendix.application-properties.security) — All security properties
- [Baeldung: Spring Security](https://www.baeldung.com/security-spring) — Tutorials
