---
name: translate-article
description: Translate web articles into Korean markdown while faithfully preserving original structure. Save to ~/dev/TIL/{category}/. Use when user provides a URL and asks to "translate", "번역", "한국어로", "Korean translation", or wants to convert English tech articles into Korean documents.
---

# Article Translator

웹 아티클을 **원문 구조를 훼손하지 않고** 한국어 마크다운으로 번역합니다.
TIL 저장소의 적절한 카테고리에 자동 저장합니다.

## 사용법

```
/translate-article <URL>          # URL의 아티클을 한국어로 번역
/translate-article                # 대화형으로 URL 입력
```

## Instructions

### Step 1: URL 확인 및 콘텐츠 가져오기

**인자가 있는 경우** (`/translate-article <URL>`):
- URL에서 콘텐츠를 바로 가져온다

**인자가 없는 경우** (`/translate-article`):
- 번역할 URL을 사용자에게 질문한다

**콘텐츠 가져오기 순서:**
1. GitHub URL → `gh` CLI 사용
2. 기타 URL → WebFetch 시도
3. WebFetch 실패 시 (403, blocked) → `tavily_extract` 사용

### Step 2: 카테고리 자동 판별

아티클 주제를 분석하여 TIL 카테고리를 자동 결정한다.
판별이 애매한 경우 사용자에게 질문한다.

**카테고리 목록:**

| 카테고리 | 주제 |
|----------|------|
| ai | AI, ML, LLM, 에이전트, 프롬프트 엔지니어링 |
| python | Python 언어, 라이브러리 |
| java | Java 언어, JVM |
| spring | Spring Framework, Spring Boot |
| nodejs | Node.js, 비동기 I/O |
| javascript | JavaScript, TypeScript |
| react | React, Next.js |
| frontend | 프론트엔드 일반 |
| backend | 백엔드 아키텍처 일반 |
| database | DB, SQL, NoSQL |
| redis | Redis |
| kafka | Kafka, 메시지 큐 |
| docker | Docker, 컨테이너 |
| kubernetes | Kubernetes, 오케스트레이션 |
| devops | CI/CD, DevOps |
| aws | AWS 서비스 |
| infra | 인프라 일반 |
| network | 네트워크, 프로토콜 |
| security | 보안 |
| computer-science | CS 기초, 알고리즘, 자료구조 |
| design-pattern | 디자인 패턴 |
| testing | 테스트, TDD |
| web | 웹 기술 일반 |
| economics | 경제 |

새 카테고리가 필요한 경우 사용자에게 확인 후 디렉토리를 생성한다.

### Step 3: 번역 실행

#### 핵심 원칙: 원문 구조 보존

**이것이 이 스킬의 가장 중요한 원칙이다.**
번역은 원문의 의미를 한국어로 전달하는 것이지, 문서를 재구성하는 것이 아니다.

| 보존해야 할 것 | 설명 |
|----------------|------|
| 섹션 구조 | 원문의 heading 계층(`#`, `##`, `###`)을 그대로 유지 |
| 단락 순서 | 원문의 단락 순서와 흐름을 변경하지 않음 |
| 리스트/테이블 | 원문의 리스트, 테이블 구조를 그대로 유지 |
| 코드 블록 | 코드는 번역하지 않음. 주석만 필요시 번역 |
| 강조 표현 | 원문의 bold, italic 위치를 유지 |
| 링크 | 원문의 링크를 보존 |
| 이미지 | 원문의 이미지 링크(`![alt](url)`)를 그대로 보존 |

#### 하지 말 것 (CRITICAL)

```
❌ 원문에 없는 "결론부터 말하면" 섹션 추가
❌ 원문 구조를 TIL 형식으로 재구성
❌ 원문에 없는 내용 추가 또는 생략
❌ 섹션 순서 변경
❌ README.md 수정
❌ git add, git commit, git push 실행 (사용자가 명시적으로 요청하지 않는 한)
```

#### 해야 할 것

```
✅ 원문의 이미지를 ![alt](url) 형태로 그대로 가져오기 (우선)
✅ 이미지 URL을 가져올 수 없는 경우에만 mermaid/테이블로 재현 (fallback)
✅ 기술 용어 첫 등장 시 영문 병기: "프롬프트 체이닝(Prompt Chaining)"
✅ 이후 등장 시에는 한국어 또는 영어 중 자연스러운 쪽 사용
✅ 코드/명령어는 번역하지 않고 원문 그대로 유지
✅ 번역 출처 헤더 추가 (아래 템플릿 참조)
```

#### 다이어그램/이미지 처리 전략

**원문 이미지를 우선 사용하고, 실패 시 mermaid로 fallback 한다.**

```
1순위: 원문의 <img> / ![alt](url) 에서 이미지 URL 추출 → 그대로 삽입
2순위: 이미지 URL을 가져올 수 없거나 CDN 접근 불가 → mermaid로 재현
```

**이미지 추출 방법:**
- WebFetch로 원문 HTML을 가져올 때, 모든 `<img>` 태그의 `src`와 `alt`를 수집
- `![alt text](image_url)` 형태로 원문의 해당 위치에 삽입
- alt text는 원문 그대로 유지 (번역하지 않음)

### Step 4: 번역 규칙

#### 4.1 언어 규칙

| 항목 | 규칙 |
|------|------|
| 본문 설명 | 한국어 |
| 기술 용어 | 영어 유지 또는 한국어(영어) 병기 |
| 코드/명령어 | 영어 원문 그대로 |
| 고유명사 | 영어 원문 그대로 (Claude, GitHub, SWE-bench 등) |
| 제목/헤딩 | 한국어 번역 (필요시 영어 병기) |

#### 4.2 문체

- **문어체** 사용 (~다, ~이다)
- 문단 단위 번역 (문장 단위 직역 금지)
- 자연스러운 한국어 흐름 유지
- 원문의 톤(격식/비격식)을 보존

#### 4.3 불확실한 번역

- 의미가 불확실한 부분은 원문을 괄호로 병기
- 예: "이 방법은 포카요케(Poka-yoke, 실수 방지) 원칙을 적용한다"

### Step 5: CLAUDE.md 포맷팅 규칙 적용

원문 구조를 보존하되, 아래 포맷팅 규칙은 반드시 따른다:

#### Bold 규칙

닫는 `**` 다음에 반드시 띄어쓰기:

```markdown
❌ Bad: **정식 지원(Stable)**된다.
✅ Good: **정식 지원(Stable)** 된다.
```

#### mermaid 규칙 (fallback 시에만 적용)

원문 이미지를 가져올 수 없어 mermaid로 재현하는 경우:

**스타일:** 어두운 배경 + 흰 글씨만 사용
```markdown
✅ style Node fill:#1565C0,color:#fff
```

**줄바꿈:** `<br>` 사용 (`\n` 금지)
```markdown
✅ ["첫째 줄<br>둘째 줄"]
```

**subgraph:** style 지정하지 않음 (기본 배경 사용)

**권장 색상:**

| 용도 | fill | color |
|------|------|-------|
| 시작/핵심 (파랑) | `#1565C0` | `#fff` |
| 종료/성공 (초록) | `#2E7D32` | `#fff` |
| 조건/분기 (주황) | `#E65100` | `#fff` |
| 오류/위험 (빨강) | `#C62828` | `#fff` |

#### ASCII 박스 금지

원문에 ASCII 다이어그램이 있으면 테이블 또는 mermaid로 변환한다.

#### 수식

원문에 수식이 있으면 LaTeX 문법으로 변환한다.

```markdown
❌ Bad: S = 1 / ((1 - P) + P/N)
✅ Good: $S = \frac{1}{(1-P) + \frac{P}{N}}$
```

### Step 6: 파일 저장

#### 파일명 규칙

**파일명 = 제목(한국어 번역)과 동일:**

| 번역된 제목 | 파일명 |
|-------------|--------|
| `# 효과적인 에이전트 구축하기` | `효과적인-에이전트-구축하기.md` |
| `# React Server Components 이해하기` | `React-Server-Components-이해하기.md` |

- 특수문자 제거, 공백을 하이픈(-)으로 변환
- 첫 줄은 반드시 `# `로 시작

#### 저장 위치

`/Users/sskim/dev/TIL/{category}/`

#### 번역 헤더 템플릿

파일 시작 부분에 아래 헤더를 추가:

```markdown
# 번역된 제목

> 이 글은 [원문 사이트명]의 [원문 제목](원문 URL) 을 한국어로 번역한 글입니다.
> 원문 작성일: YYYY년 MM월 DD일 | 작성자: 저자명
```

- 원문 작성일/저자가 확인 불가능한 경우 해당 항목 생략
- 원문 제목은 영어 원문 그대로 사용

#### 출처 섹션

문서 맨 마지막에 출처 추가:

```markdown
## 출처

- [원문 제목 - 사이트명](URL) - 원문
```

### Step 7: 완료 리포트

파일 저장 후 사용자에게 아래 정보를 안내한다:

- 저장 경로 (카테고리 포함)
- 원문 제목 → 번역 제목
- 이미지: 원문에서 가져온 수 / mermaid fallback 수

### Step 8: Self-Check

파일 저장 후 아래 항목 점검:

- [ ] 원문 구조가 보존되었는가? (섹션 순서, heading 계층)
- [ ] 원문에 없는 내용을 추가하지 않았는가?
- [ ] 번역 헤더가 포함되었는가?
- [ ] 기술 용어가 적절히 병기되었는가?
- [ ] 코드 블록이 번역되지 않고 원문 그대로인가?
- [ ] 원문 이미지를 `![alt](url)` 형태로 가져왔는가? (가져올 수 없는 경우만 mermaid)
- [ ] Bold 닫는 `**` 다음에 띄어쓰기가 있는가?
- [ ] mermaid 사용 시: `\n` 대신 `<br>`, 어두운 배경 + `color:#fff`
- [ ] ASCII 박스 대신 테이블/mermaid를 사용했는가?
- [ ] 출처가 명시되었는가?
- [ ] 파일명이 번역된 제목과 일치하는가?

## 주의사항

- README.md는 GitHub Actions가 자동 생성하므로 **절대 수정하지 말 것**
- `git add`, `git commit`, `git push`는 **사용자가 명시적으로 요청할 때만** 실행
- 원문에 없는 내용을 임의로 추가하지 말 것 (mermaid 다이어그램 재현은 예외)
- 번역 품질이 불확실한 부분은 원문을 병기하여 투명하게 처리
