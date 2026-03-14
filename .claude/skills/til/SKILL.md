---
name: til
description: Write TIL(Today I Learned) documents to ~/dev/TIL/{category}/. "Why" focused storytelling, conclusion first, mermaid diagrams, code examples. Auto-categorize (python, java, spring, nodejs, ai, etc). **Proactively use this skill** when user mentions "TIL", "write TIL", "TIL document", "learning note" without explicit /til command. Do NOT use for Obsidian vault notes (use obsidian-note skill), flashcards (use obsidian-flashcard skill), or blog posts (use tech-blog-writer skill).
---

# TIL Writer

TIL 저장소에 "왜(Why)" 중심의 스토리텔링 기술 문서를 작성합니다.

## 사용법

```
/til "주제"     # 주제로 바로 문서 작성 시작
/til            # 대화형으로 주제/카테고리 선택
```

## 참고 자료

| 파일 | 내용 |
|------|------|
| [mermaid-style-guide.md](references/mermaid-style-guide.md) | mermaid 다이어그램 스타일 규칙 (색상, sequenceDiagram, subgraph) |
| [writing-style-guide.md](references/writing-style-guide.md) | 작성 철학, 스토리텔링, Bold, LaTeX, 출처 |
| [category-guide.md](references/category-guide.md) | 카테고리별 작성 특성 |
| [til-template.md](assets/til-template.md) | TIL 문서 템플릿 |

## Instructions

### Step 1: 주제 확인

**인자가 있는 경우** (`/til "주제"`):
- 주제를 파악하고 적절한 카테고리 제안
- 카테고리 선택 시 [category-guide.md](references/category-guide.md) 참조
- 사용자 확인 후 작성 시작

**인자가 없는 경우** (`/til`):
- 어떤 주제로 TIL을 작성할지 질문
- 카테고리 선택 (python, java, spring, nodejs, security, computer-science, ai 등)

### Step 2: 문서 구조 작성

[til-template.md](assets/til-template.md)의 템플릿을 기반으로 작성.

**필수 섹션:**
- `# 제목` (호기심 유발)
- `## 결론부터 말하면` (핵심 요약 2-3문장 + 다이어그램/코드 비교)
- `## 1. 왜 ...?` (배경, 문제 상황)
- `## 2. 핵심 개념 설명`
- `## 3. 실제 사례 / 코드 예시`
- `## 4. 정리`
- `## 출처`

### Step 3: 핵심 원칙 적용

자세한 가이드: [writing-style-guide.md](references/writing-style-guide.md)

#### "왜(Why)"를 반드시 설명

```markdown
❌ Bad: "DI는 의존성을 외부에서 주입하는 패턴입니다."
✅ Good: "만약 프레임워크 없이 웹 서버를 만든다면? 우리가 직접 해야 할 일들이 산더미처럼 쌓인다..."
```

#### 스토리텔링 패턴 사용

| 패턴 | 예시 |
|------|------|
| 문제 -> 의문 -> 해답 | "싱글스레드인데 어떻게 동시에? -> libuv가 있기 때문" |
| 만약 ~라면? | "만약 Spring 없이 웹 서버를 만든다면?" |
| 이상한 점 발견 | "근데 이상하다. 싱글스레드라면서 왜 4개가 동시에?" |

#### 연결어로 흐름 만들기

```markdown
✅ Good:
"하지만 여기서 문제가 생겼다."
"왜일까?"
"그렇다면 이건 어떻게 설명할 수 있을까?"
"이제 답이 보인다."
```

#### 문단 단위로 설명 (한 줄씩 끊지 말 것)

```markdown
❌ Bad:
- libuv는 비동기 I/O 라이브러리다.
- Thread Pool을 가진다.

✅ Good:
libuv는 Node.js의 비동기 I/O를 담당하는 C 라이브러리다. Ryan Dahl이 Node.js를 만들 때
직접 개발했다. 왜 필요했을까? JavaScript 자체에는 파일을 읽거나 네트워크 통신을 하는
기능이 없다.
```

### Step 4: 시각화 규칙

자세한 가이드: [mermaid-style-guide.md](references/mermaid-style-guide.md)

**필수 규칙:**
- ASCII 박스 금지 -> 테이블 또는 mermaid 사용
- 어두운 배경 + 흰 글씨: `style Node fill:#1565C0,color:#fff`
- 줄바꿈은 `<br>` 사용 (`\n` 아님)
- subgraph에는 style 지정하지 않음
- sequenceDiagram은 `style` 대신 `rect rgba()` 사용

### Step 5: 스타일 규칙

자세한 가이드: [writing-style-guide.md](references/writing-style-guide.md)

#### Bold 처리

**닫는 `**` 다음에 반드시 띄어쓰기:**
```markdown
❌ Bad: **정식 지원(Stable)**된다.
✅ Good: **정식 지원(Stable)** 된다.
```

#### 수식은 LaTeX

```markdown
❌ Bad: S = 1 / ((1 - P) + P/N)
✅ Good: $S = \frac{1}{(1-P) + \frac{P}{N}}$
```

### Step 6: 파일 저장

**파일명 = 제목과 동일:**

| 제목 | 파일명 |
|------|--------|
| `# Python의 f-string` | `Python의-f-string.md` |
| `# Node.js가 싱글스레드라는 미신` | `Node.js가-싱글스레드라는-미신.md` |

**저장 위치:** `/Users/sskim/dev/TIL/{category}/`

### Step 7: Self-Check 실행

문서 작성 완료 후 아래 항목 점검:

#### 필수 (MUST)
- [ ] **"왜"를 설명했는가?**
- [ ] **스토리텔링으로 풀어갔는가?**
- [ ] "결론부터 말하면" 섹션이 있는가?
- [ ] 파일명이 제목과 일치하는가?

#### 권장 (SHOULD)
- [ ] Before/After 비교가 있는가?
- [ ] 복잡한 개념은 mermaid로 시각화했는가?
- [ ] ASCII 박스 대신 테이블/mermaid를 사용했는가?

#### 시각화 (CHECK)
- [ ] mermaid에서 `\n` 대신 `<br>` 사용했는가?
- [ ] mermaid style에 color가 있는가?
- [ ] sequenceDiagram에서 `rect rgba()` 사용했는가?
- [ ] subgraph에 style을 지정하지 않았는가?

#### 스타일 (CHECK)
- [ ] Bold 닫는 `**` 다음에 띄어쓰기가 있는가?
- [ ] 수식은 LaTeX로 작성했는가?
- [ ] 출처를 명시했는가?
- [ ] 문단 단위로 설명했는가?

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| mermaid 렌더링 깨짐 | `\n` 사용 또는 color 누락 | `<br>` 사용, style에 color 명시 |
| Bold 뒤 텍스트 붙음 | `**` 뒤 띄어쓰기 누락 | `**텍스트** 뒤` 형태로 수정 |
| sequenceDiagram 스타일 무시됨 | `style` 미지원 | `rect rgba()` 사용 |
| 카테고리 미결정 | 주제가 여러 카테고리에 걸침 | 가장 핵심적인 기술 기준으로 선택 |
| 파일명 특수문자 에러 | 제목에 `/`, `?`, `:` 등 포함 | 특수문자 제거 후 하이픈 변환 |

## 주의사항

- README.md는 GitHub Actions가 자동 생성하므로 **절대 수정하지 말 것**
- `git add`, `git commit`, `git push`는 **사용자가 명시적으로 요청할 때만** 실행
