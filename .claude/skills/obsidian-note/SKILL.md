---
name: obsidian-note
description: Use when user mentions "Obsidian", "옵시디언", "write as note", "save to notes", "노트로 저장", or /obsidian-note command. Do NOT use for TIL (use til) or YouTube notes (use youtube-summarizer).
---

# Zettelkasten Note Writer

**원자적 노트로 지식을 연결하는 Obsidian 노트 작성 가이드**

## 기본 설정

| 항목 | 경로/규칙 |
|------|-----------|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 템플릿 위치 | `Templates/Zettelkasten` |
| 저장 위치 | `Inbox` |
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

### 1단계: 리서치 (Tavily)
`tavily_search`로 최소 2회 검색. 실전 사례, trade-off, 최신 동향, 출처 URL 수집.

### 2단계: 기존 노트 조사
동일/유사 주제 기존 노트 검색. 연결 가능한 노트 식별 (related_notes용). 범위를 원자적 단위로 제한.

### 3단계: 집필
핵심 아이디어를 hook으로 시작. 리서치 결과를 종합하여 글쓰기 스타일 5원칙 준수. 출처 명시.

### 4단계: 시각화 (필요시)
복잡한 개념은 mermaid/ASCII 다이어그램. 비교표(table)로 trade-off를 한눈에.

### 5단계: Post-write linking
노트 저장 완료 후 [post-write-linking.md](references/post-write-linking.md)의 절차를 실행한다.
vault에서 관련 노트를 검색하고 양방향 `[[wikilink]]`를 연결한다.

## Mermaid 핵심 규칙

- 밝은 배경에는 반드시 `color:#000` 지정 (미지정 시 흰 글씨로 안 보임)
- 어두운 배경에는 `color:#fff` 지정
- `\n` 사용 금지 — mermaid에서 줄바꿈은 `<br>`
- subgraph에 직접 style 적용 불가 — 내부 노드에 style 적용
- 검증: `mcp__mermaid-mcp__validate_and_render_mermaid_diagram`으로 렌더링 확인

## References

| 파일 | 내용 |
|------|------|
| `references/writing-style.md` | 페르소나, 5원칙, 금지 패턴, Before/After, 톤 체크, 노트 유형, 품질 기준 |
| `references/complete-example.md` | CAP 정리 완성 노트 예시 |
| `references/post-write-linking.md` | Post-write linking 절차 (양방향 링킹, 후속 탐구 큐) |

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
□ Tavily 리서치 수행 완료 (최소 2회 검색)
□ frontmatter source에 출처 기록
□ related_notes의 모든 링크가 실존하는 노트
□ 핵심 아이디어가 "정의"가 아닌 "통찰/hook"으로 시작
□ trade-off 분석 포함 (장점만 나열 안 했는가)
□ 위키피디아 톤이 아닌 엔지니어링 블로그 톤
□ 대화의 모든 번호 항목이 동일 깊이로 포함되었는가 (축약/생략 없음)
□ 파일명이 순수 제목 (접두사 없음), created 날짜 현재
□ mermaid 사용 시 렌더링 검증 완료
□ Post-write linking 실행 완료 (관련 노트 검색 + related_notes 업데이트)
```

## Verification

노트 작성 완료 후:
- mermaid 사용 시 → `mcp__mermaid-mcp__validate_and_render_mermaid_diagram`으로 렌더링 확인
- related_notes의 `[[wikilink]]` → Vault에 실존하는 노트인지 확인
- frontmatter source → URL 유효성 확인

## Obsidian 마크다운 문법

Callout, embed, property 타입 등 Obsidian 고유 문법은 `obsidian:obsidian-markdown` 스킬 참조.
