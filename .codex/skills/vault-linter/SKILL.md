---
name: vault-linter
description: Obsidian vault의 끊어진 링크·고립 노트·frontmatter 상태를 점검하거나 정리할 때 사용한다.
---

# Vault Linter

Obsidian Vault의 건강 상태를 점검하고 지식 그래프의 일관성을 유지하는 스킬.
Karpathy의 "LLM Knowledge Base Linting" 패턴.

공통 규칙: `~/.dotfiles/vault/references/note-rules.md`. 규칙 위반(태그·frontmatter·MOC/허브 등록·링크·TIL 원본) 판정은 결정적 도구 `python3 ~/.dotfiles/vault/vk`가 맡고, 이 스킬은 그 결과를 해석하고 판단이 필요한 항목(고아 노트 연결, 오래된 내용, 새 노트 후보, 의미 기반 연결)을 제안한다.

## 기본 설정

| 항목 | 값 |
|------|-----|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 기본 산출물 | `_Inbox/Vault-Index.md` |
| 진단 리포트 저장 위치 | `_Inbox/Vault-Lint-Report-{YYYY-MM-DD}.md` (명시적으로 리포트를 요청한 경우만) |
| 검사 제외 | `Templates/`, `.obsidian/`, `Vault-Lint-Report*`, `Vault-Semantic-Report*`, `Vault-Index.md`, `Vault-Log.md` |

## 사용법

```
/vault-linter                    # 전체 점검
/vault-linter --check            # 정책 위반 점검만 (vk check, 읽기 전용)
/vault-linter --apply            # 기계적 수정 (vk apply --dry-run 먼저, 승인 후 vk apply)
/vault-linter --orphans          # 고아 노트만
/vault-linter --links            # 깨진 링크만
/vault-linter --stale            # 오래된 노트만
/vault-linter --suggestions      # 새 노트 후보만
/vault-linter --semantic         # 의미 기반 유사 노트 연결
/vault-linter --index            # Vault 인덱스만 갱신
/vault-linter --report           # 명시적으로 Vault-Lint-Report 생성
```

## Scripts

| 스크립트 | 용도 |
|----------|------|
| `scripts/vault-scan.sh list-notes` | 제외 대상 빼고 전체 노트 목록 출력 |
| `scripts/vault-scan.sh extract-links <file>` | 파일에서 `[[wikilink]]` 추출 (alias 처리 포함) |
| `scripts/vault-scan.sh check-links <file>` | 깨진 링크만 출력 |
| `scripts/vault-scan.sh check-links-all` | 전체 vault의 깨진 링크를 한 번의 노트 인덱스로 TSV 출력 |
| `scripts/vault-scan.sh find-orphans` | 어디서도 참조되지 않은 노트 목록 |
| `scripts/vault-scan.sh tag-list` | 태그별 사용 횟수 |
| `scripts/semantic-linker.py` | bge-m3 임베딩 + 코사인 유사도 후보 추출 |
| `scripts/semantic-linker.py --cache-only` | 임베딩 캐시만 빌드 (유사도 계산 생략) |
| `scripts/vault-index.py` | 폴더별 노트 카탈로그 생성 |
| `python3 ~/.dotfiles/vault/vk check` | 정책 위반 점검(읽기 전용, 위반 시 exit 1) |
| `python3 ~/.dotfiles/vault/vk apply --dry-run` | 기계적 수정 대상 파일만 출력 |
| `python3 ~/.dotfiles/vault/vk apply` | 기계적 수정 적용(백업 후) |

스크립트가 결정적 검증을 수행하고, Claude는 결과를 해석하고 제안한다.

## Instructions

### Step 0: 정책 점검 (`--check`, 전체 점검에 포함)

```bash
python3 ~/.dotfiles/vault/vk check
```

출력은 `[kind] 경로: 내용` 줄과 마지막 `합계:` 줄이다. kind별로 묶어 보고한다. 태그(`tag`), frontmatter, MOC·허브 누락·중복(`moc-*`, `hub-missing`), 개수 표기(`count`), 빈 태그(`tag-empty`), 깨진 링크(`link`), TIL 원본(`til-*`, `name-conflict`, `wiki-only-til-tag`), 스킬 사본 차이(`skill-drift`)가 여기서 판정된다. 아래 단계에서 같은 항목을 다시 세지 않는다.

### Step 0.5: 기계적 수정 (`--apply`, 명시 요청 시에만)

```bash
python3 ~/.dotfiles/vault/vk apply --dry-run   # 항상 먼저. 바뀔 파일 목록을 사용자에게 보여 준다
python3 ~/.dotfiles/vault/vk apply             # 사용자 승인 후에만
```

- `apply`는 태그 rename·drop, frontmatter 순서, 대응표로 정해지는 등록, MOC 개수 표기만 고친다. 실행 전 대상 파일을 `~/.local/state/vaultkit/backups/<timestamp>/`에 복사한다(`--backup-dir` 또는 `VAULTKIT_BACKUP_DIR`로 바꿈). 출력의 `백업:` 경로를 사용자에게 알린다.
- `건너뜀(empty-after-normalize)` 노트는 정규화하면 태그가 모두 사라지는 노트다. 쓰지 않았으므로 태그·위치를 사용자와 정한다. `til_root`가 없으면 `apply`는 쓰기를 거부한다(exit 2).
- TIL 파생 노트의 태그는 Wiki에서 고치지 않는다. `vk apply --til-mapping --dry-run`으로 `tag-mapping.json` 변경을 확인한 뒤 TIL 쪽에서 반영한다(til-tagger).
- 적용 후 `vk check`를 다시 실행해 남은 항목(판단 필요)만 보고한다.

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

Step 0의 `[link]` 항목을 쓴다(코드블록, 표 안 `\|`, 같은 노트 `#heading`, Archive는 도구가 제외한다). `--links` 단독 실행이면 `vk check` 출력에서 `[link]`만 추린다.

깨진 링크가 발견되면 "새 노트를 만들까요?" 또는 "링크를 제거할까요?" 제안.

### Step 4: 오래된 노트 점검 (Stale Notes)

90일 이상 된 노트 중, 버전/날짜 의존적 내용이 있는 것을 찾는다.

- 날짜 판단 우선순위: frontmatter `created` → 없으면 파일 수정 시간(`stat -f %Sm` macOS / `stat -c %y` Linux)
- 본문에서 연도(`202X`), 버전(`v1.x`, `버전 N`), "최신", "현재" 등 시간 의존적 표현 검색
- 해당 노트 목록 출력 + tavily_search로 정보 유효성 확인 제안

### Step 5: 태그 비일관성 점검 (Tag Inconsistency)

허용 분야 밖·rename 대상 잔존·단일 세그먼트는 Step 0의 `[tag]` 항목이다. 여기서는 규칙 안에 있지만 의미가 겹치는 태그 쌍만 찾는다.

유사 표현(`database/sql` vs `database/rdb`) 등을 탐지하고 통일 제안. 통일안은 policy `tags.rename`에 추가하자고 제안하고, 노트를 직접 고치지 않는다.

### Step 6: 새 노트 후보 제안 (Article Candidates)

여러 노트의 `## 남은 질문` 섹션(옛 노트는 같은 역할의 섹션 제목이 다를 수 있다)에서 공통 언급 주제를 추출한다.

- 모든 "남은 질문" 섹션 텍스트 수집
- 주제 빈도 분석
- 2개 이상 노트에서 언급된 주제를 새 노트 후보로 제안

### Step 6.5: Wiki MOC 동기화 점검

Wiki 목차는 `Wiki/_MOC/`에 있다. 최상위 목차 `00-Wiki-MOC.md`가 분야별 MOC(`MOC-*.md`)를 가리키고, 각 MOC는 하위 분류 `##` 아래에 `- [[노트]] — 한 줄 설명` 형식으로 노트를 나열한다. 모든 Wiki 노트는 정확히 하나의 MOC에 속한다.

누락·중복·개수 표기 불일치는 Step 0의 `vk check`가 판정한다. 태그로 섹션이 정해지는 누락은 `vk apply`(또는 노트별 `vk register`)가 등록한다. 이 단계에서는 도구가 섹션을 정하지 못한 노트(`unclassified`)만 다룬다.

- 파일 내용 첫 100줄을 읽고 적절한 MOC와 하위 분류(해당 MOC의 기존 `##` 섹션)를 추천
- 기존 섹션에 맞지 않으면 새 섹션 이름도 제안하고, policy `moc` 대응 추가를 함께 제안
- 리포트에 "어느 섹션에 넣을지"까지 포함

### Step 7: 리포트 생성 (`--report` 명시 시에만)

기본 실행과 `--index` 실행은 Obsidian vault에 `Vault-Lint-Report-*`를 남기지 않는다.
사용자가 명시적으로 진단 리포트를 요청했을 때만 결과를 `_Inbox/Vault-Lint-Report-{YYYY-MM-DD}.md`에 저장한다.

```markdown
---
title: "Vault-Lint-Report-{YYYY-MM-DD}"
source: []
topics: []
related_notes: []
tags:
  - productivity/vault-maintenance
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
| 정책 위반 (vk check) | N건 | 📋 |
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

### Step 8: 의미 기반 연결 (Semantic Linking) — `--semantic`

#### 8-1: 사전 조건 확인

```bash
ollama list | grep bge-m3
```

bge-m3가 없으면:
```bash
ollama pull bge-m3
```

#### 8-2: 후보 추출

```bash
python3 scripts/semantic-linker.py
```

JSON 출력의 `candidate_pairs`를 파싱한다.

#### 8-3: LLM 검증 (이어가기 지원)

리뷰 큐 파일이 있으면 이어서 진행:
```bash
ls scripts/semantic-review-queue.json 2>/dev/null && echo "리뷰 큐 있음 — 이어가기 모드"
```

리뷰 큐가 있으면 `next_batch_start`부터 `batch_size`(50)만큼 읽어서 처리하고, `llm_reviewed: true`로 업데이트. 없으면 새로 시작.

각 후보 쌍에 대해:
1. 두 노트의 내용을 Read로 읽는다
2. 연결 가치를 판단한다:
   - **연결**: 의미적으로 유의미한 관계 (보충, 선행지식, 대안 관점, 사례)
   - **거절**: 우연한 키워드 겹침, 의미 없는 유사도
3. 연결이면 양쪽 노트의 `related_notes`에 `[[상대노트]]` 추가
4. 10-20쌍 단위로 배치 처리하여 컨텍스트 관리

#### 8-4: 리포트 생성

`_Inbox/Vault-Semantic-Report-{YYYY-MM-DD}.md`에 저장:

```markdown
---
title: "Vault-Semantic-Report-{YYYY-MM-DD}"
source: []
topics: []
related_notes: []
tags:
  - productivity/vault-maintenance
created: {YYYY-MM-DD}
---

## Vault Semantic Link Report — {YYYY-MM-DD}

### 요약

| 항목 | 건수 |
|------|------|
| 분석 노트 | N개 |
| 후보 쌍 | N개 |
| 연결 완료 | N개 |
| 거절 | N개 |

### 새 연결

| Note A | Note B | 유사도 | 관계 유형 |
|--------|--------|--------|----------|
| [[A]] | [[B]] | 0.82 | 보충 |

### 거절된 쌍

| Note A | Note B | 유사도 | 거절 사유 |
|--------|--------|--------|----------|
| [[C]] | [[D]] | 0.76 | 키워드 우연 겹침 |
```

### Step 9: Vault 인덱스 — `--index`

카파시의 "LLM Wiki" 패턴에서 **index.md**는 LLM이 vault 탐색 시 가장 먼저 읽는 메타 레이어다. 매번 전체 노트를 Glob 하지 않고, 카탈로그에서 관련 폴더를 좁히고 진입한다.

#### 9-1: 인덱스 생성 (결정적)

```bash
python3 scripts/vault-index.py
```

동작:
- `_Inbox/Vault-Index.md` 전체 덮어쓰기 (폴더별 노트 + 본문 첫 줄 요약)
- `_Inbox/Vault-Log.md`는 생성하지 않음
- `_Inbox/Vault-Lint-Report-{YYYY-MM-DD}.md`는 생성하지 않음

## Self-Check

```markdown
□ 제외 대상(Templates, .obsidian)을 빼고 스캔했는가
□ `vk check` 결과를 kind별로 보고했는가
□ `vk apply`는 `--dry-run` 결과를 보여 주고 승인받은 뒤에만 실행했는가
□ 깨진 링크에서 Obsidian alias([[이름|별칭]])를 올바르게 처리했는가
□ `--index` 실행은 `Vault-Index.md`만 생성/갱신했는가
□ 리포트는 사용자가 명시적으로 요청한 경우에만 _Inbox에 저장했는가
□ 고아 노트에 구체적 연결 후보를 제안했는가
□ 새 노트 후보의 출처 노트를 명시했는가
□ 각 플래그(--orphans, --links 등) 단독 실행이 가능한 구조인가
□ --semantic 실행 전 ollama + bge-m3 설치를 확인했는가
□ 이미 연결된 노트 쌍을 중복 제안하지 않았는가
□ --index는 Vault-Index.md 덮어쓰기만 수행했는가
```

## Gotchas

- Obsidian alias 문법 `[[파일명|표시명]]`에서 파일명만 추출해야 함 — vault-scan.sh가 처리
- 파일명에 특수문자가 포함될 수 있음 — vault-scan.sh가 grep 이스케이프 처리
- vault 경로에 공백이 포함됨 (iCloud path) — 항상 따옴표로 감싸기
- `--stale`의 tavily_search는 시간이 오래 걸릴 수 있음 — 노트 수가 많으면 상위 5개만 점검
- `--orphans`도 대형 vault(300+)에서 느릴 수 있음 — vault-scan.sh가 xargs로 일괄 처리하므로 개별 grep보다 빠름
- `--semantic` 첫 실행 시 877개 임베딩 생성에 수 분 소요 — 이후 캐시로 신규/변경 노트만 처리
- ollama가 실행 중이어야 함 — `ollama serve`로 데몬 시작 필요할 수 있음
- embeddings-cache.json은 gitignore됨 — 머신 간 동기화 안 됨 (의도적)
- `--index`의 요약은 본문 첫 줄(heading/frontmatter/table row 제외)을 100자로 자름 — 프론트매터에 `description:` 필드가 있으면 나중에 그걸 우선 쓰도록 확장 가능
