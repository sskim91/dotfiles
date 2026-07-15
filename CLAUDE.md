# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal dotfiles repository managing macOS development environment. Centralized at `~/.dotfiles` with automated installation and symlink management.

## Quick Commands

```bash
./install.sh              # Full installation (CLI Brewfile, optional casks, symlinks)
source ~/.zshrc           # Reload shell config (alias: rr)
pre-commit run --all-files   # Validate before commit (format, JSON/YAML checks, secret scan)
zsh -n .zshrc zsh/*.zsh      # Syntax-check shell config changes
```

## Commit Convention

Conventional Commits: `type(scope): subject` in imperative mood, no trailing period. No Gitmoji/emoji prefixes (e.g. `feat(codex-hooks): add lint dispatcher`).

## Symlink Architecture

All configurations are managed via symlinks from home directory to dotfiles:

| Home Location | Dotfiles Source |
|---------------|-----------------|
| `~/.zshrc` | `~/.dotfiles/.zshrc` |
| `~/.zprofile` | `~/.dotfiles/.zprofile` |
| `~/.vimrc` | `~/.dotfiles/.vimrc` |
| `~/.gitconfig` | local stub file (not a symlink) — `[include]`s `~/.dotfiles/git/.gitconfig`; Sourcetree-managed sections live here to avoid dirtying tracked file |
| `~/.config/nvim/` | `~/.dotfiles/.config/nvim/` |
| `~/.claude/*` | `~/.dotfiles/.claude/*` |
| `~/.tmux.conf` | `~/.dotfiles/.tmux.conf` |
| `~/.gemini/GEMINI.md` | `~/.dotfiles/.claude/docs/working-style.md` (Antigravity 글로벌 컨텍스트 — Claude/Codex와 동일 정본) |
| `~/.gemini/antigravity-cli/settings.json` | `~/.dotfiles/.gemini/antigravity-cli/settings.json` — Antigravity가 실행 시 실파일로 덮어써 심링크가 깨질 수 있음(`.gitconfig`의 Sourcetree 패턴과 동일). dotfiles 쪽이 정본이며 install.sh 재실행으로 재링크 |
| `~/.gemini/config/{hooks,mcp_config}.json` | `~/.dotfiles/.gemini/antigravity-cli/` — `hooks.json`은 위와 같은 덮어쓰기 드리프트 대상 |
| `~/.codex/hooks.json` | `~/.dotfiles/.codex/config/global.json` — cmux가 자기 훅을 병합한 실파일로 덮어써 심링크가 깨짐(antigravity 패턴과 동일). dotfiles 쪽이 정본이며 `global.json` 수정 시 install.sh 재실행으로 재링크(직후 cmux가 다시 병합·덮어씀) |
| `~/.config/karabiner/assets/complex_modifications/my_custom_key.json` | `~/.dotfiles/.config/karabiner/my_custom_key.json` |
| `~/.config/ghostty/` | `~/.dotfiles/.config/ghostty/` |
| `~/.config/kitty/` | `~/.dotfiles/.config/kitty/` |
| `~/.config/ruff/ruff.toml` | `~/.dotfiles/.config/ruff/ruff.toml` |
| `~/.config/zed/settings.json` | `~/.dotfiles/.config/zed/settings.json` |
| `~/.config/yazi/` | `~/.dotfiles/.config/yazi/` |
| `~/.local/bin/admin-api-token.sh` | `~/.dotfiles/scripts/admin-api-token.sh` |

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
| `~/work/` | `git/.gitconfig_company` |

To add new directory-based config:
```gitconfig
# In git/.gitconfig
[includeIf "gitdir:~/new-path/"]
    path = .gitconfig_newname
```

### Multi-Account GitHub (Personal + Company)

Personal GitHub uses HTTPS via `gh` CLI (active account = `sskim91`). Company GitHub uses SSH with a host alias so a second account can authenticate without `gh auth switch`:

- Generate company key: `ssh-keygen -t ed25519 -C "<company-email>" -f ~/.ssh/company-git`
- Register `~/.ssh/company-git.pub` on the company GitHub account
- Add `Host github.com-company` block to `~/.ssh/config` (see `.ssh-config.example`)
- Clone company repos with the aliased URL: `git@github.com-company:<org>/<repo>.git`
- Place company repos under `~/work/` — `includeIf` then auto-applies company author identity

`includeIf` handles **author email** only; SSH host alias handles **authentication**. Both layers are required for full automation (HTTPS+`gh` cannot do directory-based auth).

## Claude Code Integration

### Hook System

Settings in `.claude/settings.json`. Hooks execute on file operations:

```
SessionStart → session-context.sh (injects current date/time)
SessionStart → link-skills.sh (auto-links new dotfiles skills into ~/.claude/skills/; add-only, idempotent)
SessionStart → omc-companion-sync.sh (syncs ~/.claude/CLAUDE-omc.md with installed OMC plugin version; requires ENABLE_OMC_COMPANION_SYNC=1)
UserPromptSubmit → prompt-rewriter.sh (restructures messy prompts)
PreToolUse: if Bash(git commit*) → pre-commit-gate.sh → check-sensitive-files.sh, check-env-files.sh, check-hardcoded-secrets.sh
PreToolUse: if Bash(*rm *) → block-rm.sh (suggests trash instead)
PostToolUse(Write|Edit) → file-dispatcher.sh check (routes by extension)
PostToolUse(Write|Edit) → til-review.sh (acts only on ~/dev/TIL/*.md; requires ENABLE_TIL_REVIEW=1)
PostToolUse(Write|Edit) → vault-linker.sh (Obsidian vault 링킹 제안; requires ENABLE_VAULT_LINKER=1)
```

**File Dispatcher Pattern**: Routes to `{language}-check.sh` based on extension. Currently `.py` → `python-check.sh` (Ruff lint + fix) only — JS/TS/Java checkers were removed in the 2026-07 hook audit (their tools were all permanently disabled, making the scripts no-ops). To add a language: create `{language}-check.sh`, add a case branch in `file-dispatcher.sh` (both `.claude/hooks/` and `.codex/hooks/`), and add an `ENABLE_*` toggle in `zsh/path.zsh`.

**Hook Environment Variables** (configured in `zsh/path.zsh`):

Each hook tool is individually controlled via `ENABLE_*` environment variables:
- `ENABLE_RUFF=1` - Python Ruff linter (default enabled)
- `ENABLE_TIL_REVIEW=1`, `ENABLE_VAULT_LINKER=0`, `ENABLE_OMC_COMPANION_SYNC=1` - document/review/sync hooks

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

Located in `.claude/agents/`. Custom agent configurations for the Agent tool:
- TDD agents: `tdd-red-agent`, `tdd-green-agent`, `tdd-blue-agent`
- Architecture: `database-architect`
- Development: `fastapi-developer`, `springboot-developer`
- Analysis: `java-enterprise-analyzer`, `python-analysis-expert`, `sql-performance-optimizer`
- ML: `ml-engineer`

**Overlap policy**: plugin/external agents take priority. A custom agent that duplicates a plugin agent gets deleted, not scoped (removed 2026-07: `backend-architect` → oh-my-claudecode:architect, `security-auditor` → oh-my-claudecode:security-reviewer, `python-debugger` → oh-my-claudecode:debugger + superpowers:systematic-debugging).

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
| `cco` | Claude Code + Ollama (local model) | `-y` (skip permissions), `-r` (resume), `-ry` (combo), `-m <model>` (default: qwen3-coder:30b) |
| `agy` | Antigravity CLI | `-y` (skip permissions), `-s` (sandbox), `-r` (continue latest), `-ry` (combo) |
| `gem` | Antigravity CLI if installed, Gemini CLI fallback | `-y` `-r` `-ry` |
| `cdx` | Codex CLI | default: `workspace-write` sandbox + `on-request` approval; `-y` (yolo/bypass), `-r`/`-ra`/`-rl` (resume: picker/all/last), `-ro` (read-only) |

## Multi-Tool AI Harness

This repo configures three AI CLIs in parallel. Each reads its own guidance file:

| Tool | Guidance file | Config/hooks |
|------|---------------|--------------|
| Claude Code | `.claude/CLAUDE.md` (global) + `CLAUDE.md` (this file, project) | `.claude/hooks/`, `.claude/settings.json` |
| Codex CLI | `AGENTS.md` (project) | `.codex/hooks/`, `.codex/config/`, `.codex/rules/`, `.codex/setup-mcp.sh` |
| Antigravity / Gemini CLI | `GEMINI.md` (project) | `.gemini/antigravity-cli/{settings,hooks,mcp_config}.json` |

`.codex/hooks/` mirrors `.claude/hooks/` (file-dispatcher, pre-commit-gate, check-* security gates, prompt-rewriter, language checks) so Codex sessions get the same guardrails.

**Parity checklist** — when changing any of these, update all three guidance files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`):
- Commit convention (Conventional Commits, no emoji)
- Symlink-edit rule (edit in `~/.dotfiles/`, not `$HOME`; `.gitconfig` stub exception)
- Validation commands (`pre-commit run --all-files`, `zsh -n`)
- Gotchas (tmux reload, `ENABLE_*` toggles, primary terminal)
- Security policy (secrets, `.env` handling)

**Global collaboration style** (`.claude/docs/working-style.md`) is shared across all three tools via symlink — `~/.codex/AGENTS.md` and `~/.gemini/GEMINI.md` both symlink to it, and Claude's global `.claude/CLAUDE.md` `@import`s it. Edit collaboration conventions in that one file only; symlinks propagate automatically.

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
