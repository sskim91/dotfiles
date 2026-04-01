---
name: springboot-verification
description: Use before opening PRs, after major refactoring, or pre-deployment for Spring Boot verification. Do NOT use for writing tests (use springboot-tdd), security implementation (use springboot-security), or general patterns (use springboot-patterns).
paths: "**/*.java, **/build.gradle*, **/pom.xml"
---

# Spring Boot Verification Loop

PR, 배포 전 검증 파이프라인. 빌드 → 정적분석 → 테스트+커버리지 → 보안스캔 → diff 리뷰.

## When to Activate

- PR 열기 전
- 대규모 리팩토링 / 의존성 업그레이드 후
- Staging/Production 배포 전
- 전체 검증 파이프라인 실행

## CRITICAL Rules

1. **Phase 순서 엄수** — 앞 단계 실패 시 즉시 중단 후 수정
2. **커버리지 80% 미만 = FAIL** — 예외 없음
3. **OWASP Critical/High CVE = FAIL** — 배포 차단
4. **System.out.println = FAIL** — Logger 사용 필수

## Phase 1: Build

```bash
# Maven
mvn -T 4 clean verify -DskipTests

# Gradle
./gradlew clean assemble -x test
```

빌드 실패 시 중단. 컴파일 에러, 리소스 누락 먼저 해결.

## Phase 2: Static Analysis

### Maven

```bash
# 개별 실행
mvn spotbugs:check
mvn pmd:check
mvn checkstyle:check

# 한번에
mvn -T 4 spotbugs:check pmd:check checkstyle:check
```

### Gradle

```bash
./gradlew checkstyleMain pmdMain spotbugsMain
```

### Common Issues to Check

```bash
# System.out.println (logger 사용해야 함)
grep -rn "System\.out\.print" src/main/ --include="*.java"

# Raw exception messages in responses (정보 유출)
grep -rn "e\.getMessage()" src/main/ --include="*.java" | grep -i "response\|body\|return"

# TODO/FIXME left behind
grep -rn "TODO\|FIXME\|HACK\|XXX" src/main/ --include="*.java"

# Wildcard imports
grep -rn "import .*\.\*;" src/main/ --include="*.java"
```

## Phase 3: Tests + Coverage

```bash
# Maven
mvn -T 4 test
mvn jacoco:report
# Report: target/site/jacoco/index.html

# Gradle
./gradlew test jacocoTestReport
# Report: build/reports/jacoco/test/html/index.html
```

### Coverage Verification

```bash
# Maven — fails if < 80%
mvn jacoco:check

# Check coverage summary
cat target/site/jacoco/jacoco.csv | head -5
```

### Test Failure Analysis

실패한 테스트가 있으면:
1. 실패 메시지와 stack trace 확인
2. 최근 변경 사항과 관련성 파악
3. Flaky test 여부 확인 (재실행으로 판별)
4. 수정 후 Phase 3 재실행

## Phase 4: Security Scan

### Dependency CVE Scan

```bash
# Maven (OWASP Dependency Check)
mvn org.owasp:dependency-check-maven:check
# Report: target/dependency-check-report.html

# Gradle
./gradlew dependencyCheckAnalyze
```

### Source Code Secrets Scan

```bash
# Hardcoded passwords
grep -rn 'password\s*=\s*"' src/ --include="*.java" --include="*.yml" --include="*.properties"

# API keys and secrets
grep -rn 'sk-\|api_key\|secret\s*=' src/ --include="*.java" --include="*.yml"

# Git history secrets (if git-secrets configured)
git secrets --scan
```

### Security Anti-Patterns

```bash
# Wildcard CORS (production 금지)
grep -rn 'allowedOrigins.*"\*"' src/main/ --include="*.java"

# CSRF disabled without comment/justification
grep -rn 'csrf.*disable' src/main/ --include="*.java"

# Field injection (@Autowired on fields)
grep -rn '@Autowired' src/main/ --include="*.java" | grep -v "constructor\|param"
```

## Phase 5: Format (Optional)

```bash
# Spotless (Maven)
mvn spotless:check    # Verify only
mvn spotless:apply    # Auto-fix

# Spotless (Gradle)
./gradlew spotlessCheck
./gradlew spotlessApply
```

## Phase 6: Diff Review

```bash
git diff --stat
git diff
```

### Diff Checklist

- [ ] 디버깅 로그 제거 (`System.out`, unguarded `log.debug`)
- [ ] HTTP 상태 코드 적절한지 확인
- [ ] @Transactional 필요한 곳에 있는지 확인
- [ ] @Valid 사용하여 입력 검증하는지 확인
- [ ] 새 설정값은 문서화 / application.yml에 반영
- [ ] 새 의존성 추가 시 라이선스 호환성 확인
- [ ] API 변경 시 하위 호환성 확인
- [ ] 민감 정보 로깅 없는지 확인

## Verification Report Template

```
VERIFICATION REPORT
===================
Build:     [PASS/FAIL]
Static:    [PASS/FAIL] (spotbugs/pmd/checkstyle findings: N)
Tests:     [PASS/FAIL] (X/Y passed, Z% line coverage)
Security:  [PASS/FAIL] (CVE critical: N, high: N)
Format:    [PASS/SKIP]
Diff:      [X files changed, +Y/-Z lines]

Overall:   [READY / NOT READY]

Issues to Fix:
1. ...
2. ...
```

## Quick Verification (Development)

풀 파이프라인이 무거울 때, 빠른 피드백 루프:

```bash
# Maven — build + test only
mvn -T 4 test

# + spotbugs만
mvn -T 4 test spotbugs:check

# Gradle
./gradlew test spotbugsMain
```

대규모 변경이나 PR 전에는 반드시 전체 파이프라인 실행.

## Cross-References

| Topic | Skill |
|-------|-------|
| Test 작성 방법 (MockMvc, Mockito) | `springboot-tdd` |
| Security 구현 | `springboot-security` |
| JPA 테스트 (DataJpaTest, Testcontainers) | `jpa-patterns` |
| Core Spring Boot 패턴 | `springboot-patterns` |

## References

- [Spring Boot Reference: Testing](https://docs.spring.io/spring-boot/reference/testing/) — Official test guide
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) — CVE scanning
- [SpotBugs](https://spotbugs.github.io/) — Static analysis for Java
- [JaCoCo](https://www.jacoco.org/jacoco/) — Code coverage
