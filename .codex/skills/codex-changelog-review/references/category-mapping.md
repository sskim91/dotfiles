# Codex Changelog Category Mapping

Classify each Codex release bullet by what it touches and map it to the user's local config. One bullet can touch multiple categories.

Pure bug fixes are usually skipped because upgrading picks them up automatically. Keep them only when they imply an action, a risk, or a stale config path.

This file maps review topics to evidence sources, not a snapshot of the user's environment. Read the current template, live config, wrapper, and relevant registrations before describing defaults or enabled capabilities. Distinguish configured values from observed session behavior.

## Mapping table

| Touches | Cross-reference target | Notes |
|---|---|---|
| Config keys (`config.toml`, profiles, managed config, requirements) | `.dotfiles/.codex/config.toml.example`, `~/.codex/config.toml` | Prefer tracked template for persistent changes; live file can confirm current state. |
| Approval, sandbox, permissions, bypass flags | `.codex/config.toml.example`, `~/.codex/config.toml`, `zsh/functions.zsh:cdx` | Compare template defaults, live defaults, and explicit wrapper flags separately. Check new-session and resume paths, including bypass variants. Treat bypass expansion as security review. |
| Hooks, hook schemas, trusted hashes | `.dotfiles/.codex/config/global.json`, `~/.codex/hooks.json`, `.dotfiles/.codex/hooks/*.sh`, `.dotfiles/.codex/config/hook-settings.sh`, `~/.codex/config.toml:[hooks.state]` | Match registered events and commands to scripts and effective hook settings. New fields can improve existing checks. Trusted hashes are live-state, not template material. |
| MCP server behavior | `~/.codex/config.toml:[mcp_servers.*]`, `.dotfiles/.codex/config.toml.example`, `.dotfiles/.codex/setup-mcp.sh`, `.mcp.json` if present | Distinguish enabled servers from retained entries with `enabled = false`. Registration does not prove successful startup or tool availability. Startup, OAuth, timeout, and tool schema changes are relevant. |
| Plugins, app connectors, marketplaces | `~/.codex/config.toml:[plugins.*]`, `[apps.*]`, `codex plugin list --json`, `~/.codex/plugins` cache | Verify installed and enabled plugins separately from connector access. Cached files alone do not establish activation. Plugin list/discovery JSON can support audits. |
| Skills | `.codex/skills/*`, `~/.codex/skills/*`, plugin-provided skills | Skill discovery/frontmatter changes can affect reusable workflows. Keep as Tier 2 unless an existing skill clearly benefits. |
| TUI, status line, keybindings, notifications | `.codex/config.toml.example:[tui]`, `~/.codex/config.toml:[tui]` | Compare actual status items and UI preferences in both files before recommending additions. Status/title surface changes can be Tier 1. |
| Models, reasoning, context window, compaction | `.codex/config.toml.example`, `~/.codex/config.toml`, available session metadata | Check model, reasoning effort, review overrides, and whether context/compaction values are explicitly set or left to defaults. Verify version-specific defaults in official documentation; config alone does not prove the active session model. |
| Web/image/browser/computer tools | `web_search` in both configs, MCP browser entries, plugin registrations, current session tools | Check the configured search mode and available browser/computer tools separately. Hosted tool changes may affect workflow but often need no config edit. |
| Multi-agent, goals, automations | `[features]` in both configs, current session tools, workflow skills | Inspect current feature values and nested feature tables. Distinguish configured features from capabilities exposed in the session before recommending flags or command changes. |
| CLI commands/options (`codex update`, `codex exec`, `codex plugin list --json`) | `zsh/functions.zsh:update`, `zsh/functions.zsh:cdx`, docs/tips | New scriptable commands can become aliases or checks. |
| Cloud/app/server/remote-control | `Codex app` usage, `app-server`, remote plugins | Usually Tier 2 unless local config already enables the related path. |
| Release engineering, CI, internal refactors | Skip | Keep only if it changes install/update behavior. |

## User posture notes

### Config

The tracked config template is `.dotfiles/.codex/config.toml.example`; the live file is `~/.codex/config.toml`. Recommendations should point at the tracked template when a durable dotfiles change is appropriate.

### Security

Read `cdx()` in `zsh/functions.zsh` for the exact flags used by ordinary, read-only, resume, and bypass invocations. Compare them with both config files; the template is not evidence of live permissions. Any release note that broadens bypass behavior, relaxes permission prompts, changes trusted hashes, or changes sandbox semantics should be reviewed as risk, not convenience.

### Hooks

Use `.codex/config/global.json` and `~/.codex/hooks.json` to identify registered hooks, then inspect their scripts and `.codex/config/hook-settings.sh`. A script's presence does not mean it is registered or its optional checks are enabled. Keep host-added hooks distinct from tracked definitions. New hook input fields or event types are high-signal if they improve a registered check or avoid false positives.

### MCP and plugins

Build the relevant inventory from current MCP entries, plugin listing, and connector configuration. Changes to schema compaction, OAuth, startup timeout, parallel tool calls, plugin listing, plugin validation, and app connector behavior matter when they map to an enabled integration or an explicitly requested workflow.

### TUI/status

Check `[tui].status_line` in both the template and live config; their item lists may differ. Recommend a new status item only after confirming it is absent from the relevant target and useful for the user's workflow.

### Update workflow

Inspect `update()` in `zsh/functions.zsh` for the current Codex update command and its availability check. Release bullets about self-update support or install commands may be "already covered" when that path already handles them.
