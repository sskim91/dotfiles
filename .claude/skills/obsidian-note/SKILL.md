---
name: obsidian-note
description: Use when user mentions "Obsidian", "옵시디언", "write as note", "save to notes", "노트로 저장", or /obsidian-note command. Do NOT use for TIL (use til), YouTube notes (use youtube-summarizer), GenOS 작업 지식 캡처 (use genos-knowledge-capture), GenOS 패치노트·릴리스 노트 (use write-genos-patch-notes), or deep/team/multi-angle note research (use agentic-notes).
---

# Zettelkasten Note Writer

**원자적 노트로 지식을 연결하는 Obsidian 노트 작성 가이드**

## 책임 경계

이 skill은 **leaf writer**다. 최종 Obsidian 노트 1장을 작성하고, frontmatter, 원자성, 글쓰기 톤, wikilink, Post-write linking 품질을 책임진다.

무거운 멀티 에이전트 수집, strict verification, claim ledger, 여러 역할의 팀 운영이 필요하면 `agentic-notes`를 사용한다. `agentic-notes`가 수집·검증·합성을 끝낸 뒤, 이 skill의 writer 규칙으로 최종 노트를 저장한다.

도구 매핑:
- Claude Code: 웹 수집은 `tavily_search` 또는 `WebSearch`, vault 조사는 `Grep`/`Read`를 사용한다.
- Codex: 웹 수집은 사용 가능한 search tool 또는 `web.run search_query`, vault 조사는 `rg`와 파일 read를 사용한다.

## 기본 설정

| 항목 | 경로/규칙 |
|------|-----------|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 템플릿 위치 | `Templates/Zettelkasten` |
| 저장 위치 | `_Inbox` |
| 파일명 규칙 | `{Title}.md` — 순수 제목, 접두사 없음 (예: `RAG 시스템 아키텍처.md`) |

## 노트 구조

### Frontmatter 템플릿

```yaml
---
source:              # 출처 URL (있으면)
related_notes:       # wikilink 연결 (있으면)
  - "[[실존하는_노트1]]"
  - "[[실존하는_노트2]]"
tags:                # 계층형 태그
  - domain/topic
created: YYYY-MM-DD  # 작성일
---
```

### Frontmatter 보존 규칙

frontmatter는 vault 호환성, 검색, 링크 후보 관리를 위한 메타데이터다. 본문 구조를 개선하더라도 다음 필드명과 형태를 바꾸지 않는다.

- `source`
- `related_notes`
- `tags`
- `created`

새 필드를 임의로 추가하지 않는다. claim ledger, 판단 근거, 연결 설명처럼 길어지는 정보는 본문에 둔다.

### 본문 구조

```markdown
## 핵심 아이디어
> 이 노트가 나중에 다시 꺼내 쓰려는 판단 한 문장. 정의가 아니라 통찰.

---

## 맥락
이 생각이 왜 등장했는지 설명한다. 어떤 대화, 문제, 설계, 코드, 글을 보다가 필요해졌는지 적는다.

## 핵심 모델
개념의 작동 방식, 구조, 구성요소, 흔한 오해를 자기 언어로 풀어쓴다.

## 판단
그래서 내가 받아들이는 결론을 적는다. 언제 맞고, 언제 틀리고, 어떤 조건에서 써야 하는지까지 쓴다.

## 트레이드오프
무엇을 얻고 무엇을 포기하는지 적는다. 장점만 쓰지 않는다.

## 써먹는 곳
코드 리뷰, 설계 판단, 장애 분석, 학습, 고객 설명 등 실제로 다시 꺼내 쓸 상황을 적는다.

---

## 남은 질문
- 아직 불확실한 점
- 다음에 확인할 자료
- 이 노트가 자라날 방향
```

### Reading Spine

본문은 기본적으로 `핵심 아이디어 → 맥락 → 핵심 모델 → 판단 → 트레이드오프 → 써먹는 곳 → 남은 질문` 흐름을 따른다.

주제에 더 자연스러운 제목이 있으면 바꿔도 되지만, 역할은 유지한다.

| 기본 섹션 | 역할 | 대체 제목 예시 |
|-----------|------|----------------|
| `맥락` | 이 생각이 등장한 배경과 긴장감 | `출발점`, `등장 배경` |
| `핵심 모델` | 구조, 동작 원리, 구성요소, 흔한 오해 | `작동 방식`, `내부 구조` |
| `판단` | 조건부 결론과 적용 기준 | `내 기준`, `선택 기준` |
| `트레이드오프` | 얻는 것과 잃는 것 | `현실적인 비용`, `대가` |
| `써먹는 곳` | 나중에 다시 사용할 실전 맥락 | `적용 메모`, `실전 감각` |
| `남은 질문` | 아직 열려 있는 질문과 후속 탐구 | `더 알아보기`, `다음 질문` |

### 연결 중복 방지

본문에 `## 연결` 섹션을 만들지 않는다. 연결 대상 목록은 frontmatter `related_notes`에만 기록한다.

본문에서 관련 노트를 언급해야 할 때는 별도 목록을 만들지 말고, 해당 문맥 안에서 자연스럽게 `[[노트명]]`을 1회 사용한다.

### 설명 밀도

짧게 요약하려고 정보를 압축하지 않는다. 이 노트는 나중에 다시 읽을 문서이므로, 당시의 맥락을 모르는 미래의 내가 읽어도 이해될 만큼 충분히 설명한다.

- 불릿만 나열하지 말고 각 항목이 왜 중요한지 문장으로 풀어쓴다.
- “핵심만 요약”보다 “맥락과 판단 근거를 보존”하는 쪽을 우선한다.
- 대화에서 나온 번호 매긴 항목, 비교 기준, 예시는 같은 깊이로 다룬다.
- 길어져도 괜찮다. 정보가 빠져서 나중에 의미를 복원하지 못하는 것이 더 나쁘다.

## 작성 프로세스

### 1단계: 리서치 (수집)

**기본 (단일 에이전트):** `tavily_search`로 최소 2회 검색. 실전 사례, trade-off, 최신 동향, 출처 URL 수집.

**팀 모드 (서브에이전트 fan-out) — 아래 신호일 때만 발동:**
- `--team [N]` 플래그 (N 생략 시 3; 3~5 권장, "focused 3 > scattered 5")
- 자연어 신호: "깊게 조사해서 / 팀으로 / 여러 각도로 조사해서" + 노트 요청
- 주제가 넓거나 익숙치 않으면 "팀 모드를 권할까요?" 제안 (강제 금지)

팀 모드 신호가 있으면 이 skill에서 직접 팀을 운영하지 말고 `agentic-notes`로 넘긴다. `agentic-notes`가 수집·검증·합성을 완료한 뒤, 이 skill은 최종 writer로 호출되어 2단계부터 진행한다.

> **비용 주의:** 팀 모드는 토큰 ~N배. 단순/익숙한 주제엔 기본(단일)을 쓴다.
> **충돌 회피:** 팀 수집 단계에서도 서브에이전트는 read-only 수집만, vault 쓰기(노트 1장)는 lead 또는 `note-writer`만 단독 수행한다.

### 2단계: 기존 노트 조사
동일/유사 주제 기존 노트 검색. 연결 가능한 노트 식별 (related_notes용). 범위를 원자적 단위로 제한.

### 3단계: 집필
핵심 아이디어를 hook으로 시작. 리서치 결과를 종합하여 Reading Spine과 글쓰기 스타일 5원칙을 따른다. 출처와 판단 근거를 함께 명시한다.

### 4단계: 시각화 (필요시)
복잡한 개념은 mermaid/ASCII 다이어그램. 비교표(table)로 trade-off를 한눈에.

### 5단계: Post-write linking
노트 저장 완료 후 [post-write-linking.md](references/post-write-linking.md)의 절차를 실행한다.
vault에서 관련 노트를 검색하고 양방향 `[[wikilink]]`를 연결한다.

## 향후: 엄격 검증 버전 (Phase 2)

현재 팀 모드의 검증은 "lead 교차확인"(가벼움)이다. "가짜 정보 절대 안 됨" 수준이 필요해지면 `agentic-notes --verify strict` 또는 `agentic-notes --deep`를 사용한다. 이 skill 안에서는 최종 writer 규칙만 유지한다.

## Mermaid 핵심 규칙

- 밝은 배경에는 반드시 `color:#000` 지정 (미지정 시 흰 글씨로 안 보임)
- 어두운 배경에는 `color:#fff` 지정
- `\n` 사용 금지 — mermaid에서 줄바꿈은 `<br>`
- subgraph에 직접 style 적용 불가 — 내부 노드에 style 적용
- 검증: `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`으로 렌더링 확인

## References

| 파일 | 내용 |
|------|------|
| `references/writing-style.md` | 페르소나, 5원칙, 금지 패턴, Before/After, 톤 체크, 노트 유형, 품질 기준 |
| `references/complete-example.md` | CAP 정리 완성 노트 예시 |
| `references/post-write-linking.md` | Post-write linking 절차 (양방향 링킹, 후속 탐구 큐) |
| `references/obsidian-syntax.md` | Obsidian 고유 문법 (wikilink/embed/callout/block-id/highlight/math/footnote) |

## Gotchas

- **밝은 배경 color 미지정**: `fill:#E3F2FD`만 쓰면 자동 흰색 글씨 → 반드시 `color:#000` 추가
- **여러 개념 한 노트**: 원자성 위반. 한 노트 = 한 아이디어. 쪼갤 수 있으면 쪼개라
- **대화 내용 축약 금지**: 대화에서 다룬 번호 매긴 항목(1~N번)을 노트로 옮길 때, 일부를 한 줄 테이블로 압축하거나 "나머지는 빠르게" 식으로 생략하지 마라. 모든 항목을 동일한 깊이로 작성. 노트가 길어지는 건 괜찮다 — 내용이 빠지는 게 더 문제
- **정의 나열**: "~는 ~이다" 위키피디아 톤 금지. hook + 분석 + 판단이 있어야 함
- **존재하지 않는 노트 링크**: related_notes의 모든 `[[wikilink]]`는 실존 노트만 기록
- **mermaid `\n` 사용**: 줄바꿈은 `<br>` 사용. `\n`은 문자 그대로 출력됨
- **subgraph style**: subgraph 자체에 style 불가. 내부 노드에 개별 적용

## 작성 후 체크리스트

```markdown
□ Tavily 리서치 수행 완료 (단일: 최소 2회 / 팀 모드: 각 서브에이전트 최소 1회)
□ frontmatter source에 출처 기록
□ related_notes의 모든 링크가 실존하는 노트
□ 핵심 아이디어가 "정의"가 아닌 "통찰/hook"으로 시작
□ Reading Spine이 유지되었는가 (핵심 아이디어 → 맥락 → 핵심 모델 → 판단 → 트레이드오프 → 써먹는 곳 → 남은 질문)
□ 본문에 `## 연결` 섹션을 만들지 않았는가 (연결 목록은 related_notes에만)
□ trade-off 분석 포함 (장점만 나열 안 했는가)
□ 짧게 요약하려고 정보를 압축하지 않았는가 (미래의 내가 읽어도 맥락 복원 가능)
□ 위키피디아 톤이 아닌 엔지니어링 블로그 톤
□ 대화의 모든 번호 항목이 동일 깊이로 포함되었는가 (축약/생략 없음)
□ 파일명이 순수 제목 (접두사 없음), created 날짜 현재
□ mermaid 사용 시 렌더링 검증 완료
□ Post-write linking 실행 완료 (관련 노트 검색 + related_notes 업데이트)
□ (팀 모드 시) 서브에이전트는 read-only 수집만 했고 vault 쓰기는 lead 단독
□ (팀 모드 시) 여러 팀원 출처가 인용에 반영, 모순은 "⚠️ 이견 있음" 병기
```

## Verification

노트 작성 완료 후:
- mermaid 사용 시 → `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`으로 렌더링 확인
- related_notes의 `[[wikilink]]` → Vault에 실존하는 노트인지 확인
- frontmatter source → URL 유효성 확인
- 본문 구조 → Reading Spine, 연결 중복 방지, 설명 밀도 체크리스트 확인

## Obsidian 마크다운 문법

Callout, embed, wikilink 변형, block ID, highlight, math, footnote 등 Obsidian 고유 문법은
[references/obsidian-syntax.md](references/obsidian-syntax.md) 참조.

> `.base`/`.canvas` 파일이 필요해지면 [help.obsidian.md/bases](https://help.obsidian.md/bases),
> [jsoncanvas.org/spec/1.0](https://jsoncanvas.org/spec/1.0/) 공식 문서를 보고
> 별도 커스텀 스킬로 만들 것 (공식 플러그인 스킬은 비활성화됨).
