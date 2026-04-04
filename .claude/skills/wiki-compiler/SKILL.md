---
name: wiki-compiler
description: Use when user says "wiki compile", "위키 컴파일", "raw 정리", "지식 컴파일", "소스 컴파일", or wants to compile raw sources into a structured wiki. Do NOT use for individual note creation (use obsidian-note) or vault maintenance (use vault-linter).
---

# Wiki Compiler

raw 소스 디렉토리의 문서들을 읽고 구조화된 .md 위키로 "컴파일"하는 스킬.
Karpathy의 "LLM Knowledge Base Compile" 패턴 — raw → 개념 추출 → 아티클 생성 → 인덱스 유지.

## 기본 설정

| 항목 | 값 |
|------|-----|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 기본 raw 경로 | 사용자 지정 (예: `{Vault}/{Topic}/raw/`) |
| 기본 wiki 경로 | 사용자 지정 (예: `{Vault}/{Topic}/wiki/`) |

## 사용법

```
/wiki-compiler "{Topic}"                 # Vault 내 {Topic}/raw/ → {Topic}/wiki/ 컴파일
/wiki-compiler --path ~/my-research      # 임의 경로의 raw/ → wiki/ 컴파일
/wiki-compiler --incremental             # 변경분만 재컴파일
```

## 디렉토리 구조

```
{project}/
  raw/                    ← 소스 문서 (사람 또는 다른 스킬이 수집)
    article-1.md
    paper-2.md
    images/
  wiki/                   ← LLM이 컴파일한 위키 (수동 편집 금지)
    INDEX.md              ← 전체 목차 + 한줄 요약
    concepts/
      concept-a.md
      concept-b.md
    _meta/
      compile-state.json  ← 컴파일 이력
  output/                 ← Q&A 결과, 다이어그램 등 (선택)
```

## Instructions

### Step 1: 프로젝트 구조 확인

```bash
ls {project}/raw/
mkdir -p {project}/wiki/concepts {project}/wiki/_meta
```

raw/가 없으면 "raw/ 디렉토리에 소스 문서를 먼저 추가해주세요" 안내.

### Step 2: raw/ 스캔 및 변경 감지

```bash
find {project}/raw/ -name "*.md" -type f | sort
```

증분 컴파일(`--incremental`) 시:
- `wiki/_meta/compile-state.json` 읽기
- 마지막 컴파일 이후 수정된 파일만 대상
- compile-state.json이 없으면 전체 컴파일

### Step 3: 소스 문서 읽기 및 개념 추출

모든 대상 raw 파일을 읽고 핵심 개념을 추출한다.

**추출 기준:**
- 여러 소스에서 반복 언급되는 용어/개념
- 소스 내에서 정의되거나 상세 설명되는 개념
- 소스 간 관계를 형성하는 핵심 주제

**출력:** 개념 목록을 사용자에게 보여주고 확인 후 진행
```
📋 추출된 개념 (N개):
1. Concept A — 3개 소스에서 언급
2. Concept B — 2개 소스에서 언급
이 개념들로 위키를 컴파일할까요?
```

### Step 4: 개념별 아티클 생성

각 개념에 대해 `wiki/concepts/{concept-name}.md`를 생성한다.

**아티클 템플릿:**

```markdown
---
title: {개념명}
sources:
  - raw/{source1}.md
  - raw/{source2}.md
related:
  - "[[다른-개념]]"
last_compiled: {YYYY-MM-DDTHH:mm}
---

## 핵심

> raw 소스들을 종합한 이 개념의 핵심 설명 (2-3 문장)

## 상세

소스별로 이 개념에 대해 말하는 내용을 종합.
각 주장에 출처 표기: *(출처: raw/article-1.md)*

## 연결

- [[관련-개념A]]: 관계 설명
- [[관련-개념B]]: 관계 설명
```

**아티클 작성 원칙:**
- raw 소스에 없는 정보를 추가하지 않는다 (환각 방지)
- 여러 소스가 상충하면 양쪽을 모두 기록하고 차이를 명시한다
- 각 주장의 출처를 raw 파일명으로 표기한다

### Step 5: INDEX.md 생성

```markdown
# {프로젝트명} Wiki Index

> 마지막 컴파일: {YYYY-MM-DD HH:mm}
> raw 소스: {N}개 | 개념 아티클: {M}개 | 총 단어 수: ~{W}

## 개념 목록

| 개념 | 요약 | 소스 수 | 마지막 컴파일 |
|------|------|---------|-------------|
| [[concept-a]] | 한줄 요약 | 3 | 2026-04-04 |

## 소스 목록

| 파일 | 유형 | 상태 |
|------|------|------|
| raw/article-1.md | 번역 아티클 | ✅ 컴파일됨 |
| raw/video-3.md | 영상 노트 | 🆕 미컴파일 |
```

### Step 6: 컴파일 상태 저장

`wiki/_meta/compile-state.json`에 컴파일 이력을 기록한다.

```json
{
  "project": "{프로젝트명}",
  "last_compiled": "2026-04-04T10:00:00",
  "processed_files": {
    "raw/article-1.md": {
      "modified_at": "2026-04-04T09:00:00",
      "compiled_at": "2026-04-04T10:00:00",
      "concepts": ["concept-a", "concept-b"]
    }
  },
  "stats": {
    "total_sources": 5,
    "total_concepts": 8,
    "total_words": 45000
  }
}
```

### Step 7: Post-compile linking

obsidian-note의 [post-write-linking.md](../obsidian-note/references/post-write-linking.md) 절차를 wiki 아티클 전체에 대해 실행.
wiki의 각 개념과 vault의 기존 노트를 교차 연결한다.

### Step 8: 완료 리포트

```
📚 Wiki Compile 완료
├── 프로젝트: {프로젝트명}
├── raw 소스: N개 처리
├── 개념 아티클: M개 생성 (신규 X, 업데이트 Y)
├── INDEX.md 업데이트됨
├── 총 단어 수: ~W
└── Post-compile linking: Z건 연결
```

## 다른 스킬과의 연동

| 스킬 | 연동 |
|------|------|
| `translate-article` | 번역 결과를 raw/에 저장 → 다음 컴파일에 포함 |
| `youtube-summarizer` | 영상 요약을 raw/에 저장 → 다음 컴파일에 포함 |
| `obsidian-note` | 개별 노트를 raw/에 추가 가능 |
| `vault-linter` | 컴파일된 wiki를 lint 대상에 포함 |
| `cc-team-builder` | 대규모 raw(20+ 파일)는 병렬 에이전트로 처리 |

## Self-Check

```markdown
□ raw/ 소스에 없는 정보를 추가하지 않았는가
□ 모든 아티클에 출처(raw 파일명)를 명시했는가
□ INDEX.md가 모든 개념과 소스를 포함하는가
□ compile-state.json이 올바르게 업데이트되었는가
□ 상충하는 정보를 양쪽 모두 기록했는가
□ 개념 목록을 사용자에게 확인받았는가
```

## Gotchas

- raw/ 파일은 절대 수정하지 않는다 — 원본 보존이 핵심
- wiki/ 파일은 수동 편집 금지 — 다음 컴파일에서 덮어써질 수 있음
- 대규모 raw(20+ 파일)는 한 번에 컨텍스트에 넣기 어려울 수 있음 → cc-team-builder로 병렬 처리 고려
- 이미지는 raw/images/에 유지하고 wiki에서 상대경로로 참조
- vault 경로에 공백 포함 (iCloud path) — 항상 따옴표로 감싸기
- 증분 컴파일 시 기존 아티클의 sources에 새 raw 파일이 추가될 수 있음 — 아티클 전체를 재생성
