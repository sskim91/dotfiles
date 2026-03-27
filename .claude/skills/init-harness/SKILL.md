---
name: init-harness
description: Use when user says "init harness", "하네스 초기화", "하네스 설정", "init rules", "프로젝트 룰 설정", "rules 초기화", "프로젝트 룰", "프로젝트 설정". Do NOT use for skill creation (use skill-guide) or Serena (use init-serena).
---

# Init Harness

프로젝트를 스캔하여 AI 에이전트가 자율적으로 작업할 수 있는 하네스(`.claude/` 구성)를 생성한다.

## 하네스 3 레이어

### 1. Knowledge Layer — 에이전트가 프로젝트를 이해하는 문서

| 산출물 | 역할 |
|--------|------|
| `.claude/CLAUDE.md` | **목차**. 프로젝트 개요, 아키텍처 다이어그램, 파일 구조 맵, Quick commands. docs/와 rules/로의 포인터 |
| `.claude/docs/ARCHITECTURE.md` | 시스템 지도 — 계층 구조, 데이터 흐름, 주요 컴포넌트 관계 |

### 2. Execution Layer — 에이전트의 코딩 가드레일

| 산출물 | 역할 |
|--------|------|
| `.claude/rules/{lang}/coding-style.md` | 네이밍, 포매터/린터, 타입 시스템, 파일 조직 |
| `.claude/rules/{lang}/testing.md` | 테스트 프레임워크, TDD, 커버리지 목표, 실행 명령어 |
| `.claude/rules/{lang}/security.md` | 시크릿 관리, input validation, injection 방지 |

### 3. Verification Layer — 자기 검증 기준

| 산출물 | 역할 |
|--------|------|
| `.claude/docs/QUALITY_CHECKLIST.md` | PR/작업 완료 전 확인 사항 (빌드, 테스트, 린트, 보안 스캔 명령어) |

## 실행 흐름

1. **프로젝트 스캔**: 언어, 프레임워크, 디렉토리 구조, 기존 `.claude/` 유무 감지
2. **하네스 구성 제안**: 생성할 파일 목록과 트리 구조를 사용자에게 제시
3. **사용자 확인 후 생성** — 확인 전에 파일을 생성하지 않는다
4. **기존 파일 보호** — 이미 존재하는 파일은 덮어쓰지 않고 알린다

## 프로젝트 스캔

### 언어 감지

| 언어 | 감지 파일 | rules paths |
|------|----------|-------------|
| Python | pyproject.toml, setup.py, requirements.txt | `**/*.py` |
| Java | pom.xml, build.gradle(.kts) + *.java | `**/*.java` |
| Kotlin | *.kt + kotlin plugin | `**/*.kt`, `**/*.kts` |
| TypeScript | tsconfig.json | `**/*.ts`, `**/*.tsx` |
| JavaScript | package.json (tsconfig 없을 때) | `**/*.js`, `**/*.jsx` |
| Go | go.mod | `**/*.go` |
| Rust | Cargo.toml | `**/*.rs` |

### 프레임워크 감지

의존성 파일(pyproject.toml, package.json, pom.xml 등)을 읽어 프레임워크를 감지한다:
FastAPI, Django, Flask, Spring Boot, Quarkus, Next.js, React, Vue, Express, NestJS, Gin, Echo, Axum 등.

## 각 산출물 작성 원칙

### CLAUDE.md

- **목차 역할**: 상세는 docs/와 rules/에, CLAUDE.md는 포인터
- **아키텍처 다이어그램**: ASCII 텍스트로 계층/데이터 흐름 (내부 텍스트는 영어만 사용)
- **파일 구조 맵**: 주요 디렉토리와 역할
- **Quick commands**: 빌드, 테스트, 린트 실행 명령어
- 기존 CLAUDE.md가 있으면 **병합 제안** (덮어쓰기 금지)

### ARCHITECTURE.md

- **실제 코드를 분석하여 작성** — 추측하지 않는다
- 컴포넌트 간 관계, 데이터 흐름, 계층 의존 방향
- 핵심 도메인 개념 (주요 엔티티/모델)

### Rules 파일

- 모든 파일에 `paths` frontmatter 포함
- **30~50줄 이내** — 가드레일이지 레퍼런스가 아님
- CRITICAL/HIGH 원칙만. 코드 예제 최소화 (Good/Bad 각 1개 이내)
- 감지된 프레임워크 컨벤션 반영
- 글로벌 스킬이 존재하면 Reference 섹션에 연결

### QUALITY_CHECKLIST.md

- 프로젝트에 실제 존재하는 도구 기반으로 작성
- 빌드/테스트/린트/보안스캔 각 명령어와 기대 결과
- 에이전트가 작업 완료 전에 자기 검증할 수 있는 체크리스트

## 글로벌 스킬 연결

| 언어 | 연결 가능 스킬 |
|------|---------------|
| Python | python-patterns, python-code-style, python-testing |
| Java | jpa-patterns, java-modern-patterns, springboot-patterns, springboot-security, springboot-tdd |
| Kotlin | kotlin-patterns, jpa-patterns |
| TypeScript/JS | react-best-practices |
| Go | golang-patterns |

**CRITICAL**: `~/.claude/skills/`를 확인하여 실제 존재하는 스킬만 Reference에 추가한다.

## 함정 회피

| 함정 | 대응 |
|------|------|
| CLAUDE.md에 모든 것을 때려넣음 → 컨텍스트 희석 | CLAUDE.md는 목차, 상세는 docs/와 rules/에 분리 |
| 글로벌 스킬 내용을 rules에 복제 | rules는 "이것만은 꼭" 수준, 상세는 스킬 참조 |
| 코드를 안 읽고 추측으로 아키텍처 작성 | 실제 코드를 분석한 뒤 작성 |
| 기존 .claude/ 설정을 덮어씀 | 기존 파일 보호, 병합 제안 |
| monorepo에서 단일 언어만 감지 | 복수 언어 동시 스캔 및 생성 |
