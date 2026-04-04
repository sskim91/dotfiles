---
name: research-session
description: Use when user says "research", "리서치", "조사해줘", "wiki에서 찾아", "연구해줘", or wants to ask questions against their knowledge base and have answers automatically filed back. Do NOT use for individual note creation (use obsidian-note) or article translation (use translate-article).
---

# Research Session

질문을 받아 wiki/vault를 탐색하고, 답변을 .md 파일로 자동 저장하여 지식이 누적되는 스킬.
Karpathy의 "Q&A → filing back → compound interest" 패턴.

**핵심 원칙: 모든 탐색은 지식으로 남는다.** 답변이 터미널에서 사라지지 않고, 항상 .md 파일로 vault에 편입된다.

## 기본 설정

| 항목 | 값 |
|------|-----|
| Vault 경로 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` |
| 출력 위치 | 프로젝트 wiki가 있으면 `{project}/output/`, 없으면 `00.Inbox/` |
| 파일명 규칙 | `Research-{질문요약}.md` |

## 사용법

```
/research "RAG vs Long Context 트레이드오프"
/research "이 vault에서 LLM 관련 노트 요약해줘"
/research --topic "AI" "최근 트렌드 정리"
```

## Instructions

### Step 1: 질문 파악 및 탐색 범위 결정

사용자 질문을 분석하고 탐색 범위를 결정한다.

**범위 결정 기준:**

| 질문 유형 | 탐색 범위 | 예시 |
|-----------|----------|------|
| 특정 프로젝트 | `{project}/wiki/` + `{project}/raw/` | "이 리서치에서 X는?" |
| vault 전체 | vault 전체 .md 검색 | "LLM 관련 노트 요약" |
| 외부 포함 | vault + tavily_search | "최신 트렌드까지 포함해서" |

### Step 2: 관련 노트 수집

vault에서 질문과 관련된 노트를 찾는다.

```bash
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note"
```

**탐색 순서:**
1. 프로젝트 wiki/INDEX.md가 있으면 먼저 읽기 (전체 구조 파악)
2. INDEX에서 관련 개념 아티클 식별 → 해당 아티클 읽기
3. INDEX가 없으면 vault 전체에서 키워드/태그로 관련 노트 검색
4. 관련 노트를 찾으면 본문을 읽고 질문에 답변할 수 있는 정보 수집

**핵심: Claude의 Read/Grep 도구를 활용.** 벡터 DB나 RAG 불필요 — 1M 컨텍스트로 관련 노트를 직접 읽는다.

### Step 3: 답변 생성

수집한 정보를 종합하여 답변을 작성한다.

**답변 원칙:**
- vault에 있는 정보를 우선 사용, 출처 노트를 명시
- vault에 없는 정보는 `tavily_search`로 보완 (사용자가 요청한 경우)
- 불확실한 부분은 명시적으로 표시
- 단순 텍스트가 아닌, 구조화된 .md 형태로 작성

### Step 4: 답변을 .md 파일로 저장 (자동 filing)

**이것이 이 스킬의 핵심 차별점.** 답변을 반드시 파일로 저장한다.

**출력 파일 템플릿:**

```markdown
---
source:
  - "[[참조한 노트1]]"
  - "[[참조한 노트2]]"
related_notes:
  - "[[관련 노트]]"
tags:
  - research/output
  - {주제 태그}
created: {YYYY-MM-DD}
query: "{원래 질문}"
---

## 질문

> {사용자의 원래 질문}

## 답변

{구조화된 답변}

### 근거

| 출처 | 관련 내용 |
|------|-----------|
| [[노트A]] | 해당 노트에서 가져온 핵심 정보 |
| [[노트B]] | 해당 노트에서 가져온 핵심 정보 |

## 후속 질문

- {이 답변에서 파생되는 추가 질문 1}
- {추가 질문 2}
```

**저장 위치 결정:**
- 프로젝트 wiki가 있으면: `{Vault}/{Topic}/output/Research-{질문요약}.md`
- 없으면: `{Vault}/00.Inbox/Research-{질문요약}.md`

여기서 `{Topic}`은 사용자가 `--topic`으로 지정하거나, 질문 컨텍스트에서 vault 내 토픽 디렉토리를 자동 감지한 것.

### Step 5: INDEX 업데이트 (프로젝트 wiki가 있는 경우)

프로젝트 `wiki/INDEX.md`가 존재하면 출력 섹션에 새 리서치 결과를 추가한다.

### Step 6: Post-write linking

[post-write-linking.md](../obsidian-note/references/post-write-linking.md) 절차를 실행.
저장된 답변 파일과 vault의 기존 노트를 양방향 연결한다.

### Step 7: 완료 리포트

```
🔍 Research Session 완료
├── 질문: "{질문}"
├── 참조 노트: N개
├── 답변 저장: {저장 경로}
├── 링킹: M개 노트와 연결
└── 후속 질문: K개 제안됨

💡 후속 질문으로 계속 리서치하려면:
   /research "후속 질문 내용"
```

## 연속 리서치 (Chained Research)

한 리서치의 "후속 질문"으로 다음 리서치를 이어갈 수 있다.
이렇게 하면 **탐색 체인이 vault에 누적**된다:

```
Research-RAG-트레이드오프.md
  → 후속: "Embedding 모델 선택 기준은?"
    → Research-Embedding-모델-선택.md
      → 후속: "OpenAI vs Cohere 임베딩 비교?"
        → Research-OpenAI-vs-Cohere.md
```

각 리서치가 이전 리서치를 참조하므로 지식 그래프가 자연스럽게 성장한다.

## 다른 스킬과의 연동

| 스킬 | 연동 |
|------|------|
| `wiki-compiler` | 리서치 결과가 다음 컴파일 시 raw로 편입될 수 있음 |
| `vault-linter` | 리서치 결과의 후속 질문 → 새 노트 후보로 감지됨 |
| `obsidian-note` | 리서치 결과를 더 깊이 다듬고 싶으면 /obsidian-note로 정식 노트 작성 |


## Self-Check

```markdown
□ 답변이 .md 파일로 저장되었는가 (터미널에만 출력하고 끝나지 않았는가)
□ 참조한 노트를 source에 명시했는가
□ query 필드에 원래 질문이 기록되었는가
□ 후속 질문이 최소 1개 제안되었는가
□ Post-write linking이 실행되었는가
□ vault에 없는 정보를 추가한 경우 출처가 명시되었는가
```

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| vault에서 관련 노트 0건 | 키워드 불일치 또는 빈 vault | 키워드를 동의어/영어 포함으로 확장, 그래도 0건이면 "vault에 관련 노트가 없어 외부 검색으로 보완합니다" 안내 |
| tavily_search 실패/타임아웃 | API 일시적 오류 | 재시도 1회, 그래도 실패 시 vault 정보만으로 답변 작성하고 "외부 검색 실패" 명시 |
| 프로젝트 wiki INDEX.md 없음 | 새 프로젝트 또는 미컴파일 | vault 전체 검색으로 폴백. "wiki-compiler로 INDEX 생성을 권장합니다" 안내 |
| 답변 파일이 너무 길어짐 | 소스 노트가 많거나 질문이 광범위 | 질문을 세분화하여 연속 리서치로 분리 제안 |

## Gotchas

- 답변을 터미널에만 출력하고 파일 저장을 깜빡하는 것이 가장 흔한 실수 — **저장이 핵심**
- vault 규모가 크면 (100+ 노트) 모든 노트를 읽지 말고 INDEX → 관련 아티클만 선택적으로 읽기
- 외부 검색(tavily_search)은 사용자가 "최신 정보"나 "외부도 포함해서"라고 한 경우만
- 후속 질문은 구체적으로 — "더 알아보기" 수준이 아니라 실행 가능한 리서치 질문
- `{project}`는 vault 내 특정 토픽 디렉토리 (예: `{Vault}/AI-Research/`)를 의미. working directory가 아님
