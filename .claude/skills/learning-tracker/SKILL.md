---
name: learning-tracker
description: |
  Claude Code 세션에서 새로운 기술/라이브러리/개념 학습 내용을 추출.
  "학습 정리", "오늘 배운 것", "learning", "세션 요약" 등의 요청 시 자동 적용.
  추출된 내용은 /til 또는 /obsidian-flashcard 스킬에 위임하여 저장.
---

# Learning Tracker Skill

Claude Code 세션에서 **새로운 기술, 라이브러리, 개념**에 대한 학습 내용을 추출하여 TIL 형식으로 정리합니다.

## 사용법

```bash
/learning-tracker              # 현재 세션의 학습 내용 추출
/learning-tracker "주제"       # 특정 주제로 필터링하여 추출
```

## Instructions

### Step 1: 세션 로그 분석

현재 대화 세션에서 다음 패턴을 찾습니다:

#### 학습 감지 패턴

**한국어 키워드:**
| 패턴 | 설명 |
|------|------|
| "배웠", "배워" | 학습 완료 표현 |
| "알게 됐", "알았" | 새로운 이해 |
| "처음", "처음으로" | 최초 경험 |
| "새로운", "새롭게" | 새로운 지식 |
| "이해했", "이해됐" | 개념 이해 |
| "몰랐던", "몰랐는데" | 기존 무지 인정 |
| "이렇게 하는구나" | 방법 습득 |

**영어 키워드:**
| 패턴 | 설명 |
|------|------|
| "TIL", "Today I learned" | 명시적 학습 표현 |
| "learned", "discovered" | 학습/발견 |
| "didn't know", "now I know" | 새로운 지식 |
| "first time" | 최초 경험 |

**질문 패턴 (사용자 질문 → 학습 기회):**
| 패턴 | 설명 |
|------|------|
| "이게 뭐야?", "이게 뭔가요?" | 개념 질문 |
| "어떻게 해?", "어떻게 하나요?" | 방법 질문 |
| "왜?", "왜 그런가요?" | 이유 질문 |
| "차이가 뭐야?" | 비교 질문 |

**기술 학습 지표:**
| 지표 | 설명 |
|------|------|
| 새 라이브러리 import | 처음 사용하는 패키지 |
| 새 CLI 도구 사용 | 처음 사용하는 명령어 |
| API 문서 참조 | WebFetch로 공식 문서 조회 |
| 에러 해결 후 설명 | 문제 해결 과정에서 학습 |
| 코드 설명 요청 | "이 코드가 뭐야?" |

### Step 2: 학습 내용 분류

추출한 내용을 카테고리별로 분류합니다:

| 카테고리 | 키워드/패턴 |
|----------|------------|
| `python` | Python, pip, pytest, FastAPI, Django, pandas |
| `java` | Java, Spring, Maven, Gradle, JUnit |
| `spring` | Spring Boot, Spring Security, JPA |
| `nodejs` | Node.js, npm, Express, libuv |
| `ai` | LangChain, LangGraph, OpenAI, LLM, embedding |
| `security` | 보안, 암호화, 인증, OAuth, JWT |
| `computer-science` | 알고리즘, 자료구조, 동시성, 병렬성 |
| `database` | SQL, PostgreSQL, MySQL, Redis |
| `devops` | Docker, Kubernetes, CI/CD, GitHub Actions |

### Step 3: 학습 내용 요약 생성

추출한 학습 내용을 구조화하여 정리합니다 (저장용 포맷은 각 스킬이 담당):

```yaml
# 학습 추출 결과
주제: [학습 주제]
카테고리: [python, java, spring, ai, etc.]
한줄요약: [핵심 내용 1문장]

학습_포인트:
  - [핵심 개념 1]: [설명]
  - [핵심 개념 2]: [설명]

코드_예시: |
  [세션에서 작성/참조한 코드]

배경: [왜 이걸 배우게 됐는지]
출처: [참조한 문서/링크]
```

**참고**: 이 요약은 `/til` 또는 `/obsidian-flashcard` 스킬에 전달되며, 최종 포맷은 해당 스킬이 적용합니다.

### Step 4: 사용자 확인

생성된 초안을 사용자에게 보여주고 확인 요청:

```
📚 학습 내용 추출 완료!

**감지된 학습 주제:**
1. [주제 1] - python 카테고리
2. [주제 2] - spring 카테고리

**어떤 형식으로 저장할까요?**
1. TIL 문서 → `/til` 스킬 호출
2. 플래시카드 → `/obsidian-flashcard` 스킬 호출
3. 둘 다 생성 → 두 스킬 순차 호출
```

### Step 5: 저장 (다른 스킬에 위임)

사용자 선택에 따라 해당 스킬을 호출하여 저장을 위임:

| 선택 | 호출 스킬 | 전달 내용 |
|------|-----------|-----------|
| TIL 문서 | `/til` | 추출된 주제, 카테고리, 학습 내용 요약 |
| 플래시카드 | `/obsidian-flashcard` | Q&A 형식으로 변환된 학습 포인트 |
| 둘 다 | 두 스킬 순차 호출 | 각각에 맞는 형식으로 전달 |

**중요**: learning-tracker는 직접 파일을 저장하지 않음. 포맷과 저장 규칙은 각 스킬이 담당.

---

## 자동 추출 예시

### 예시 1: 라이브러리 사용

**세션 대화:**
```
사용자: httpx로 비동기 요청 어떻게 해?
Claude: httpx.AsyncClient를 사용하면 됩니다...
```

**추출 결과:**
```markdown
# Python httpx로 비동기 HTTP 요청하기

## 결론부터 말하면

httpx는 requests와 유사한 API를 제공하면서 async/await를 지원하는 HTTP 클라이언트다.
`AsyncClient`를 context manager로 사용하면 connection pooling까지 자동 관리된다.
```

### 예시 2: 개념 이해

**세션 대화:**
```
사용자: 왜 Spring에서 @Transactional이 private 메서드에서 안 먹어?
Claude: Spring AOP는 프록시 기반이라서...
```

**추출 결과:**
```markdown
# Spring @Transactional이 private 메서드에서 작동하지 않는 이유

## 결론부터 말하면

Spring의 @Transactional은 프록시 기반 AOP로 동작한다.
private 메서드는 프록시가 가로챌 수 없어서 트랜잭션이 적용되지 않는다.
```

### 예시 3: 문제 해결

**세션 대화:**
```
사용자: pytest에서 fixture 스코프가 뭐야?
Claude: fixture의 생명주기를 결정합니다. function, class, module, session...
```

**추출 결과:**
```markdown
# pytest fixture scope 이해하기

## 결론부터 말하면

fixture scope는 fixture 인스턴스의 생명주기를 결정한다.
function(기본값)은 매 테스트마다, session은 전체 테스트 실행 중 한 번만 생성된다.
```

---

## 워크플로우

learning-tracker는 **추출 전용** 스킬로, 저장은 다른 스킬에 위임:

```
/learning-tracker
    ↓
세션 분석 & 학습 내용 추출
    ↓
사용자에게 추출 결과 확인
    ↓
저장 형식 선택
    ├─ TIL 문서 → /til 스킬 호출 → ~/dev/TIL/{category}/
    └─ 플래시카드 → /obsidian-flashcard 호출 → Obsidian 00.Inbox/FC-*.md
```

**핵심 원칙**: 포맷/저장 규칙은 각 스킬이 담당. learning-tracker는 추출만 수행.

---

## 주의사항

- learning-tracker는 **추출만** 수행. 파일 저장은 `/til` 또는 `/obsidian-flashcard` 스킬이 담당
- 민감한 정보(API 키, 비밀번호 등)가 포함된 내용은 추출에서 제외
- 저장 관련 규칙(파일명, 경로, git 작업 등)은 각 스킬의 지침을 따름
