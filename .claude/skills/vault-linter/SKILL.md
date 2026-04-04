---
name: vault-linter
description: Use when user says "vault lint", "노트 점검", "vault 정리", "orphan notes", "링크 점검", or wants to check Obsidian vault health. Do NOT use for individual note creation (use obsidian-note) or tag management (use til-tagger).
---

# Vault Linter

Obsidian Vault의 건강 상태를 점검하고 지식 그래프의 일관성을 유지하는 스킬.
Karpathy의 "LLM Knowledge Base Linting" 패턴.

## 기본 설정

| 항목 | 값 |
|------|-----|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 리포트 저장 위치 | `00.Inbox/Vault-Lint-Report-{YYYY-MM-DD}.md` |
| 검사 제외 | `99.Template/`, `10.Flashcards/FC-*.md`, `.obsidian/` |

## 사용법

```
/vault-linter                    # 전체 점검
/vault-linter --orphans          # 고아 노트만
/vault-linter --links            # 깨진 링크만
/vault-linter --stale            # 오래된 노트만
/vault-linter --suggestions      # 새 노트 후보만
```

## Scripts

| 스크립트 | 용도 |
|----------|------|
| `scripts/vault-scan.sh list-notes` | 제외 대상 빼고 전체 노트 목록 출력 |
| `scripts/vault-scan.sh extract-links <file>` | 파일에서 `[[wikilink]]` 추출 (alias 처리 포함) |
| `scripts/vault-scan.sh check-links <file>` | 깨진 링크만 출력 |
| `scripts/vault-scan.sh find-orphans` | 어디서도 참조되지 않은 노트 목록 |
| `scripts/vault-scan.sh tag-list` | 태그별 사용 횟수 |

스크립트가 결정적 검증을 수행하고, Claude는 결과를 해석하고 제안한다.

## Instructions

### Step 1: Vault 스캔

```bash
bash scripts/vault-scan.sh list-notes
```

결과로 전체 노트 목록을 확보. 이후 단계에서 스크립트를 활용한다.

### Step 2: 고아 노트 점검 (Orphan Notes)

```bash
bash scripts/vault-scan.sh find-orphans
```

결과로 나온 고아 노트에 대해 tags와 키워드 기반으로 연결 후보를 제안한다.

### Step 3: 깨진 위키링크 점검 (Broken Links)

각 노트에 대해:
```bash
bash scripts/vault-scan.sh check-links "$NOTE"
```

깨진 링크가 발견되면 "새 노트를 만들까요?" 또는 "링크를 제거할까요?" 제안.

### Step 4: 오래된 노트 점검 (Stale Notes)

frontmatter `created` 날짜가 90일 이상 된 노트 중, 버전/날짜 의존적 내용이 있는 것을 찾는다.

- created 날짜 추출
- 본문에서 연도(`202X`), 버전(`v1.x`, `버전 N`), "최신", "현재" 등 시간 의존적 표현 검색
- 해당 노트 목록 출력 + tavily_search로 정보 유효성 확인 제안

### Step 5: 태그 비일관성 점검 (Tag Inconsistency)

모든 태그를 수집하여 유사하지만 다른 태그 쌍을 찾는다.

대소문자 차이(`ai/llm` vs `ai/LLM`), 유사 표현(`database/sql` vs `db/sql`) 등을 탐지하고 통일 제안.

### Step 6: 새 노트 후보 제안 (Article Candidates)

여러 노트의 `## 더 알아보기` 섹션에서 공통 언급 주제를 추출한다.

- 모든 "더 알아보기" 섹션 텍스트 수집
- 주제 빈도 분석
- 2개 이상 노트에서 언급된 주제를 새 노트 후보로 제안

### Step 7: 리포트 생성

결과를 `00.Inbox/Vault-Lint-Report-{YYYY-MM-DD}.md`에 저장한다.

```markdown
---
tags:
  - vault/maintenance
created: {YYYY-MM-DD}
---

## Vault Lint Report — {YYYY-MM-DD}

### 요약

| 항목 | 건수 | 심각도 |
|------|------|--------|
| 고아 노트 | N건 | ⚠️ |
| 깨진 링크 | N건 | 🚫 |
| 오래된 노트 | N건 | 💡 |
| 태그 비일관성 | N건 | 💡 |
| 새 노트 후보 | N건 | ✨ |

### 🚫 깨진 링크

| 노트 | 깨진 링크 | 제안 |
|------|-----------|------|
| [[노트A]] | [[존재하지않는것]] | 새 노트 생성 or 링크 제거 |

### ⚠️ 고아 노트

| 노트 | 연결 후보 |
|------|-----------|
| [[고아노트]] | [[관련노트]] (태그 매칭) |

### 💡 오래된 노트

| 노트 | 생성일 | 시간 의존적 내용 |
|------|--------|-----------------|
| [[구형노트]] | 2025-01-01 | "v2.x 기준" 언급 |

### 💡 태그 비일관성

| 태그 A | 태그 B | 건수 | 통일 제안 |
|--------|--------|------|-----------|
| ai/llm | ai/LLM | 5+2 | ai/llm |

### ✨ 새 노트 후보

| 주제 | 언급 노트 수 | 출처 노트 |
|------|-------------|-----------|
| RAG vs Long Context | 3 | [[A]], [[B]], [[C]] |
```

## Self-Check

```markdown
□ 제외 대상(Template, Flashcards, .obsidian)을 빼고 스캔했는가
□ 깨진 링크에서 Obsidian alias([[이름|별칭]])를 올바르게 처리했는가
□ 리포트를 00.Inbox에 저장했는가
□ 고아 노트에 구체적 연결 후보를 제안했는가
□ 새 노트 후보의 출처 노트를 명시했는가
□ 각 플래그(--orphans, --links 등) 단독 실행이 가능한 구조인가
```

## Gotchas

- Obsidian alias 문법 `[[파일명|표시명]]`에서 파일명만 추출해야 함 — vault-scan.sh가 처리
- 파일명에 특수문자가 포함될 수 있음 — vault-scan.sh가 grep 이스케이프 처리
- vault 경로에 공백이 포함됨 (iCloud path) — 항상 따옴표로 감싸기
- `--stale`의 tavily_search는 시간이 오래 걸릴 수 있음 — 노트 수가 많으면 상위 5개만 점검
- `--orphans`도 대형 vault(300+)에서 느릴 수 있음 — vault-scan.sh가 xargs로 일괄 처리하므로 개별 grep보다 빠름
