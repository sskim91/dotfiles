---
name: codex-changelog-review
description: Review Codex CLI changelog updates against the user's Codex and dotfiles configuration, then recommend which new features are worth adopting. Use when the user mentions "codex 변경사항", "codex changelog", "codex 업데이트 검토", "codex release notes", "codex 버전", "최근 codex 릴리스", gives a Codex CLI version range like 0.136.0..0.137.0, or asks what is worth adopting from Codex updates. Do NOT use for Claude Code changelogs, OpenAI SDK/API model changelogs, or general release-note reading without a dotfiles cross-reference.
---

# Codex Changelog Review

Compares recent Codex CLI releases against the user's Codex/dotfiles setup and produces tiered, actionable recommendations.

**Output only -- never auto-apply changes.** The user must explicitly choose what to adopt. This skill is a review/filter, not a migration runner.

## Why this exists

Codex ships frequently, and many release bullets are pure fixes or internal cleanup. A few touch surfaces the user actively uses: `~/.codex/config.toml`, `.dotfiles/.codex/config.toml.example`, Codex hooks, plugins, MCP servers, features, status line, and the `cdx` shell wrapper. Those are worth surfacing; the rest should be compressed.

Use the official Codex changelog for product context:

- https://developers.openai.com/codex/changelog
- https://github.com/openai/codex/releases

The bundled fetch script uses GitHub release bodies because they are structured markdown and match the CLI release entries shown on the official changelog page.

## Inputs

The user's request might come as:

| Format | Example | Resolution |
|---|---|---|
| Range | `0.136.0..0.137.0`, `0.136.0 to 0.137.0` | Inclusive both ends |
| Last N | `last 5`, `최근 5개` | N most recent stable CLI releases |
| Single version | `0.137.0`, `rust-v0.137.0` | Just that release |
| Include prereleases | `--include-prerelease`, `alpha 포함` | Include alpha/pre-release entries |
| Nothing | - | Default to last 5 stable releases |

If the request is genuinely ambiguous, ask once. Otherwise use the default.

## Workflow

### Fetch

Use the bundled script:

```bash
~/.dotfiles/.claude/skills/codex-changelog-review/scripts/fetch-codex-changelog.sh
~/.dotfiles/.claude/skills/codex-changelog-review/scripts/fetch-codex-changelog.sh 10
~/.dotfiles/.claude/skills/codex-changelog-review/scripts/fetch-codex-changelog.sh 0.137.0
~/.dotfiles/.claude/skills/codex-changelog-review/scripts/fetch-codex-changelog.sh 0.136.0 0.137.0
~/.dotfiles/.claude/skills/codex-changelog-review/scripts/fetch-codex-changelog.sh --include-prerelease 5
```

### Read user config

Read these in parallel when available:

- `~/.dotfiles/.codex/config.toml.example` -- tracked Codex config template
- `~/.codex/config.toml` -- live Codex config, including auto-managed state
- `~/.codex/hooks.json` -- live hook definitions, if present
- `~/.dotfiles/.codex/hooks/` -- tracked hook scripts
- `~/.dotfiles/zsh/functions.zsh` -- `cdx` wrapper and `update()` behavior
- `~/.dotfiles/zsh/path.zsh` -- `ENABLE_*` env toggles inherited by hooks
- `~/.dotfiles/.claude/skills/` and `~/.codex/skills/` -- reusable workflows that might be affected by skill/plugin changes
- `~/.dotfiles/.mcp.json` and `.mcp.json` -- MCP config, if present

Use `nl -ba` or `rg -n` for line numbers before citing a target path.

### Categorize

Read `references/category-mapping.md` before categorizing. One release bullet can touch multiple categories.

Skip pure bug fixes unless they indicate a security or workflow risk for this user's current setup.

### Assign Tier

- **Tier 1 -- 즉시 효과**: Maps to an existing user config surface and can be adopted with a small edit.
- **Tier 2 -- 워크플로우 추가**: Optional capability requiring a new alias, hook, config block, skill, or explicit policy choice.
- **Tier 3 -- 마이너 정리**: Docs/tips/awareness cleanup.
- **Skip**: Pure bug fixes, internal refactors, release engineering, or platform-specific changes that do not affect this user.

If a recommendation would touch 5+ files, demote it from Tier 1 to Tier 2.

### Verify before recommending

Before recommending a setting, verify whether it already exists:

```bash
rg -n 'key_or_feature_name' ~/.dotfiles/.codex ~/.codex/config.toml ~/.dotfiles/zsh
```

If it is already set, drop the recommendation or mention it under "already covered".

### Render

Use Korean output. Technical identifiers stay in original form.

Include:

1. Version range covered, total bullets, bullets after skip/filter
2. Tier sections with: changelog item, version, target `file_path:line_number`, recommended action
3. One concrete top recommendation with reasoning
4. Links to the official Codex changelog and relevant GitHub release(s)

End with:

**"어느 항목을 적용할까요? 또는 '전체 검토만'으로 답하시면 종료합니다."**

## Gotchas

- Codex official changelog is a web page, not a single stable markdown file. Prefer the bundled GitHub release helper for CLI entries, then cite the official changelog URL for product context.
- Default to stable releases. Alpha releases are noisy unless the user asks for them.
- `~/.codex/config.toml` contains auto-managed runtime state. For persistent recommendations, prefer the tracked template at `~/.dotfiles/.codex/config.toml.example` when the setting belongs there.
- The user's `cdx -y` bypasses approvals and sandboxing. Changes that expand bypass behavior are security review items, not convenience wins.
- The user's default Codex config is conservative (`sandbox_mode = "read-only"`), while `cdx` opts into `--full-auto`. Evaluate both paths.
- Do not mirror release notes. Filter aggressively and explain why each surviving item maps to this user's setup.

## Files

- `references/category-mapping.md` -- Codex changelog category mapping to the user's dotfiles.
- `scripts/fetch-codex-changelog.sh` -- fetch and filter Codex CLI release notes.
