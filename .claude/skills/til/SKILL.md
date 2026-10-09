---
name: til
description: Use when user mentions "TIL", "write TIL", "TIL 작성", "learning note", or /til command. Do NOT use for Obsidian notes (use obsidian-note) or blog posts.
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

- 인자가 있으면(`/til "주제"`) 그 주제로, 없으면(`/til`) 어떤 주제로 쓸지 먼저 묻는다.
- 카테고리는 `~/dev/TIL`의 기존 최상위 폴더다(`scripts` 제외). 매번 `command ls -d ~/dev/TIL/*/`로 목록을 확인하고, 폴더별 작성 특성은 [category-guide.md](references/category-guide.md)를 참조해 하나를 제안한다.
- 주제가 여러 카테고리에 걸치면 가장 핵심적인 기술 기준으로 고른다. 맞는 폴더가 없을 때만 새 폴더를 제안하고, 사용자 확인 후 만든다.
- 사용자가 주제·카테고리를 확인하면 작성을 시작한다.

### Step 2: 리서치

작성 전 `tavily_search`로 주제를 검색하여(쓸 수 없으면 `brave_web_search` → `WebSearch` 순) 최신 정보와 공식 문서 URL을 확보한다. 할루시네이션 방지와 정확한 출처 확보를 위해 **항상 실행**한다.

### Step 3: 문서 구조 작성

[til-template.md](assets/til-template.md)의 템플릿을 기반으로 작성.

**필수 섹션:**
- `# <기술명> — <부제>` (기술명은 정렬·검색용 라벨이고, 호기심은 부제가 맡는다. 부제는 생략할 수 있으며, 그때는 바로 아래 한 줄 설명이 호기심을 맡는다. 기술명 고르는 법은 Step 7)
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
- **빌드업으로 처음 보는 독자도 따라오게** — 핵심 용어를 정의 없이 사용 금지. 도구 정의 → 직관적 기대 → 직관이 무너지는 순간 → 해법 순서로 쌓을 것 (writing-style-guide.md 6절)
- **연결어로 흐름 만들기** — 단락 간 자연스러운 전환
- **문단 단위로 설명** — 한 줄씩 끊지 말 것

### Step 5: 시각화 규칙

[mermaid-style-guide.md](references/mermaid-style-guide.md)를 읽고 아래 규칙을 적용:

- ASCII 박스 금지 → 테이블 또는 mermaid 사용
- 어두운 배경 + 흰 글씨: `style Node fill:#1565C0,color:#fff`
- 줄바꿈은 `<br>` 사용 (`\n` 아님)
- subgraph에는 style 지정하지 않음
- sequenceDiagram은 `style` 대신 `rect rgba()` 사용

### Step 6: 스타일 규칙

[writing-style-guide.md](references/writing-style-guide.md)의 스타일 규칙 섹션을 참조:

- Bold 닫는 `**` 다음에 반드시 띄어쓰기
- 수식은 LaTeX (`$...$`, `$$...$$`)
- 출처는 `## 출처` 섹션에 공식 문서 최상단 배치

### Step 7: 파일 저장

**제목은 핵심 기술명으로 시작한다.** Obsidian Wiki에는 모든 TIL이 한 폴더에 모이므로, 같은 기술의 노트가 이름순으로 나란히 서게 한다.

- 기술 폴더(java, python, spring, kubernetes, redis 등): 폴더 기술명으로 시작한다(`Redis`, `Docker`). 노트가 다른 구체 기술을 다루면 그 기술명으로 시작해도 된다(`FastAPI`, `Helm`).
- 도메인 폴더(ai, database, security, computer-science, web 등): 노트가 설명하는 대상 하나를 고른다. 기준은 Wiki에서 같이 묶여 보이길 원하는 단어다(`BM25`, `Kerberos`, `Covering Index`).
- 표기는 공식 표기를 따르고(`MySQL`, `NGINX`, `OAuth`), 일반 개념은 영어 Title-Case로 쓴다. 같은 대상을 다룬 기존 노트가 있으면 그 철자에 맞춘다(`command ls ~/dev/TIL/<폴더>/`로 확인).

**파일명 = 제목에서 공백을 하이픈으로 변환:**

| 제목 | 파일명 |
|------|--------|
| `# Python의 f-string` | `Python의-f-string.md` |
| `# Node.js가 싱글스레드라는 미신` | `Node.js가-싱글스레드라는-미신.md` |
| `# Spring CGLIB — 왜 CGLIB 프록시를 기본으로 선택했을까?` | `Spring-CGLIB-왜-CGLIB-프록시를-기본으로-선택했을까.md` |

**특수문자 처리:** 따옴표 `' "`와 백틱(`` ` ``)은 그냥 지운다. `/ ? : * ( ) [ ] , @ =`와 `—`는 공백으로 바꾼 뒤 공백을 하이픈으로 변환한다(단어가 붙지 않게). `.`은 유지한다(`Node.js`). 연속 하이픈은 하나로 줄이고, 앞뒤 하이픈은 지운다.

예: `# Node.js/Deno 비교: list[tuple]은?` → `Node.js-Deno-비교-list-tuple-은.md`, `` # Helm — 내 첫 Helm Chart, `helm create`부터 `` → `Helm-내-첫-Helm-Chart-helm-create부터.md`

**저장 위치:** `/Users/sskim/dev/TIL/{category}/`

### Step 8: 태그 매핑 등록 (커밋 전)

공통 규칙: `~/.dotfiles/vault/references/note-rules.md` (4절 TIL 파생 노트, 2절 태그). TIL 노트는 커밋 시 post-commit 동기화가 Wiki 노트로 만든다. 태그는 `~/dev/TIL/tag-mapping.json`이 정본이므로, 커밋 전에 til-tagger의 분류 규칙으로 새 파일의 항목을 추가한다. til-tagger는 스킬로 호출되지 않을 수 있으니(설정에서 꺼짐) `~/.dotfiles/.claude/skills/til-tagger/SKILL.md`의 "2. Classify tags"·"Tag Guidelines" 절을 직접 읽고 따른다.

```json
"<파일명-확장자-제외>": ["domain/sub"]
```

- `domain`은 policy 허용 목록에서 고른다: `jq -r '.tags.domains[]' ~/.dotfiles/vault/vault-policy.json`
- 항목이 없으면 Wiki 노트에 `<til_folder_domain 또는 폴더>/untagged` 태그(예: `computer-science` → `cs/untagged`)가 붙어 `vk check`에 걸린다.
- 추가 후 JSON 유효성을 확인한다: `python3 -m json.tool ~/dev/TIL/tag-mapping.json > /dev/null`
- `git add/commit`은 사용자가 요청할 때만 한다. 커밋 대상에 새 노트와 `tag-mapping.json`을 함께 넣는다.

### Step 9: Self-Check 실행

문서 작성 완료 후 아래 항목 점검:

#### 필수 (MUST)
- [ ] **"왜"를 설명했는가?**
- [ ] **스토리텔링으로 풀어갔는가?**
- [ ] **빌드업이 충분한가?** — 검색으로 처음 들어온 독자가 첫 섹션에서 막히는 핵심 용어가 있는가? 모든 핵심 용어가 등장 시점에 정의되어 있는가?
- [ ] "결론부터 말하면" 섹션이 있는가?
- [ ] 파일명이 제목과 일치하는가?
- [ ] 제목이 핵심 기술명으로 시작하는가?
- [ ] 카테고리가 기존 TIL 폴더인가?
- [ ] `tag-mapping.json`에 새 파일 항목을 추가했는가?

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

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ mermaid에서 `\n` 사용 → `<br>` 사용해야 함
- ❌ subgraph에 style 지정 → subgraph는 style 미지원
- ❌ sequenceDiagram에서 `style` 사용 → `rect rgba()` 사용
- ❌ mermaid style에 `color` 누락 → 글씨가 안 보이니 `fill`과 `color:#fff`를 함께 지정
- ❌ Bold 닫는 `**` 바로 뒤에 글자를 붙임 → 렌더링이 깨지니 `**텍스트** 뒤`처럼 띄어쓰기
- ❌ README.md 수정 시도 → GitHub Actions 자동 생성이므로 절대 금지
- ❌ "~는 ~이다" 정의 나열 → Why 중심 스토리텔링으로
- ❌ 핵심 용어를 정의 없이 사용 → 등장 시점에 1줄이라도 정의를 깔거나 빌드업 4단계(도구 정의→직관→직관 붕괴→해법)로 쌓아라
- ❌ 리서치 없이 내부 지식만으로 작성 → Step 2 검색을 먼저 실행
- ❌ 파일명에 특수문자 포함 → Step 7의 제거 목록대로 지운 뒤 하이픈 변환
- ❌ `git add/commit/push` 자동 실행 → 사용자가 명시적으로 요청할 때만
