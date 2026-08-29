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
| ZSH | `.zshenv`, `.zprofile`, `.zshrc`, `zsh/` | `~/.zshenv`, `~/.zprofile`, `~/.zshrc` |
| Git | `git/.gitconfig` | `~/.gitconfig` (local stub that `[include]`s the tracked base — not a symlink) |
| Neovim | `.config/nvim/` | `~/.config/nvim/` |
| Antigravity global context | `.claude/docs/working-style.md` | `~/.gemini/GEMINI.md` |
| Antigravity CLI settings | `.gemini/antigravity-cli/settings.json` | `~/.gemini/antigravity-cli/settings.json` |
| Antigravity MCP | `.gemini/antigravity-cli/mcp_config.json` | `~/.gemini/config/mcp_config.json` (symlink) |
| Antigravity hooks | `.gemini/antigravity-cli/hooks.json` | `~/.gemini/config/hooks.json` — **merged, not symlinked.** cmux *replaces* this file with one holding only its own `cmux` block, so `install.sh` uses `merge_hooks_json` to keep both top-level blocks. Re-linking it would delete cmux's hooks. |
| Claude | `.claude/` | `~/.claude/` |
| Codex hooks | `.codex/config/global.json` | `~/.codex/hooks.json` — cmux overwrites the symlink with a real file but *merges*, keeping our 8 hooks alongside its own (unlike Antigravity; measured 2026-08-27). Both sides share one `.hooks` object, so a top-level merge is unsafe and this stays a plain symlink. |
| Apps | `.config/` | `~/.config/` |

## Gemini and Antigravity CLI Integration

### Hook System
Antigravity CLI settings are stored in `.gemini/antigravity-cli/settings.json`. Hooks and MCP are linked into `~/.gemini/config/`, which is the path Antigravity uses after onboarding. Hooks are declared in `.gemini/antigravity-cli/hooks.json`:

1. **PreToolUse (File Ops)**: Security hooks in `.gemini/antigravity-cli/hooks/` block accidental writes of sensitive data on `write_to_file`/`replace_file_content`:
   - `check-secrets.sh`: Blocks hardcoded secrets.
   - `check-sensitive-files.sh`: Blocks `.pem`, `.key`, etc.
   - `check-env-files.sh`: Blocks newly added `.env` files, structured secret/config files (`credentials`/`secrets`/`config.local` as `.json`/`.yaml`/`.toml`), and any added line that assigns a real-looking value to a secret key. Edits to an already-tracked `.env` holding only placeholders are allowed.

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

Load order is `.zshenv` (every zsh) -> `.zprofile` (login only) -> `.zshrc` (interactive only). `.zshenv` holds only the Homebrew PATH prepend, since `ssh host <command>` skips `.zprofile`, `.zshrc`, and `path_helper` alike.

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

## Gotchas
- After editing `.tmux.conf`, reload with `Prefix(Ctrl+a) + r` — no tmux restart needed. Copy mode is `Prefix + y` (default `[` is rebound).
- Both Ghostty and kitty configs exist; Ghostty is the primary terminal.
- Remote commands run via `ssh host <command>` get a non-login, non-interactive shell: `.zprofile`, `.zshrc`, and `path_helper` are all skipped. Homebrew tools needed there must get their PATH from `.zshenv` (this is why mosh fails with `mosh-server not found`).
- When adding a new hook script, also add its `ENABLE_*` toggle in `zsh/path.zsh`.
- **Do not move the CLAUDE-omc.md sync back into a SessionStart hook** (relocated 2026-08-29). The doc describes the *installed* plugin version, and that only changes via `claude plugin update` (= `ccpu`). As a hook it ran every session watching for drift the user has to trigger by hand, and when a real bump finally landed (5.0.0 → 5.0.2) it synced exactly one line: the version marker. That cost two separate bug fixes. `ccpu` and `install.sh` now call `scripts/omc-companion-sync.sh` explicitly — the check is bound to its cause instead of polling.
- **Marketplace `autoUpdate` refreshes the catalog only** — it does not bump installed plugin versions (that is `ccpu`). Disabled 2026-07-01 (`7e8eb77`) because the startup git pull caused intermittent plugin load errors; re-enabled 2026-08-29 after v2.1.105, v2.1.232 and v2.1.251 fixed the underlying races. That area was still being patched in 2.1.251, so **if startup plugin-load errors or missing skills come back, suspect `autoUpdate` first**.
- `.claude/settings.json` has a **dual role**: it is user scope via the `~/.claude/settings.json` symlink, and it is also project scope whenever the cwd is `~/.dotfiles`. Claude Code dedupes skills by inode but not settings.json, so both copies load (measured: identical permission rules applied to `userSettings` and `projectSettings`). Keys valid only in user/managed scope — `tipsFile`, `label` — still take effect, but the project copy logs one `[WARN] ... are ignored` line. Harmless, and it recurs for every such key.
- Settings warnings never reach `claude -p` output; capture them with `--debug-file <path>`.
- `block-rm.sh` inspects commands **line by line** (fixed 2026-08-29). It previously folded newlines into spaces, so a multi-line `touch x`⏎`rm x` passed straight through an always-on guard. Trade-off: heredoc content with `rm` at line start is now blocked too — use `\rm` there. The Codex mirror (`.codex/hooks/block-rm.sh`) blocks via the `decision` field with exit 0, not exit 2, so verify it against a different signal.
- Neovim plugin conflicts: run `:Lazy clean` and restart — LazyVim's auto-sync does not always resolve them.

## Security & Privacy
- **Do not commit** `.env.local` or any file containing secrets.
- Use the provided Git identity switching (`git/.gitconfig_personal` vs `git/.gitconfig_company`) based on the directory context.

## Instruction for Antigravity CLI and Legacy Gemini CLI
1. **Tool Usage**: Prefer `npx` for temporary tools and `brew` for persistent system tools.
2. **File Edits**: Use surgical replacements for config files to avoid breaking existing logic.
3. **Shell**: You are operating in a `zsh` environment on `darwin` (macOS). Use modern alternatives (`eza`, `fd`, `bat`) when possible.
4. **Context**: Use the `session-context` provided at session start to remain aware of the current time/date.
