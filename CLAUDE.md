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
| `~/.gitconfig` | `~/.dotfiles/git/.gitconfig` |
| `~/.config/nvim/` | `~/.dotfiles/.config/nvim/` |
| `~/.claude/*` | `~/.dotfiles/.claude/*` |
| `~/.tmux.conf` | `~/.dotfiles/.tmux.conf` |
| `~/.gemini/settings.json` | `~/.dotfiles/.gemini/settings.json` |
| `~/.config/karabiner/` | `~/.dotfiles/.config/karabiner/` |
| `~/.config/ghostty/` | `~/.dotfiles/.config/ghostty/` |
| `~/.config/kitty/` | `~/.dotfiles/.config/kitty/` |
| `~/.config/zed/settings.json` | `~/.dotfiles/.config/zed/settings.json` |

**Important**: Edit files in `~/.dotfiles/`, not the symlinked locations.

## Shell Configuration

Modular ZSH configuration loaded from `zsh/`:

| File | Purpose |
|------|---------|
| `aliases.zsh` | Command shortcuts, tool aliases |
| `functions.zsh` | Custom functions (mkd, killport, extract, ccv, etc.) |
| `path.zsh` | PATH, environment variables, tool activation |

All loaded via `.zshrc`: `source <(cat $DOTFILES/zsh/*zsh)`

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
PreToolUse(git commit) → check-sensitive-files.sh, check-env-files.sh, check-hardcoded-secrets.sh
PostToolUse(Write|Edit) → file-dispatcher.sh check → file-dispatcher.sh review
```

**File Dispatcher Pattern**: Routes to `{language}-{type}.sh` based on extension:
- `.py` → `python-check.sh`, `python-review.sh`
- `.java` → `java-check.sh`
- `.ts/.tsx` → `typescript-check.sh`
- `.js/.jsx` → `javascript-check.sh`
- `~/dev/TIL/*.md` → `til-review.sh` (Gemini review, requires `ENABLE_TIL_REVIEW=1`)

**Hook Environment Variables** (configured in `zsh/path.zsh`):

Each hook tool is individually controlled via `ENABLE_*` environment variables:
- `ENABLE_RUFF=1` - Python Ruff linter (default enabled)
- `ENABLE_TIL_REVIEW=1` - TIL document Gemini review (default enabled)
- `ENABLE_ESLINT=0`, `ENABLE_TSC=0`, `ENABLE_CHECKSTYLE=0` - Disabled by default
- `ENABLE_GEMINI_REVIEW=0` - AI code review for all languages (disabled by default)

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

Located in `.claude/skills/`. Each skill is a directory with `SKILL.md`:

| Skill | Trigger |
|-------|---------|
| `til` | TIL 문서 작성 |
| `obsidian-note` | Obsidian Zettelkasten 노트 작성 |
| `obsidian-flashcard` | Obsidian Spaced Repetition 플래시카드 |
| `tech-blog-writer` | 기술 블로그 글쓰기 |
| `learning-tracker` | 세션 학습 내용 정리 |
| `project-overview` | 프로젝트 온보딩 분석 |
| `github-actions` | GitHub Actions 실패 분석 |
| `gemini-fetch` | WebFetch 403 우회 |
| `devlog` | 작업 로그 기록 |
| `session-handoff` | 세션 인계 요약 생성 |
| `git-commit` | Gitmoji 커밋 메시지 |
| `git-commit-and-push` | 커밋 + 푸시 |
| `git-push` | 안전한 푸시 |
| `sql-optimization-patterns` | SQL 쿼리 최적화 패턴 |
| `sns-writer` | X/Threads 초안을 단단한 글로 다듬기 |
| `skill-writer` | 새 스킬 작성 가이드 |
| `mcp-integration` | MCP 서버 통합 |
| `init-serena` | Serena MCP 초기화 |
| `cc-team-builder` | Agent Team 대화형 구성 위저드 |

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

Uses **mise** (asdf replacement) for runtime versions. Activated in `path.zsh`.
