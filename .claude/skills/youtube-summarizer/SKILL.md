---
name: youtube-summarizer
description: Summarize YouTube videos into Obsidian Zettelkasten notes. Accepts YouTube URL (auto-downloads transcript) or raw transcript text. Use when user provides YouTube URL/link, mentions "youtube summarize", "video summary", "transcript to note", or wants to convert video content to Obsidian notes.
---

# YouTube → Obsidian Note

YouTube 영상을 Obsidian Zettelkasten 노트로 변환하는 스킬.
URL만 주면 트랜스크립트 자동 다운로드 → 번역/요약 → Obsidian 저장.

---

## 입력 처리

### YouTube URL이 주어진 경우 (자동 다운로드)

```bash
# URL 패턴 감지: youtube.com/watch?v=, youtu.be/
# 한국어 자막 우선, 실패 시 영어 폴백
python3 ~/.dotfiles/scripts/yt-transcript.py "$URL" -l kr -f json
```

스크립트가 JSON으로 반환:
- `video_id`: 영상 ID
- `url`: 원본 URL
- `segments`: 타임스탬프별 자막 세그먼트
- `full_text`: 전체 텍스트

### 트랜스크립트가 직접 주어진 경우

사용자가 붙여넣은 텍스트를 그대로 처리.

### URL도 트랜스크립트도 없는 경우

"YouTube URL 또는 트랜스크립트를 제공해주세요." 안내.

---

## 언어 옵션

사용자가 명시하지 않으면 **자동 판별**:
- 한국어 자막 존재 → 한국어 자막 사용 (요약만)
- 영어 자막만 존재 → 영어 자막 다운로드 → 한국어 번역 + 요약

사용자가 명시한 경우:
- `/youtube-summarizer kr <URL>` → 한국어 자막 우선
- `/youtube-summarizer en <URL>` → 영어 자막 우선 (번역 포함)

---

## 처리 프로세스

### 1단계: 트랜스크립트 확보

```
□ URL이면 yt-transcript.py로 자동 다운로드
□ 직접 제공이면 그대로 사용
□ 메타데이터 추출 (제목, 채널, 길이)
```

### 2단계: 기존 노트 검색

```bash
# Obsidian Vault에서 관련 노트 검색
Vault 경로: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note
```

- 주요 키워드로 기존 노트 검색
- **실존하는 노트만** `[[wikilink]]`로 연결

### 3단계: 문서 작성

아래 템플릿에 따라 작성.

### 4단계: 저장 및 검증

```
□ Write tool로 00.Inbox에 저장
□ Read tool로 파일 생성 확인
□ 실패 시 재시도
□ 검증 완료 후 경로 안내
```

---

## 문서 템플릿

```markdown
---
source:
  - YouTube URL
related_notes:
  - "[[실존하는_관련노트]]"
tags:
  - 도메인/하위주제
created: YYYY-MM-DD
---

## 핵심 요약

영상 전체 내용을 2-3 문단으로 요약.
첫 문단은 영상의 주제와 전체 흐름을 서술.
두 번째 문단은 핵심 방법론이나 인사이트를 서술.

## 주요 개념

영상에서 다룬 핵심 개념들을 정의와 함께 정리.
용어 설명은 **굵은 글씨**로 강조.
필요시 하위 섹션으로 구분.
(핵심 개념이 없는 영상은 이 섹션 생략)

## 상세 내용

### (00:00-05:00) 섹션 제목

섹션별 상세 요약 (2-3 문단).
불릿 포인트 나열보다 문단 서술을 우선.
중요한 인용구는 `> 인용` 형식 사용.
코드나 명령어는 코드 블록 사용.

### (05:00-10:00) 섹션 제목

...

## 결론 및 인사이트

1. 이 영상에서 얻은 핵심 교훈 (5-10개 문장)
2. 해당 정보가 왜 중요한지에 대한 인사이트
3. 실무에 적용할 수 있는 포인트

## 액션 아이템

- [ ] 추가 학습이 필요한 부분
- [ ] 실습해볼 내용

## 연결 고리

- [[관련노트]]: 이 노트와의 관계 설명
```

---

## 문서 번역 및 요약 규칙

### 대상 독자

- 컴퓨터 공학 전공, 소프트웨어 개발 경력 보유
- 영어 원문을 빠르게 읽기 어려움
- 관심 분야: OOP, TDD, Design Patterns, Refactoring, DDD, Clean Code, Architecture, Code Review, Agile, Spring Boot, AI 활용
- 학습한 내용을 정리해서 업무와 학습에 활용

### 번역 (영어 트랜스크립트인 경우)

- 기술 용어는 첫 등장 시 영문 병기: "테스트 주도 개발(Test-Driven Development)"
- 가능한 한 많은 원문 영어 용어를 포함
- 직역 우선, 자연스러운 한국어 표현
- 불확실한 부분은 `[?]` 마크로 명시
- 코드/명령어는 번역하지 않음
- **자연스러운 흐름 유지가 필수**: 원본의 말하기 순서와 구조를 유지하고 인위적 재구성 금지. 화자의 강조, 반복, 부연설명 패턴을 보존

### 요약 (한국어 트랜스크립트인 경우)

- 구어체를 문어체로 다듬되 핵심 내용 유지
- 같은 내용 반복은 한번으로 통합
- 시간순 섹션으로 나누어 구조화

### 공통 규칙

#### 요약 구조

1. **핵심 요약**: 전체 내용을 2-3 문단으로 요약
2. **상세 내용**: 약 5분 단위로 섹션을 나누고 각 섹션을 2-3 문단으로 상세 요약
3. **결론 및 인사이트**: 전체 내용을 5-10개 문장으로 정리하고 이 정보가 왜 중요한지 인사이트 제공

#### 섹션 분할 기준

| 트랜스크립트 길이 | 섹션 분할 |
|-------------------|-----------|
| ~10분 | 2-3 섹션 |
| 10-30분 | 5분 단위 |
| 30분+ | 주제별 논리적 단위 |

#### 서식

- **제목 계층**: ## (주요 섹션) > ### (하위 섹션) > #### (세부 항목)
- **강조**: 중요 개념은 **굵은 글씨**, 용어는 _이탤릭_
- **코드**: 인라인 코드는 `backticks`, 블록은 ``` 사용
- **다이어그램**: 필요시 Mermaid 다이어그램 활용
- 영상 10분당 최소 1,000자 이상
- 내용이 없는 섹션은 제거

#### 품질 기준

- 원문에 없는 정보 추가 금지 (트랜스크립트 내용만)
- 코드 예제 누락 없이 포함 (모든 코드 블록 확인)
- 연결 노트 실존 확인 (`[[링크]]` 전에 검색)
- 핵심 요약만 읽어도 전체 내용 파악 가능
- 불확실한 부분은 명시적으로 표시
- 최종 정보를 자체 검증 후 작성

---

## 저장 규칙

| 항목 | 값 |
|------|-----|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 저장 위치 | `00.Inbox` |
| 파일명 | `{Title}.md` — 순수 제목, 접두사 없음 (예: `RAG 파이프라인 구축 가이드.md`) |

---

## Frontmatter 필드 설명

| 필드 | 설명 |
|------|------|
| `source` | 원본 YouTube URL |
| `related_notes` | 실존하는 관련 Obsidian 노트 (wikilink) |
| `tags` | 계층형 태그 (도메인/하위주제) |
| `created` | 파일 생성 날짜 |

필드 순서: `source` → `related_notes` → `tags` → `created`
