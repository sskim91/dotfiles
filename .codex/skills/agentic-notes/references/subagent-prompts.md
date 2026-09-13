# Agentic Notes Subagent Prompts

Use these as role templates. Keep each spawned task self-contained and read-only unless the role is `note-writer`.

## Common Prompt Shape

```text
TASK: <imperative assignment>
DELIVERABLE: Return markdown with the required role output schema.
SCOPE: Topic, vault path, allowed files, web-search expectations, and explicit out-of-scope items.
VERIFY: Name the checks you performed and the binary PASS/FAIL observable.
CONSTRAINTS: Do not write to the vault. Do not invent sources. Include URLs or wikilinks for every material claim.
```

## source-hunter

Purpose: collect external sources and current context.

Output:

```markdown
## 핵심 주장
- <claim>

## 근거
| 주장 | 출처 URL | 신뢰도 | 비고 |
|---|---|---|---|

## outdated 위험
- <what may have changed recently>

## 노트 후보 문장
- <sentence with source>
```

## vault-researcher

Purpose: inspect the Obsidian vault for existing notes, related concepts, and duplicate risk.

Output:

```markdown
## 연결 후보
| 노트 | 경로 | 연결 이유 | 실존 확인 |
|---|---|---|---|

## 중복/분할 위험
- <existing note that may overlap>

## 노트 범위 제안
- <atomic scope recommendation>
```

## skeptic

Purpose: challenge claims, look for contradictions, stale assumptions, and weak evidence.

Output:

```markdown
## 반박/주의점
| 주장 | 리스크 | 확인 방법 | 판정 |
|---|---|---|---|

## 약하게 써야 할 주장
- <claim and reason>

## 노트에 남길 이견
- <conflict to preserve>
```

## synthesizer

Purpose: merge role outputs into a writer-ready packet.

Output:

```markdown
## 원자적 제목
<title>

## Claim Ledger
| 주장 | 출처 수 | 신뢰도 | 채택 방식 |
|---|---:|---|---|

## 구조
- 핵심 아이디어:
- 본문 섹션:
- 더 알아보기:

## obsidian-note 입력
<writer-ready brief>
```

## note-writer

Purpose: create exactly one Obsidian note using `obsidian-note`.

Output:

```markdown
## 저장 경로
<vault-relative path>

## 완료 체크
- frontmatter source recorded:
- related_notes exist:
- hook is insight, not definition:
- trade-off included:
- post-write linking performed:
```
