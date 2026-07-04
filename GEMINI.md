# GEMINI.md

This file provides guidance to Antigravity CLI (`agy`) when working within this dotfiles repository. It complements the existing `CLAUDE.md` and defines the environment's architecture, tools, and AI-specific configurations.

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
| Git | `git/.gitconfig` | `~/.gitconfig` (local stub that `[include]`s the tracked base — not a symlink) |
| Neovim | `.config/nvim/` | `~/.config/nvim/` |
| Antigravity global context | `.claude/docs/working-style.md` | `~/.gemini/GEMINI.md` |
| Antigravity CLI settings | `.gemini/antigravity-cli/settings.json` | `~/.gemini/antigravity-cli/settings.json` |
| Antigravity config | `.gemini/antigravity-cli/{hooks,mcp_config}.json` | `~/.gemini/config/` |
| Claude | `.claude/` | `~/.claude/` |
| Apps | `.config/` | `~/.config/` |

## Gemini and Antigravity CLI Integration

### Hook System
Antigravity CLI settings are stored in `.gemini/antigravity-cli/settings.json`. Hooks and MCP are linked into `~/.gemini/config/`, which is the path Antigravity uses after onboarding. Hooks are declared in `.gemini/antigravity-cli/hooks.json`:

1. **PreToolUse (File Ops)**: Security hooks in `.gemini/antigravity-cli/hooks/` block accidental writes of sensitive data on `write_to_file`/`replace_file_content`:
   - `check-secrets.sh`: Blocks hardcoded secrets.
   - `check-sensitive-files.sh`: Blocks `.pem`, `.key`, etc.
   - `check-env-files.sh`: Blocks `.env` and sensitive config files.

### MCP Servers
The environment provides the following MCP servers for enhanced capabilities:
- `context7`: Up-to-date documentation and code examples.
- `playwright`: Web browser automation and testing.
- `tavily`: High-quality web search.

### Migration Notes
Antigravity CLI uses `agy` as its executable. Gemini CLI stopped serving free/Pro/Ultra tiers on 2026-06-18 and has been removed from this repo; `agy` is now the sole terminal agent for this stack. The one-time plugin import from the old Gemini CLI was:

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
The `.claude/skills/` directory contains specialized "skills" (e.g., `git-commit`, `til`, `obsidian-note`).
- **Guidance for Antigravity/Gemini**: Before implementing new automation or workflows, check `.claude/skills/` for existing logic that can be adapted or reused.

## Validation & Commits
- Before commit: `pre-commit run --all-files` (format, JSON/YAML checks, secret scan).
- Shell changes: validate with `zsh -n .zshrc zsh/*.zsh`.
- Commit convention: Conventional Commits `type(scope): subject`, imperative mood, no Gitmoji/emoji prefixes.

## Security & Privacy
- **Do not commit** `.env.local` or any file containing secrets.
- Use the provided Git identity switching (`git/.gitconfig_personal` vs `git/.gitconfig_company`) based on the directory context.

## Instruction for Antigravity CLI and Legacy Gemini CLI
1. **Tool Usage**: Prefer `npx` for temporary tools and `brew` for persistent system tools.
2. **File Edits**: Use surgical replacements for config files to avoid breaking existing logic.
3. **Shell**: You are operating in a `zsh` environment on `darwin` (macOS). Use modern alternatives (`eza`, `fd`, `bat`) when possible.
4. **Context**: Use the `session-context` provided at session start to remain aware of the current time/date.
