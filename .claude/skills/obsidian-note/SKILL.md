---
name: obsidian-note
description: Use when user mentions "Obsidian", "옵시디언", "write as note", "save to notes", "노트로 저장", or /obsidian-note command. Do NOT use for TIL (use til), YouTube notes (use youtube-summarizer), GenOS 작업 지식 캡처 (use genos-knowledge-capture), or deep/team/multi-angle note research (use agentic-notes).
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

### 본문 구조

```markdown
## 핵심 아이디어                    ← [필수] hook. 왜 이게 중요한지, 한 문단으로 긴장감 있게
> 핵심을 한 문장으로. 정의가 아니라 통찰.

---

## {주제에 맞는 자유 섹션들}        ← [자유] 내용의 깊이를 담는 본문
- 섹션 제목은 주제에 맞게 자유롭게 ("상세 설명" 같은 제네릭 제목 지양)
- trade-off와 판단을 반드시 포함. 근거(사례, 수치 등)로 뒷받침

---

## 더 알아보기                      ← [필수] 후속 탐구 방향
- 구체적인 후속 질문 (단순 키워드 나열 금지)
```

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
핵심 아이디어를 hook으로 시작. 리서치 결과를 종합하여 글쓰기 스타일 5원칙 준수. 출처 명시.

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
□ trade-off 분석 포함 (장점만 나열 안 했는가)
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

## Obsidian 마크다운 문법

Callout, embed, wikilink 변형, block ID, highlight, math, footnote 등 Obsidian 고유 문법은
[references/obsidian-syntax.md](references/obsidian-syntax.md) 참조.

> `.base`/`.canvas` 파일이 필요해지면 [help.obsidian.md/bases](https://help.obsidian.md/bases),
> [jsoncanvas.org/spec/1.0](https://jsoncanvas.org/spec/1.0/) 공식 문서를 보고
> 별도 커스텀 스킬로 만들 것 (공식 플러그인 스킬은 비활성화됨).
