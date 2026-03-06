# Obsidian Flashcard - from-note Guide

## --from-note: Obsidian Vault에서 기존 노트 변환

Obsidian Vault에서 기존 노트를 검색하고 플래시카드로 변환합니다.

### 프로세스

```
Step 1: 노트 검색
  - Vault 경로에서 키워드로 노트 검색
  - 파일명 또는 내용에서 매칭

Step 2: 노트 선택
  - 검색 결과 목록 표시
  - 사용자가 변환할 노트 선택

Step 3: 내용 분석
  - 노트 구조 파악 (헤딩, 코드블록, 리스트)
  - 핵심 개념 추출

Step 4: 플래시카드 변환
  - 헤딩 -> 섹션 구분
  - 정의/설명 -> Q&A 카드
  - 순서/흐름 -> Cloze 카드
  - 코드 예시 -> 코드 카드

Step 5: 저장
  - FC-{원본노트명}.md 로 저장
  - 원본 노트 링크 추가
```

### 검색 경로

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/
  00.Inbox/
  09.TIL/          <- TIL 노트
  01.Projects/
  ...
```

### 변환 규칙

| 원본 노트 구조 | 플래시카드 변환 |
|---------------|----------------|
| `## 헤딩` | 섹션 구분자 |
| `**용어**: 정의` | `용어:::정의` |
| `- 항목1, 항목2` | Multi-line Q&A |
| 코드 블록 (전/후 비교) | `Before:::After` |
| 순서 설명 | Cloze `==키워드==` |
| `> 인용문` | 핵심 개념 추출 |

### 예시

**명령:**
```bash
/obsidian-flashcard --from-note "Spring Framework 7"
```

**검색 결과:**
```
"Spring Framework 7" 검색 결과:

1. 09.TIL/Spring-Framework-7.0.md
2. 09.TIL/Spring-Framework-7-API-Versioning.md
3. 09.TIL/Spring-Framework-7-HTTP-Service-Client.md

어떤 노트를 플래시카드로 변환할까요? (번호 또는 'all')
```

**변환 후:**
```markdown
---
created: 2026-02-02
tags:
  - flashcard
source: "[[Spring-Framework-7.0]]"
---

#flashcards/spring

## 시스템 요구사항

Spring Framework 7.0의 최소 Java 버전은?::JDK 17 (권장: JDK 25 LTS)

---

> 생성: Claude Code /obsidian-flashcard --from-note
> 원본: [[Spring-Framework-7.0]]
```

### 변환 품질 향상 팁

1. **원본 노트가 잘 구조화되어 있을수록** 변환 품질이 높음
2. **결론부터/핵심 요약** 섹션이 있으면 좋은 카드 생성
3. **Before/After 코드 비교**가 있으면 양방향 카드로 변환
4. **Why 설명**이 있으면 Why 질문 카드 생성

### --from-note 체크리스트

```markdown
- [ ] 원본 노트에서 핵심 5-10개만 추출
- [ ] 단순 버전/숫자 정보는 제외
- [ ] source 필드에 원본 노트 링크 추가
- [ ] 실무에서 바로 써먹을 지식만 포함
- [ ] 푸터에 원본 노트 링크 명시
```
