---
name: init-project-rules
description: Initialize project-level Claude Code rules by detecting languages and frameworks. Creates .claude/rules/{lang}/ with coding-style, testing, and security guardrails. Use when setting up a new project, saying "init rules", "프로젝트 룰 설정", "rules 초기화", "프로젝트 룰", or wanting project-specific coding guardrails. Do NOT use for global skill creation (use skill-guide) or Serena initialization (use init-serena).
---

# 프로젝트 Rules 초기화

프로젝트의 언어와 프레임워크를 감지하여 `.claude/rules/{lang}/` 에 가드레일을 생성한다.

## Step 1: 프로젝트 스캔

아래 기준으로 프로젝트 루트를 스캔한다.

### 언어 감지

| 언어 | 감지 파일 | paths 패턴 |
|------|----------|-----------|
| Python | pyproject.toml, setup.py, setup.cfg, requirements.txt, Pipfile | `**/*.py`, `**/*.pyi` |
| Java | pom.xml, build.gradle, build.gradle.kts + *.java 존재 | `**/*.java` |
| Kotlin | *.kt 존재, build.gradle.kts with kotlin plugin | `**/*.kt`, `**/*.kts` |
| TypeScript | tsconfig.json, *.ts 존재 | `**/*.ts`, `**/*.tsx` |
| JavaScript | package.json 존재 + tsconfig 없음, *.js 존재 | `**/*.js`, `**/*.jsx` |
| Go | go.mod | `**/*.go` |
| Rust | Cargo.toml | `**/*.rs` |

### 프레임워크 감지

설정 파일이 존재하면 의존성을 읽어 프레임워크를 감지한다:

| 언어 | 설정 파일 | 감지 대상 |
|------|----------|----------|
| Python | pyproject.toml, requirements.txt | fastapi, django, flask, sqlalchemy |
| Java/Kotlin | pom.xml, build.gradle(.kts) | spring-boot, quarkus |
| TypeScript/JS | package.json | next, react, vue, express, nestjs |
| Go | go.mod | gin, echo, fiber |
| Rust | Cargo.toml | actix-web, axum, rocket, tokio |

## Step 2: 사용자 확인 (대화형)

스캔 결과를 아래 형식으로 표시하고 사용자 확인을 받는다:

```
프로젝트를 스캔했습니다.

감지된 언어:
  ✅ Python (pyproject.toml → FastAPI, SQLAlchemy)
  ✅ TypeScript (tsconfig.json → Next.js)

연결 가능한 글로벌 스킬:
  Python  → python-patterns, python-code-style, python-testing
  TypeScript → react-best-practices

이대로 진행할까요? 언어를 추가/제거하려면 알려주세요.
```

**CRITICAL**: 사용자가 확인하기 전에 파일을 생성하지 않는다.

## Step 3: Rules 생성

확인된 각 언어에 대해 `.claude/rules/{lang}/` 디렉토리를 만들고 3개 파일을 생성한다:

```
.claude/rules/
├── python/
│   ├── coding-style.md
│   ├── testing.md
│   └── security.md
├── typescript/
│   ├── coding-style.md
│   ├── testing.md
│   └── security.md
└── ...
```

**기존 파일 보호**: `.claude/rules/{lang}/` 가 이미 존재하면 덮어쓰지 않고 사용자에게 알린다.

## Step 4: 결과 요약

```
.claude/rules/ 생성 완료:

  python/
    coding-style.md  (42줄) - PEP 8, type hints, ruff
    testing.md       (38줄) - pytest, TDD, 80%+ coverage
    security.md      (30줄) - bandit, input validation

  typescript/
    coding-style.md  (40줄) - ESLint, strict TypeScript
    testing.md       (35줄) - Vitest, Testing Library
    security.md      (28줄) - XSS, CSP, dependency audit
```

---

## Rule 파일 작성 규칙

### 형식

1. **모든 파일에 `paths` frontmatter** 포함:
   ```yaml
   ---
   paths:
     - "**/*.py"
     - "**/*.pyi"
   ---
   ```
2. **30~50줄 이내** — 가드레일이지 레퍼런스가 아님
3. **CRITICAL/HIGH 원칙만** — 모든 것을 담지 않는다
4. **코드 예제 최소화** — Good/Bad 각 1개 이내
5. **프레임워크 반영** — 감지된 프레임워크 컨벤션을 rules에 포함
6. **글로벌 스킬 연결** — 존재하는 스킬만 Reference 섹션에 추가

### Reference 섹션

글로벌 스킬이 존재하는 경우에만 파일 끝에 추가:

```markdown
## Reference

See skill: `python-patterns` for comprehensive patterns and code review.
See skill: `python-code-style` for linter and formatter configuration.
```

### 글로벌 스킬 매핑 테이블

| 언어 | 연결 가능한 스킬 |
|------|----------------|
| Python | `python-patterns`, `python-code-style`, `python-testing` |
| Java | `jpa-patterns`, `java-modern-patterns` |
| Kotlin | `jpa-patterns`, `java-modern-patterns` |
| TypeScript | `react-best-practices` |
| JavaScript | `react-best-practices` |
| Go | (없음) |
| Rust | (없음) |

**CRITICAL**: `~/.claude/skills/` 를 실제로 확인하여 존재하는 스킬만 Reference에 추가한다. 테이블에 있더라도 실제 설치되지 않은 스킬은 참조하지 않는다.

---

## 언어별 Rule 내용 가이드

### coding-style.md

각 언어에 맞게 아래 항목을 포함:

- **네이밍 컨벤션**: 파일, 클래스, 함수, 상수 네이밍 규칙
- **포매터/린터**: 도구명과 기본 설정 (한 줄 요약)
- **타입 시스템**: type hints, generics, strict mode 등
- **파일 조직**: 크기 제한, 모듈 구조 원칙
- **Immutability**: 불변 데이터 선호 패턴

| 언어 | 포매터/린터 | 타입 시스템 |
|------|-----------|-----------|
| Python | ruff (lint+format), mypy | type hints 필수, strict mode |
| Java | google-java-format, checkstyle | generics, sealed classes |
| Kotlin | ktlint, detekt | null safety, data class |
| TypeScript | ESLint, Prettier | strict: true, no any |
| JavaScript | ESLint, Prettier | JSDoc 권장 |
| Go | gofmt, golangci-lint | 내장 타입 시스템 |
| Rust | rustfmt, clippy | 소유권, 라이프타임 |

### testing.md

- **테스트 프레임워크**: 언어별 표준 프레임워크
- **TDD 사이클**: RED → GREEN → REFACTOR
- **커버리지**: 80%+ 목표, 실행 명령어
- **테스트 분류**: unit / integration / e2e
- **프레임워크별 패턴**: 테스트 클라이언트, DB fixture 등

| 언어 | 프레임워크 | 커버리지 명령어 |
|------|----------|---------------|
| Python | pytest | `pytest --cov=src --cov-report=term-missing` |
| Java | JUnit 5 + Mockito | `./gradlew test jacocoTestReport` 또는 `mvn test jacoco:report` |
| Kotlin | JUnit 5 + MockK | 동일 (Gradle/Maven) |
| TypeScript | Vitest 또는 Jest | `npx vitest --coverage` |
| JavaScript | Vitest 또는 Jest | `npx vitest --coverage` |
| Go | testing + testify | `go test -cover ./...` |
| Rust | cargo test | `cargo tarpaulin` |

### security.md

- **시크릿 관리**: 환경변수 사용, .env를 git에 커밋 금지
- **Input validation**: 시스템 경계에서 검증
- **Injection 방지**: SQL, XSS, command injection
- **의존성 보안**: 스캔 도구
- **에러 메시지**: 민감 정보 노출 금지

| 언어 | 보안 스캔 도구 | 의존성 감사 |
|------|-------------|-----------|
| Python | bandit | `pip-audit`, `safety` |
| Java/Kotlin | SpotBugs, OWASP dep-check | `./gradlew dependencyCheckAnalyze` |
| TypeScript/JS | ESLint security plugin | `npm audit` |
| Go | gosec | `govulncheck ./...` |
| Rust | cargo-audit | `cargo audit` |

---

## 주의사항

- 글로벌 스킬에 있는 상세 내용을 rules에 **복제하지 않는다**
- rules는 **"이것만은 꼭 지켜라"** 수준의 가드레일만 담는다
- 프레임워크가 감지되지 않으면 **언어 기본 컨벤션**으로 생성한다
- monorepo에서는 **복수 언어 동시 생성**이 가능하다
