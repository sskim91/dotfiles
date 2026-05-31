# GEMINI.md

This file provides guidance to Antigravity CLI and legacy Gemini CLI when working within this dotfiles repository. It complements the existing `CLAUDE.md` and defines the environment's architecture, tools, and AI-specific configurations.

## Repository Overview

Personal dotfiles repository for managing a macOS development environment. Centralized at `~/.dotfiles` with automated installation and symlink management. It features a highly integrated AI ecosystem with custom hooks, skills, and MCP servers.

## Quick Commands

- `./install.sh`: Full installation (Homebrew, mise runtimes, symlinks, AI configs).
- `source ~/.zshrc` (alias: `rr`): Reload shell configuration.
- `agy`: Wrapper for Antigravity CLI. Use `-y` (skip permissions), `-s` (sandbox), `-r` (continue latest), or `-ry` (both).
- `gem`: Compatibility wrapper. Uses Antigravity CLI when `agy` is installed, otherwise falls back to Gemini CLI.

## Architecture & Symlinks

All configurations are symlinked from `~/.dotfiles/` to their respective home locations. **Always edit files in `~/.dotfiles/`, not the symlinked locations in `$HOME`.**

| Feature | Dotfiles Source | Home Destination |
|---------|-----------------|------------------|
| ZSH | `.zprofile`, `.zshrc`, `zsh/` | `~/.zprofile`, `~/.zshrc` |
| Git | `git/.gitconfig` | `~/.gitconfig` |
| Neovim | `.config/nvim/` | `~/.config/nvim/` |
| Legacy Gemini CLI | `.gemini/` | `~/.gemini/` |
| Antigravity CLI settings | `.gemini/antigravity-cli/settings.json` | `~/.gemini/antigravity-cli/settings.json` |
| Antigravity config | `.gemini/antigravity-cli/{hooks,mcp_config}.json` | `~/.gemini/config/` |
| Claude | `.claude/` | `~/.claude/` |
| Apps | `.config/` | `~/.config/` |

## Gemini and Antigravity CLI Integration

### Hook System
Legacy Gemini CLI configuration is located in `.gemini/settings.json`.
Antigravity CLI settings are stored in `.gemini/antigravity-cli/settings.json`. Hooks and MCP are linked into `~/.gemini/config/`, which is the path Antigravity uses after onboarding.

1. **SessionStart**: Executes `session-context.sh` to inject the current date/time.
2. **BeforeTool (File Ops)**: Security hooks block accidental writes of sensitive data:
   - `check-secrets.sh`: Blocks hardcoded secrets.
   - `check-sensitive-files.sh`: Blocks `.pem`, `.key`, etc.
   - `check-env-files.sh`: Blocks `.env` and sensitive config files.

### MCP Servers
The environment provides the following MCP servers for enhanced capabilities:
- `context7`: Up-to-date documentation and code examples.
- `playwright`: Web browser automation and testing.
- `desktop-commander`: Advanced local file and system operations.
- `tavily`: High-quality web search.

### Migration Notes
Antigravity CLI uses `agy` as its executable. Keep Gemini CLI available as a fallback during migration, but prefer `agy` for new terminal sessions. After installing Antigravity CLI, run:

```bash
agy plugin import gemini
```

## Development Conventions

### Modular ZSH
Configuration is split into logical files in `zsh/`:
- `aliases.zsh`: Command shortcuts (e.g., `vim` -> `nvim`, `ls` -> `eza`).
- `functions.zsh`: Custom shell functions (e.g., `ccv`, `gem`, `mkd`).
- `path.zsh`: PATH exports, env vars, Claude hook toggles (`ENABLE_XXX`). Sourced by `.zprofile`.

### Runtime Management
Uses **mise** for managing language runtimes (Node.js, Python).
- Configured in `install.sh`.
- Activated in `.zprofile` via `mise activate zsh`.

### AI Skills & Logic
The `.claude/skills/` directory contains 17+ specialized "skills" (e.g., `git-commit`, `til`, `obsidian-note`).
- **Guidance for Antigravity/Gemini**: Before implementing new automation or workflows, check `.claude/skills/` for existing logic that can be adapted or reused.

## Security & Privacy
- **Do not commit** `.env.local` or any file containing secrets.
- Use the provided Git identity switching (`git/.gitconfig_personal` vs `git/.gitconfig_company`) based on the directory context.

## Instruction for Antigravity CLI and Legacy Gemini CLI
1. **Tool Usage**: Prefer `npx` for temporary tools and `brew` for persistent system tools.
2. **File Edits**: Use surgical replacements for config files to avoid breaking existing logic.
3. **Shell**: You are operating in a `zsh` environment on `darwin` (macOS). Use modern alternatives (`eza`, `fd`, `bat`) when possible.
4. **Context**: Use the `session-context` provided at session start to remain aware of the current time/date.
