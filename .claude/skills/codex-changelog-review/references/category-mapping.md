# Codex Changelog Category Mapping

Classify each Codex release bullet by what it touches and map it to the user's local config. One bullet can touch multiple categories.

Pure bug fixes are usually skipped because upgrading picks them up automatically. Keep them only when they imply an action, a risk, or a stale config path.

## Mapping table

| Touches | Cross-reference target | Notes |
|---|---|---|
| Config keys (`config.toml`, profiles, managed config, requirements) | `.dotfiles/.codex/config.toml.example`, `~/.codex/config.toml` | Prefer tracked template for persistent changes; live file can confirm current state. |
| Approval, sandbox, permissions, bypass flags | `.codex/config.toml.example`, `zsh/functions.zsh:cdx` | User has conservative live defaults but `cdx` uses `--full-auto`; `cdx -y` bypasses all guardrails. Treat bypass expansion as security review. |
| Hooks, hook schemas, trusted hashes | `~/.codex/hooks.json`, `.dotfiles/.codex/hooks/*.sh`, `~/.codex/config.toml:[hooks.state]` | New hook events/fields can improve lint dispatch, prompt rewriting, and secret checks. Trusted hashes are live-state, not template material. |
| MCP server behavior | `~/.codex/config.toml:[mcp_servers.*]`, `.dotfiles/.codex/setup-mcp.sh`, `.mcp.json` | User has context7, playwright, desktop-commander, tavily, brave-search, and youtrack. Startup, OAuth, timeout, and tool schema changes are relevant. |
| Plugins, app connectors, marketplaces | `~/.codex/config.toml:[plugins.*]`, `.codex/plugins` cache, installed openai-curated plugins | User has GitHub, Gmail, Google Drive enabled. Plugin list/discovery JSON can support audits. |
| Skills | `.claude/skills/*`, `~/.codex/skills/*`, plugin-provided skills | Skill discovery/frontmatter changes can affect reusable workflows. Keep as Tier 2 unless an existing skill clearly benefits. |
| TUI, status line, keybindings, notifications | `~/.codex/config.toml:[tui]` | User has a dense status line with `codex-version`, context, and rate-limit items. Status/title surface changes can be Tier 1. |
| Models, reasoning, context window, compaction | `.codex/config.toml.example`, `~/.codex/config.toml` | User pins `gpt-5.5`, `model_reasoning_effort = "high"`, and a manual compaction threshold. Model/default changes need careful verification. |
| Web/image/browser/computer tools | `web_search`, MCP browser tools, frontend workflow assumptions | User uses web search cached mode and Playwright MCP; hosted tool changes may affect workflow but often need no config edit. |
| Multi-agent, goals, automations | `[features]`, status line, workflow skills | User has `multi_agent`, `hooks`, and `goals` enabled. Runtime metadata/default changes are relevant if they change config or command usage. |
| CLI commands/options (`codex update`, `codex exec`, `codex plugin list --json`) | `zsh/functions.zsh:update`, `zsh/functions.zsh:cdx`, docs/tips | New scriptable commands can become aliases or checks. |
| Cloud/app/server/remote-control | `Codex app` usage, `app-server`, remote plugins | Usually Tier 2 unless local config already enables the related path. |
| Release engineering, CI, internal refactors | Skip | Keep only if it changes install/update behavior. |

## User posture notes

### Config

The tracked config template is `.dotfiles/.codex/config.toml.example`; the live file is `~/.codex/config.toml`. Recommendations should point at the tracked template when a durable dotfiles change is appropriate.

### Security

`cdx` defaults to `--full-auto`, and `cdx -y` uses `--dangerously-bypass-approvals-and-sandbox`. Any release note that broadens bypass behavior, relaxes permission prompts, changes trusted hashes, or changes sandbox semantics should be reviewed as risk, not convenience.

### Hooks

The tracked hook scripts include prompt rewriting, sensitive-file guards, env-file guards, language checks, hardcoded-secret checks, pre-commit gate, and file dispatcher. New hook input fields or event types are high-signal if they let these hooks make better decisions or avoid false positives.

### MCP and plugins

The user has several MCP servers and curated plugins enabled. Changes to schema compaction, OAuth, startup timeout, parallel tool calls, plugin listing, plugin validation, and app connector behavior are likely relevant.

### TUI/status

The status line already includes model, reasoning, cwd, git branch, context, rate limits, Codex version, and context window size. Release bullets about status/title items should be checked against `[tui].status_line` before recommending anything.

### Update workflow

`zsh/functions.zsh:update` already runs `codex update` when `codex` exists. Release bullets about self-update support or install commands may be "already covered" unless they change the recommended update path.
