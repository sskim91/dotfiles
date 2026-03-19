---
name: skill-guide
description: Quick skill creation guide with structure validation and Anthropic official best practices. Use when user wants to create a new Skill from scratch, validate SKILL.md structure/frontmatter, review skill quality against checklist, or reference Anthropic's official skill design guide. Do NOT use for eval-based iterative improvement, benchmark testing, description trigger optimization, or blind A/B comparison (use skill-creator plugin instead).
---

# Skill Guide

## Frontmatter Spec

Every skill needs a `SKILL.md` file (exact casing) in a kebab-case directory.

```yaml
---
name: skill-name          # kebab-case, max 64 chars, must match directory name
description: What it does and when to use it.  # max 1024 chars, no XML tags (<>)
---
```

**Naming rules**: lowercase, numbers, hyphens only. No "claude" or "anthropic" prefix.

**Optional fields**:

```yaml
allowed-tools: "Read Grep Glob"          # Restrict tool access
license: MIT
compatibility: "Claude Code only"        # 1-500 chars
metadata:
  author: Name
  version: 1.0.0
  tags: [automation, workflow]
```

## Description Writing

Description은 요약이 아니라 **트리거 판단 기준**이다. Claude가 세션 시작 시 모든 스킬의 description을 스캔해서 로드 여부를 결정한다.

**Formula**: `[What it does] + [When to use it] + [Negative triggers]`

```yaml
# ✅ 구체적 트리거 + negative trigger
description: Analyze Excel spreadsheets, create pivot tables, and generate charts.
  Use when working with .xlsx files or analyzing tabular data.
  Do NOT use for CSV-only operations (use data-processor skill).

# ❌ 모호 — Claude가 언제 로드할지 판단 불가
description: Helps with data analysis
```

## Skill Location

| Location | Use for |
|----------|---------|
| `~/.claude/skills/` | Personal workflows, experiments |
| `.claude/skills/` | Team/project, committed to git |

## File Structure

스킬은 **폴더**다. SKILL.md 하나가 아니다.

```
skill-name/
├── SKILL.md              # Required — 핵심 지시사항 (5,000 words 이내)
├── references/            # Claude가 필요할 때 읽는 상세 문서
├── scripts/               # 결정적(deterministic) 검증/처리용 스크립트
└── assets/                # Templates, data files
```

파일 시스템 자체가 progressive disclosure다. SKILL.md에서 어떤 파일이 있는지 알려주면, Claude가 적절한 시점에 읽는다. SKILL.md에 모든 내용을 넣지 말 것.

## Content Writing Principles

### Don't State the Obvious

Claude는 코딩, 마크다운 구조화, 에지 케이스 처리를 이미 안다. **Claude의 일반적 사고방식을 벗어나게 하는 정보**에 집중하라 — 조직의 컨벤션, 도메인 특화 gotchas, 비직관적 패턴.

### Build a Gotchas Section

스킬에서 가장 가치 있는 콘텐츠는 **Gotchas 섹션**이다. Claude가 실제로 틀리는 지점을 기록하고, 시간이 지나며 축적하라.

```markdown
## Gotchas
- API returns paginated results but doesn't indicate total count — always loop until empty
- The `--dry-run` flag silently ignores invalid configs instead of erroring
- Date fields use ISO 8601 but timezone is always UTC regardless of user locale
```

### Avoid Railroading

정보는 주되, Claude가 상황에 맞게 적응할 유연성을 남겨라. 모든 상황에 적용되는 rigid step sequence를 강제하지 말 것.

```markdown
# ❌ 과도한 제약
## Step 1: Always create the config file first
## Step 2: Then validate the schema
## Step 3: Then run the migration

# ✅ 유연한 가이드
## Setup
Ensure config exists (see references/config-schema.md for required fields).
Validate before running migrations — migration order matters,
check references/migration-deps.md for dependency graph.
```

### Use Scripts for Determinism

스크립트는 결정적이고, 자연어 지시는 아니다. 중요한 검증이나 출력 포맷은 `scripts/`에 코드로 번들하라.

## Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| 스킬이 트리거 안됨 | description이 모호 | 트리거 문구, 파일 타입, "Use when..." 추가 |
| 무관한 쿼리에서 트리거 | description이 넓음 | "Do NOT use for..." negative trigger 추가 |
| 여러 스킬 충돌 | description 겹침 | 각 스킬의 범위를 구체적으로 좁힘 |
| YAML 파싱 에러 | 포맷 오류 | `---` 구분자, 탭 대신 스페이스, 따옴표 닫기 확인 |
| 원인 불명 | — | `claude --debug`로 스킬 로딩 과정 확인 |

## References

- [Anthropic 공식 스킬 가이드](references/anthropic-skill-guide.md) — 설계 원칙, 워크플로우 패턴, 테스트 전략, 전체 frontmatter 참조
- [실전 스킬 작성 팁](references/practical-tips.md) — 9가지 스킬 유형, 고급 패턴 (데이터 저장, On Demand Hooks, 스킬 조합, 배포 전략)
