---
name: til
description: 학습 내용을 개인 TIL 저장소의 형식과 저장 규칙에 맞춰 기록할 때 사용한다.
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

**파일명 = 제목에서 공백을 하이픈으로 변환:**

| 제목 | 파일명 |
|------|--------|
| `# Python의 f-string` | `Python의-f-string.md` |
| `# Node.js가 싱글스레드라는 미신` | `Node.js가-싱글스레드라는-미신.md` |
| `# 왜 Spring은 CGLIB을 선택했을까?` | `왜-Spring은-CGLIB을-선택했을까.md` |

**특수문자 처리:** 따옴표 `' "`는 그냥 지운다. `/ ? : * ( ) [ ] , @ =`는 공백으로 바꾼 뒤 공백을 하이픈으로 변환한다(단어가 붙지 않게). `.`은 유지한다(`Node.js`). 연속 하이픈은 하나로 줄이고, 앞뒤 하이픈은 지운다.

예: `# Node.js/Deno 비교: list[tuple]은?` → `Node.js-Deno-비교-list-tuple-은.md`

**저장 위치:** `/Users/sskim/dev/TIL/{category}/`

### Step 8: 태그 매핑 등록 (커밋 전)

공통 규칙: `~/.dotfiles/vault/references/note-rules.md` (4절 TIL 파생 노트, 2절 태그). TIL 노트는 커밋 시 post-commit 동기화가 Wiki 노트로 만든다. 태그는 `~/dev/TIL/tag-mapping.json`이 정본이므로, 커밋 전에 til-tagger의 분류 규칙으로 새 파일의 항목을 추가한다. til-tagger는 스킬로 호출되지 않을 수 있으니 `~/.dotfiles/.codex/skills/til-tagger/SKILL.md`의 "2. Classify tags"·"Tag Guidelines" 절을 직접 읽고 따른다.

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

### Step 10: Claude·Antigravity 교차 검토

Self-Check가 끝난 새 문서 또는 내용이 변경된 TIL마다 아래 명령을 실행한다. 작성 중간의 개별 편집마다 호출하지 않는다. 사용자가 이번 작업의 외부 리뷰 생략을 명시했다면 생략 사실을 완료 보고에 남긴다.

```bash
python3 ~/.dotfiles/.codex/skills/til/scripts/review.py "/Users/sskim/dev/TIL/{category}/{파일명}.md"
```

실행기는 동일한 문서 사본을 **Claude(공식 출처·기술 사실)** 와 **Antigravity(논리·전제·독자 이해)** 에 병렬 전달한다. [review-rubric.md](references/review-rubric.md)가 공통 검토 기준이다. 리뷰어는 검토 의견을 반환하고, 원문 수정과 최종 판단은 작성자인 Codex가 맡는다.

Claude는 WebSearch/WebFetch만 허용하고 리뷰 세션의 훅을 끈다. Antigravity는 임시 작업 디렉터리에서 `--mode plan --sandbox`와 도구 호출 금지 지침으로 실행한다. 후자는 OS 수준의 파일 읽기 전용 격리를 보장하는 옵션은 아니다. 두 리뷰어에게 원문 경로는 전달하지 않으며, 검토 후 원문이 달라졌다면 `ERROR`로 판정한다.

- `claude`와 `agy`가 PATH에 있고 로그인되어 있어야 한다. 모델은 각 CLI 기본 설정을 사용한다. 필요하면 `--claude-model`, `--antigravity-model`로 이번 실행만 지정한다.
- 기본 제한은 리뷰어별 240초이며 자동 재시도는 없다. `--timeout`으로 조정한다. CLI 응답·stderr·문서 사본·SHA-256·종합 판정은 출력된 임시 디렉터리에 보존된다. `--output-dir`에는 아직 없는 새 디렉터리를 지정할 수 있다.
- 두 리뷰 본문과 `result.json`을 읽는다. 종료 코드 `0`/`PASS`는 두 리뷰 모두 Blocker가 없다는 뜻이며, Refinement와 Insight도 확인한다.
- 종료 코드 `1`/`FAIL`이면 Blocker의 근거를 검증한다. 타당한 지적은 수정하고 변경본을 다시 검토한다. 잘못된 지적은 근거와 함께 기각하되 실제 FAIL 결과를 PASS로 바꾸어 보고하지 않는다.
- 종료 코드 `2`/`ERROR`는 CLI 실패·시간 초과·형식 오류·검토 중 원본 변경이다. 통과로 취급하지 말고 로그를 확인해 원인과 미검토 범위를 보고한다. 재실행은 원인을 해결했을 때만 한다.
- 문서 수정에 따른 재검토는 최초 검토 뒤 최대 2회다. 여전히 Blocker가 남거나 의견이 충돌하면 현재 문서와 남은 쟁점을 보고하고 반복을 멈춘다.
- 완료 보고에는 **파일 경로, 태그 등록, Claude/Antigravity 각각의 상태, 반영·기각한 핵심 의견, 미해결 항목과 리뷰 결과 경로**를 포함한다. 교차 검토는 커밋·푸시 권한을 추가하지 않는다.

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
