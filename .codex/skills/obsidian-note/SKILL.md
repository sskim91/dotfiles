---
name: obsidian-note
description: 개인 Obsidian vault에 일반 지식 노트를 작성·수정할 때 사용한다. GenOS·TIL·영상 노트는 전용 스킬을 사용한다.
---

# 개인 Obsidian 노트

일반 지식 노트 한 장을 개인 vault의 형식에 맞춰 작성·수정한다. 사용자가 준 자료와 현재 대화의 맥락·판단 근거를 충분히 보존한다.

## 저장 위치와 형식

- Vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note`
- 기본 저장 폴더: `_Inbox`; 템플릿: `Templates/Zettelkasten`
- 파일명: `{Title}.md` — 분류 접두사 없는 순수 제목
- 새 노트 또는 구조 변경은 [노트 형식](references/note-format.md)을 읽는다. `source`, `related_notes`, `tags`, `created` 필드와 Reading Spine이 이 vault의 규칙이다.
- 기존 문서를 수정할 때는 요청 범위와 기존 frontmatter를 보존한다.

## 작성 기준

기존 노트를 검색해 중복과 연결 후보를 확인하고, 한 노트의 핵심 판단을 분명히 한다. 본문은 맥락·작동 방식·조건부 판단·트레이드오프·실전 사용처를 설명한다. 대화의 비교 항목이나 예시를 한 줄씩 압축해 빠뜨리지 않는다.

사용자가 제공한 자료로 충분하면 바로 집필한다. 최신 사실이나 근거가 비어 있는 주장만 공식 출처로 확인한다. 검색 횟수나 검색 제공자를 고정하지 않는다.

`related_notes`에는 실존하는 노트만 넣는다. 연결 목록은 frontmatter에서 관리하고, 본문에서는 해당 맥락에 필요한 wikilink를 자연스럽게 사용한다.

저장 후 [post-write linking](references/post-write-linking.md)의 범위·절차에 따라 관련 노트 연결을 처리한다. 추가 문서 변경은 그 절차와 사용자가 허용한 범위를 따른다.

## 필요한 경우에만 읽는 자료

- 글쓰기 톤이나 설명 예시: [writing-style.md](references/writing-style.md), [complete-example.md](references/complete-example.md)
- Callout, embed, block ID 등 Obsidian 문법: [obsidian-syntax.md](references/obsidian-syntax.md)
- 팀 조사·심층 검증을 명시적으로 요청한 노트: `agentic-notes`가 수집·검증을 맡고 이 스킬은 최종 작성 규칙을 제공한다.
- GenOS 지식·패치노트, TIL, 영상은 해당 전용 스킬의 저장 형식을 따른다.

새로 만든 링크는 실제 파일 존재를 확인하고, Mermaid를 추가·변경했다면 렌더링해서 문법과 가독성을 확인한다. 사용하지 않은 기능의 검증은 추가하지 않는다.
