# Agentic Notes Strict Verification

Use this reference only for `--verify strict` or `--deep`.

## Purpose

Strict mode trades speed and token cost for lower hallucination risk. It does not replace judgment; it makes each material claim auditable before `obsidian-note` writes the final note.

## Strict Flow

1. Build a claim ledger from source-hunter, vault-researcher, and synthesizer outputs.
2. Send the ledger to one or more `skeptic` workers.
3. For each claim, record:
   - source count
   - source quality
   - freshness risk
   - contradicting evidence
   - final wording strength
4. Adopt only claims with enough evidence for their strength.
5. Move weak or unresolved claims to "더 알아보기".

## Triggers

- `--verify strict`
- `--deep`
- user says "가짜 정보 절대 안 됨", "엄격하게 검증", "출처까지 검증"

## Claim Ledger Template

```markdown
## Claim Ledger

| ID | Claim | Sources | Confidence | Freshness risk | Skeptic verdict | Final wording |
|---|---|---|---|---|---|---|
| C1 | ... | 2 official docs | high | low | pass | assert |
| C2 | ... | 1 blog | low | medium | weak | mention cautiously |
```

## Acceptance Rules

- 2+ independent credible sources: can be stated directly.
- 1 credible source: state cautiously and cite.
- conflicting sources: preserve "이견 있음" and explain the split.
- no source: exclude from body or move to "더 알아보기".
- time-sensitive claim: include current date checked or avoid strong wording.

## Writer Handoff

The final handoff to `obsidian-note` must include:

- title
- source URLs
- verified related notes
- claim ledger summary
- exact weak/conflicting claims to preserve
