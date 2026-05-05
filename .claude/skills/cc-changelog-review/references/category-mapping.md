# Changelog Category Mapping

For each bullet in a Claude Code CHANGELOG section, classify what it touches and map to the corresponding user config target. **One bullet can touch multiple categories** — record all of them rather than forcing a 1:1 mapping.

Pure bug fixes are skipped — they're covered by the upgrade itself, not by config changes. Note them in the summary line ("버그픽스 K건 제외"), don't list them.

## Mapping table

| Touches | Cross-reference target | Notes |
|---|---|---|
| Hook input/output schema (PostToolUse, PreToolUse, hookSpecificOutput, duration_ms) | `.claude/settings.json:hooks` + `.claude/hooks/*.sh` | Highest-leverage area for users with custom hooks. New input fields (e.g., `duration_ms` in 2.1.119) often unlock new hook capabilities. |
| New `settings.json` keys | Top-level keys in `.claude/settings.json` | Verify with `jq '.<key>'` before recommending — many keys are auto-set by Claude Code on first use. |
| MCP server options (`alwaysLoad`, `headersHelper`, etc.) | `.mcp.json`, `mcpServers` block in settings | Especially valuable when `ENABLE_TOOL_SEARCH=1` is set (deferred loading). |
| Env vars (`CLAUDE_*`, `ANTHROPIC_*`, `DISABLE_*`) | `.claude/settings.json:env` + `zsh/path.zsh` | Some env vars are session-only (settings.json), others affect spawned shells (path.zsh). Check both. |
| Permissions / allowlist / `--dangerously-skip-permissions` | `.claude/settings.json:permissions` | Don't promote to Tier 1 unless `skipDangerousModePermissionPrompt: true` is set. **Protection-shrinking changes** (e.g., "X path no longer protected from skip-mode") are *security risks* for skip-mode users, not convenience wins — recommend explicit `permissions.deny` entries to restore guardrails. |
| Skills frontmatter / discovery / `${CLAUDE_*}` placeholders | `.claude/skills/*` | New skill features (e.g., `${CLAUDE_EFFORT}` in 2.1.120) can be retroactively added to existing skills. |
| Slash commands (`/usage`, `/branch`, `/skills`, etc.) | `spinnerTipsOverride.tips` | Deprecated/renamed commands need tip updates so user discoverability stays current. |
| Themes | `~/.claude/themes/` | Custom theme files added in 2.1.118+. User uses Tokyo Night for tmux — theme parity is awareness-tier. |
| Plugins / marketplaces | `enabledPlugins`, `extraKnownMarketplaces` | New plugins are user-discretion; marketplace API changes affect existing plugin install paths. |
| CLI subcommands (`claude project purge`, `claude ultrareview`) | `zsh/aliases.zsh`, dotfiles README | Aliases for non-interactive use; documentation for one-off commands. |
| Vim mode | `editorMode` setting | Visual mode (v/V) added in 2.1.118 — only matters if user has vim mode enabled. |
| Status line | `statusLine` block | User's `claude-hud` status line consumes stdin JSON; new fields (e.g., `effort.level` in 2.1.119) may be displayable. |
| Auto mode / plan mode | `permissions.defaultMode`, `autoMode` | User has `defaultMode: "plan"` — items affecting plan mode are higher relevance. |
| Pure bug fix | (skip) | Covered by upgrade itself. Note in summary line, don't list. |

## Per-category notes

### Hooks

The user runs three hooks on every Write/Edit/MultiEdit (file-dispatcher, til-review, vault-linker). Any changelog entry that:

- **Adds new fields to PostToolUse input** → potential observability win. Check whether the user's hooks could use the new field.
- **Allows new return types from hooks** → potential output-injection win. Example: 2.1.121 expanded `hookSpecificOutput.updatedToolOutput` from MCP-only to all tools, which the user already adopted in `file-dispatcher.sh`.
- **Adds new event types** → check if any of the existing three hooks could benefit, or whether a new hook is warranted.

### MCP

Look for `ENABLE_TOOL_SEARCH=1` in settings.json env. If set (the user has it set), MCP changes that affect tool availability timing — `alwaysLoad`, `nonblocking` mode, server-startup retries — are higher leverage because every tool call currently goes through deferred lookup. `alwaysLoad: true` on serena/github/context7 would skip that.

### Env vars

Two locations:
- `~/.dotfiles/.claude/settings.json:env` — Claude Code session vars only.
- `~/.dotfiles/zsh/path.zsh` — vars exported to all spawned shells (and inherited by Claude Code from the login shell).

If a new env var has a paired `ENABLE_X=0|1` toggle pattern matching the user's hooks (e.g., `ENABLE_RUFF`, `ENABLE_TY`), recommend adding to `path.zsh` with a default that matches their conservative posture (most ENABLE_* vars are 0 by default).

### Skills

The user has many skills in `.claude/skills/`. New skill capabilities (placeholders, frontmatter fields, hook integration) are typically Tier 2 — user can retrofit to existing skills opportunistically rather than urgently.

### Slash commands

When a command is renamed or merged (e.g., `/cost` + `/stats` → `/usage` in 2.1.118), update `spinnerTipsOverride.tips` so the discoverability hints reflect current names. Otherwise the user reads stale tips and the friction silently builds.

### CLI subcommands

The user has `ccv`, `cco`, `cdx`, `gem` aliases for AI CLIs in `zsh/functions.zsh`. New non-interactive subcommands (e.g., `claude ultrareview --json`, `claude project purge`) can become aliases or be documented in the dotfiles README under the "AI CLI Wrappers" section.

## When to update this file

When Claude Code introduces a new config surface area (e.g., a future "agent profiles" feature), add a new row. When a category becomes obsolete, mark it with `(deprecated as of X.Y.Z)` rather than deleting — past-version reviews still need it for historical interpretation.
