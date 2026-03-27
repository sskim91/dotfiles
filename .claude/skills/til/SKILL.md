---
name: til
description: Use when user mentions "TIL", "write TIL", "TIL 작성", "learning note", or /til command. Do NOT use for Obsidian notes (use obsidian-note), flashcards (use obsidian-flashcard), or blog posts (use tech-blog-writer).
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

### Step 2: 리서치

작성 전 `tavily_search` 또는 `WebSearch`로 주제를 검색하여 최신 정보와 공식 문서 URL을 확보한다. 할루시네이션 방지와 정확한 출처 확보를 위해 **항상 실행**한다.

### Step 3: 문서 구조 작성

[til-template.md](assets/til-template.md)의 템플릿을 기반으로 작성.

**필수 섹션:**
- `# 제목` (호기심 유발)
- `## 결론부터 말하면` (핵심 요약 2-3문장 + 다이어그램/코드 비교)
- `## 1. 왜 ...?` (배경, 문제 상황)
- `## 2. 핵심 개념 설명`
- `## 3. 실제 사례 / 코드 예시`
- `## 4. 정리`
- `## 출처`

### Step 4: 핵심 원칙 적용

[writing-style-guide.md](references/writing-style-guide.md)를 읽고 아래 원칙을 적용:

- **"왜(Why)"를 반드시 설명** — 정의 나열이 아닌 문제 상황에서 출발
- **스토리텔링 패턴 사용** — 문제→의문→해답, 만약~라면?, 이상한 점 발견
- **연결어로 흐름 만들기** — 단락 간 자연스러운 전환
- **문단 단위로 설명** — 한 줄씩 끊지 말 것

### Step 5: 시각화 규칙

[mermaid-style-guide.md](references/mermaid-style-guide.md)를 읽고 아래 규칙을 적용:

- ASCII 박스 금지 → 테이블 또는 mermaid 사용
- 어두운 배경 + 흰 글씨: `style Node fill:#1565C0,color:#fff`
- 줄바꿈은 `<br>` 사용 (`\n` 아님)
- subgraph에는 style 지정하지 않음
- sequenceDiagram은 `style` 대신 `rect rgba()` 사용
- **다이어그램 작성 즉시** `mcp__mermaid-mcp__validate_and_render_mermaid_diagram`으로 검증

### Step 6: 스타일 규칙

[writing-style-guide.md](references/writing-style-guide.md)의 스타일 규칙 섹션을 참조:

- Bold 닫는 `**` 다음에 반드시 띄어쓰기
- 수식은 LaTeX (`$...$`, `$$...$$`)
- 출처는 `## 출처` 섹션에 공식 문서 최상단 배치

### Step 7: 파일 저장

**파일명 = 제목에서 공백을 하이픈으로 변환:**

| 제목 | 파일명 |
|------|--------|
| `# Python의 f-string` | `Python의-f-string.md` |
| `# Node.js가 싱글스레드라는 미신` | `Node.js가-싱글스레드라는-미신.md` |
| `# 왜 Spring은 CGLIB을 선택했을까?` | `왜-Spring은-CGLIB을-선택했을까.md` |

**특수문자 처리:** `/`, `?`, `:`, `*` 등은 제거 후 하이픈 변환

**저장 위치:** `/Users/sskim/dev/TIL/{category}/`

### Step 8: Self-Check 실행

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
- [ ] `mcp__mermaid-mcp__validate_and_render_mermaid_diagram`으로 렌더링 검증했는가?

#### 스타일 (CHECK)
- [ ] Bold 닫는 `**` 다음에 띄어쓰기가 있는가?
- [ ] 수식은 LaTeX로 작성했는가?
- [ ] 출처를 명시했는가?
- [ ] 문단 단위로 설명했는가?

## Verification

- mermaid 작성 즉시 → `mcp__mermaid-mcp__validate_and_render_mermaid_diagram`으로 렌더링 검증
- Self-Check 체크리스트 (Step 8) 통과 확인

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ mermaid에서 `\n` 사용 → `<br>` 사용해야 함
- ❌ subgraph에 style 지정 → subgraph는 style 미지원
- ❌ sequenceDiagram에서 `style` 사용 → `rect rgba()` 사용
- ❌ README.md 수정 시도 → GitHub Actions 자동 생성이므로 절대 금지
- ❌ "~는 ~이다" 정의 나열 → Why 중심 스토리텔링으로
- ❌ 리서치 없이 내부 지식만으로 작성 → 항상 tavily_search 먼저
- ❌ 파일명에 `/`, `?`, `:` 특수문자 포함 → 제거 후 하이픈 변환
- ❌ `git add/commit/push` 자동 실행 → 사용자가 명시적으로 요청할 때만

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| mermaid 렌더링 깨짐 | `\n` 사용 또는 color 누락 | `<br>` 사용, style에 color 명시 |
| Bold 뒤 텍스트 붙음 | `**` 뒤 띄어쓰기 누락 | `**텍스트** 뒤` 형태로 수정 |
| sequenceDiagram 스타일 무시됨 | `style` 미지원 | `rect rgba()` 사용 |
| 카테고리 미결정 | 주제가 여러 카테고리에 걸침 | 가장 핵심적인 기술 기준으로 선택 |
| 파일명 특수문자 에러 | 제목에 `/`, `?`, `:` 등 포함 | 특수문자 제거 후 하이픈 변환 |
