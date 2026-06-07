---
name: agentic-notes
description: Use when the user asks to create an Obsidian note with an agent team, deep research, strict verification, multiple angles, or phrases like "팀으로 조사해서 노트", "깊게 조사해서 옵시디언 노트", "/agentic-notes", "--team", "--verify strict", or "--deep". Do NOT use for a simple one-shot Obsidian note; use obsidian-note instead.
---

# Agentic Notes

Obsidian 노트를 만들기 전에 여러 서브에이전트가 수집·검증·합성을 맡고, 마지막에는 `obsidian-note`의 leaf writer 규칙으로 노트 1장을 저장하는 상위 orchestration skill.

## Trigger

다음 신호가 있을 때 사용한다.

- `/agentic-notes`
- `--team [N]`
- `--verify strict` 또는 `--deep`
- "팀으로 조사해서 노트로", "깊게 조사해서 옵시디언 노트로", "여러 각도로 검토해서 저장"

단순한 "노트로 저장해줘"는 `obsidian-note`로 처리한다.

## Workflow

1. **Scope 결정**: 노트 주제, 원자적 범위, 원하는 깊이, `--team` 크기, strict 여부를 정한다. 기본 팀 크기는 4다.
2. **팀 구성**: 아래 역할을 필요한 만큼 spawn한다.
   - `source-hunter`: 공식 문서, 웹 출처, 최신 자료 수집
   - `vault-researcher`: 기존 Obsidian vault에서 관련 노트와 연결 후보 조사
   - `skeptic`: 주장 검증, 반례, outdated 정보, 과장 표현 탐지
   - `synthesizer`: 팀 결과를 claim ledger와 노트 구조로 합성
   - `note-writer`: 최종 결과를 `obsidian-note` 규칙으로 저장
3. **서브에이전트 프롬프트 작성**: 모든 프롬프트는 `TASK`, `DELIVERABLE`, `SCOPE`, `VERIFY`를 포함한다. 자세한 템플릿은 `references/subagent-prompts.md`를 읽는다.
4. **전원 완료 대기**: 수집 결과가 모두 돌아오기 전에는 최종 집필을 시작하지 않는다. 실패한 역할은 누락으로 기록하고, 핵심 역할이면 더 작은 scope로 한 번 재시도한다.
5. **검증 수준 선택**:
   - 기본: lead가 claim별 출처와 이견을 교차확인한다.
   - strict: `references/strict-verification.md`를 읽고 claim ledger를 작성한다.
6. **노트 작성**: `note-writer` 또는 lead가 `obsidian-note`를 사용해 `_Inbox/{Title}.md` 한 장으로 저장한다.

## Tool Mapping

| Intent | Claude Code | Codex |
| --- | --- | --- |
| Spawn role worker | `Agent` with `subagent_type: general-purpose` | `spawn_agent` with `fork_turns: "none"` |
| Wait for results | wait for all Agent results | `wait_agent`, then integrate substantive final output |
| Follow up on silent worker | send targeted prompt | `send_message` or `followup_task` |
| Close worker | not usually explicit | `close_agent` after integrating result |

## Prompt Contract

Every subagent assignment starts with:

```text
TASK: <imperative assignment>
DELIVERABLE: <required artifact>
SCOPE: <allowed paths, sources, and boundaries>
VERIFY: <checks the subagent must run or report>
```

## Output Contract

The final synthesis must include:

- one atomic note title
- claim ledger with source count and confidence
- conflicting claims, if any
- existing vault links that were verified to exist
- final writer input for `obsidian-note`

Subagent output must follow `references/subagent-prompts.md`.

## Guardrails

- Only the lead or `note-writer` writes to the vault.
- Source and vault workers are read-only.
- Do not create multiple notes unless the user explicitly asks for a note set.
- Do not use strict mode by default; it is slower and token-heavy.
- If sources conflict, preserve the disagreement instead of silently choosing one.
- If a claim has one weak source, write it cautiously or move it to "더 알아보기".

## Verification

Before reporting completion:

- confirm the created note follows `obsidian-note` frontmatter and body structure
- confirm `related_notes` links exist in the vault
- confirm strict mode, when used, has a claim ledger
- confirm all temporary QA/session resources are cleaned up
