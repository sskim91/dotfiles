# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal dotfiles repository managing macOS development environment. Centralized at `~/.dotfiles` with automated installation and symlink management.

## Quick Commands

```bash
./install.sh              # Full installation (Homebrew, packages, symlinks via Brewfile)
source ~/.zshrc           # Reload shell config (alias: rr)
```

## Symlink Architecture

All configurations are managed via symlinks from home directory to dotfiles:

| Home Location | Dotfiles Source |
|---------------|-----------------|
| `~/.zshrc` | `~/.dotfiles/.zshrc` |
| `~/.zprofile` | `~/.dotfiles/.zprofile` |
| `~/.gitconfig` | `~/.dotfiles/git/.gitconfig` |
| `~/.config/nvim/` | `~/.dotfiles/.config/nvim/` |
| `~/.claude/*` | `~/.dotfiles/.claude/*` |
| `~/.tmux.conf` | `~/.dotfiles/.tmux.conf` |
| `~/.gemini/settings.json` | `~/.dotfiles/.gemini/settings.json` |
| `~/.config/karabiner/` | `~/.dotfiles/.config/karabiner/` |
| `~/.config/ghostty/` | `~/.dotfiles/.config/ghostty/` |
| `~/.config/kitty/` | `~/.dotfiles/.config/kitty/` |
| `~/.config/ruff/ruff.toml` | `~/.dotfiles/.config/ruff/ruff.toml` |
| `~/.config/zed/settings.json` | `~/.dotfiles/.config/zed/settings.json` |
| `~/.config/yazi/` | `~/.dotfiles/.config/yazi/` |
| `~/.config/obsidian/` | `~/.dotfiles/.config/obsidian/` |

**Important**: Edit files in `~/.dotfiles/`, not the symlinked locations.

## Shell Configuration

Modular ZSH configuration loaded from `zsh/`:

| File | Purpose | Sourced By |
|------|---------|------------|
| `path.zsh` | PATH, env vars, Claude hooks ENABLE_* | `.zprofile` |
| `aliases.zsh` | Command shortcuts, tool aliases | `.zshrc` |
| `functions.zsh` | Custom functions (mkd, killport, ccv, etc.) | `.zshrc` |

`.zprofile` sources `path.zsh` (login-time, once). `.zshrc` sources `aliases.zsh` and `functions.zsh` explicitly.

### Adding Aliases/Functions

```bash
# In zsh/aliases.zsh - group related aliases
alias ll='eza -l --git'

# In zsh/functions.zsh - include usage help
function myfunc() {
    [[ -z "$1" ]] && { echo "Usage: myfunc <arg>"; return 1; }
    # implementation
}
```

## Git Configuration

Uses `includeIf` for automatic identity switching:

| Directory | Config File |
|-----------|-------------|
| `~/dev/` | `git/.gitconfig_personal` |
| `~/company-src/` | `git/.gitconfig_company` |

To add new directory-based config:
```gitconfig
# In git/.gitconfig
[includeIf "gitdir:~/new-path/"]
    path = .gitconfig_newname
```

## Claude Code Integration

### Hook System

Settings in `.claude/settings.json`. Hooks execute on file operations:

```
SessionStart → temporal-context.sh (injects current date/time)
UserPromptSubmit → prompt-rewriter.sh (restructures messy prompts)
PreToolUse: if Bash(git commit*) → pre-commit-gate.sh → check-sensitive-files.sh, check-env-files.sh, check-hardcoded-secrets.sh
PreToolUse: if Bash(*rm *) → block-rm.sh (suggests trash instead)
PostToolUse(Write|Edit) → file-dispatcher.sh check
PostToolUse: if Write|Edit(*/dev/TIL/*.md) → til-review.sh (Gemini fact-check, requires ENABLE_TIL_REVIEW=1)
```

**File Dispatcher Pattern**: Routes to `{language}-check.sh` based on extension:
- `.py` → `python-check.sh` (Ruff lint + fix)
- `.java` → `java-check.sh`
- `.ts/.tsx` → `typescript-check.sh`
- `.js/.jsx` → `javascript-check.sh`

**Hook Environment Variables** (configured in `zsh/path.zsh`):

Each hook tool is individually controlled via `ENABLE_*` environment variables:
- `ENABLE_RUFF=1` - Python Ruff linter (default enabled)
- `ENABLE_ESLINT=0`, `ENABLE_TSC=0`, `ENABLE_CHECKSTYLE=0` - Disabled by default

### Adding New Hooks

1. Create script in `.claude/hooks/{language}-{type}.sh`
2. Script receives JSON via stdin, extract path: `jq -r '.tool_input.file_path'`
3. Exit 0 for success, non-zero to block operation

### Hook Debugging

```bash
# Test hook manually
echo '{"tool_input":{"file_path":"test.py"}}' | ~/.claude/hooks/python-check.sh

# Check hook execution logs
# Hooks output goes to Claude Code's stderr
```

### Skills

Located in `.claude/skills/`. Each skill has `SKILL.md` with trigger description.
Run `ls .claude/skills/` to list available skills.

### Adding New Skills

1. Create directory `.claude/skills/{skill-name}/`
2. Create `SKILL.md` with frontmatter:
- `description`: English, single-line. Include "Use when..." trigger hint.
```markdown
---
name: my-skill
description: Short description for Claude. Use when ...
---

# Skill Instructions
...
```

### Agents

Located in `.claude/agents/`. Custom agent configurations for Task tool:
- TDD agents: `tdd-red-agent`, `tdd-green-agent`, `tdd-blue-agent`
- Architecture: `backend-architect`, `database-architect`
- Analysis: `java-enterprise-analyzer`, `python-analysis-expert`, `sql-performance-optimizer`
- ML: `ml-engineer`

## Neovim (LazyVim)

Config in `.config/nvim/`. Uses LazyVim distribution with lazy.nvim.

```bash
nvim                  # Auto-syncs plugins on startup
:Lazy                 # Plugin manager UI
:Mason                # LSP/formatter installer
:LazyExtras           # Enable/disable language support
```

Enabled extras: Python, TypeScript/JavaScript, Java, JSON, Markdown

## Tool Replacements

Standard tools aliased to modern alternatives:
- `cat` → `bat`, `ls` → `eza`, `vim` → `nvim`, `top` → `htop`, `df` → `duf`
- Git pager uses `delta` for enhanced diffs

## AI CLI Wrappers

Custom functions in `zsh/functions.zsh` for AI tool invocation:

| Function | Tool | Options |
|----------|------|---------|
| `ccv` | Claude Code (flag shortcuts) | `-y` (skip permissions), `-d` (dontAsk), `-r` (resume), `-ry` `-rd` (combo) |
| `cco` | Claude Code + Ollama (local model) | Same + `-m <model>` (default: qwen3-coder:30b) |
| `gem` | Gemini CLI | `-y` (yolo), `-r` (resume), `-ry` (both) |
| `cdx` | Codex CLI | `update` (install latest), default: full-auto mode |

## Karabiner Key Mappings

Caps Lock as modifier key (`.config/karabiner/`):

| Shortcut | Action |
|----------|--------|
| Caps+i/k/j/l | Arrow keys (Up/Down/Left/Right) |
| Caps+e/d | Page Up/Down |
| Caps+r/f | Home/End |
| Caps+n/m | Backspace/Delete |

## Version Management

Uses **mise** (asdf replacement) for runtime versions. Activated in `.zprofile`.

## Gotchas

- `.tmux.conf` 변경 후 반드시 `Prefix(Ctrl+a) + r`로 reload — tmux 재시작 불필요
- tmux copy mode 진입: `Prefix + y` (기본 `[`는 window navigation으로 재바인딩됨)
- Ghostty/kitty 둘 다 설정 존재 — 현재 주 터미널은 Ghostty
- `.claude/hooks/` 스크립트는 `ENABLE_*` env var로 개별 제어 — 새 hook 추가 시 `path.zsh`에 변수 추가 필요
- Neovim plugin 충돌 시 `:Lazy clean` 후 재시작 — LazyVim 자동 sync가 해결 못하는 경우 있음
