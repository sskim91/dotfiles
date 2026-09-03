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
| `~/.zshenv` | `~/.dotfiles/.zshenv` |
| `~/.zshrc` | `~/.dotfiles/.zshrc` |
| `~/.zprofile` | `~/.dotfiles/.zprofile` |
| `~/.vimrc` | `~/.dotfiles/.vimrc` |
| `~/.gitconfig` | local stub file (not a symlink) — `[include]`s `~/.dotfiles/git/.gitconfig`; Sourcetree-managed sections live here to avoid dirtying tracked file |
| `~/.config/nvim/` | `~/.dotfiles/.config/nvim/` |
| `~/.claude/*` | `~/.dotfiles/.claude/*` |
| `~/.tmux.conf` | `~/.dotfiles/.tmux.conf` |
| `~/.gemini/GEMINI.md` | `~/.dotfiles/.claude/docs/working-style.md` (Antigravity 글로벌 컨텍스트 — Claude/Codex와 동일 정본) |
| `~/.gemini/antigravity-cli/settings.json` | `~/.dotfiles/.gemini/antigravity-cli/settings.json` — Antigravity가 실행 시 실파일로 덮어써 심링크가 깨질 수 있음(`.gitconfig`의 Sourcetree 패턴과 동일). dotfiles 쪽이 정본이며 install.sh 재실행으로 재링크 |
| `~/.gemini/config/mcp_config.json` | `~/.dotfiles/.gemini/antigravity-cli/mcp_config.json` — 심링크 |
| `~/.gemini/config/hooks.json` | `~/.dotfiles/.gemini/antigravity-cli/hooks.json` — **심링크가 아니라 병합 대상.** cmux가 이 파일을 실파일로 **교체**하며 자기 `cmux` 블록만 남긴다(Codex와 달리 사용자 훅을 보존하지 않음 — 2026-08-27 실측). install.sh는 `merge_hooks_json`으로 최상위 키를 병합해 양쪽을 살린다. 재링크하면 cmux 훅이 삭제되므로 `link_file`을 쓰지 말 것 |
| `~/.codex/hooks.json` | `~/.dotfiles/.codex/config/global.json` — cmux가 실파일로 덮어쓰되 **사용자 훅 8종을 보존한 채 자기 것을 추가**한다(Antigravity와 동작이 다름). `.hooks` 객체를 공유하는 구조라 최상위 병합이 불가하므로 `link_file`을 유지한다. install.sh 재실행 시 cmux 훅이 일시적으로 사라지지만 cmux 다음 실행에서 다시 병합된다 |
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

Load order: `.zshenv` (every zsh) -> `.zprofile` (login only) -> `.zshrc` (interactive only).

`.zshenv` carries only the Homebrew PATH prepend, because `ssh host <command>` runs a
non-login, non-interactive shell — `.zprofile`, `.zshrc`, and `/etc/zprofile`'s
`path_helper` are all skipped there, so `/opt/homebrew/bin` would be missing.

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
SessionStart · PostModelSwitch → model-context.sh (Opus 5 세션에만 간결성·위임 제한 지침 주입; Fable은 하네스가 자체 주입하므로 무출력. `ENABLE_MODEL_CONTEXT`)
UserPromptSubmit → prompt-rewriter.sh (restructures messy prompts)
PreToolUse: if Bash(git commit*) → pre-commit-gate.sh → check-sensitive-files.sh, check-env-files.sh, check-hardcoded-secrets.sh
  ├ check-env-files.sh (`ENABLE_ENV_FILE_CHECK`, 현재 0=비활성) 차단 대상: ① 새로 추가되는 .env류 ② 구조화 설정 파일(credentials/secrets/config.local의 .json/.yaml/.toml — key: value 문법이라 값 검사 불가) ③ 추적 파일이라도 추가된 줄이 시크릿 키에 실값을 할당하는 경우. placeholder만 든 추적 .env의 수정은 허용
  ├ check-hardcoded-secrets.sh (`ENABLE_SECRET_SCAN`, 현재 0=비활성): 코드 diff에서 API 키·토큰·credential URL 패턴 차단
  └ check-sensitive-files.sh: 키 파일(id_rsa·.pem 등) 차단 — 토글 없이 상시 활성
PreToolUse: if Bash(*rm *) → block-rm.sh (줄 단위 검사, trash 사용 제안; `\rm`·`command rm`은 허용)
PostToolUse(Write|Edit) → file-dispatcher.sh check (routes by extension)
PostToolUse(Write|Edit) → til-review.sh (acts only on ~/dev/TIL/*.md; requires ENABLE_TIL_REVIEW=1)
PostToolUse(Write|Edit) → vault-linker.sh (Obsidian vault 링킹 제안; requires ENABLE_VAULT_LINKER=1)
```

**File Dispatcher Pattern**: Routes to `{language}-check.sh` based on extension. Currently `.py` → `python-check.sh` (Ruff lint + fix) only — JS/TS/Java checkers were removed in the 2026-07 hook audit (their tools were all permanently disabled, making the scripts no-ops). To add a language: create `{language}-check.sh`, add a case branch in `file-dispatcher.sh` (both `.claude/hooks/` and `.codex/hooks/`), and add an `ENABLE_*` toggle in `zsh/path.zsh`.

**Hook Environment Variables** (configured in `zsh/path.zsh`):

Each hook tool is individually controlled via `ENABLE_*` environment variables:
- `ENABLE_RUFF=1` - Python Ruff linter (default enabled)
- `ENABLE_TIL_REVIEW=1`, `ENABLE_VAULT_LINKER=0` - document/review hooks
- `ENABLE_ENV_FILE_CHECK=0`, `ENABLE_SECRET_SCAN=0` - commit security gates (currently disabled by user choice; set to 1 to re-enable)

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

3. Claude·Codex 겸용 Skill은 선택적으로 `agents/openai.yaml`을 포함한다. Claude Code는 이 파일을 무시하고, Codex는 Skill 목록과 호출 UI의 metadata로 사용한다.

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
| `ccv` | Claude Code (flag shortcuts) | `-y` (skip permissions), `-d` (dontAsk), `-r` (resume), `-ry` `-rd` (combo), `-R` (restricted) |
| `cco` | Claude Code + Ollama (local model) | `-y` (skip permissions), `-r` (resume), `-ry` (combo), `-m <model>` (default: qwen3-coder:30b) |
| `agy` | Antigravity CLI | `-y` (skip permissions), `-s` (sandbox), `-r` (continue latest), `-ry` (combo) |
| `gem` | Antigravity CLI if installed, Gemini CLI fallback | `-y` `-r` `-ry` |
| `cdx` | Codex CLI | default: `workspace-write` sandbox + `on-request` approval; `-y` (yolo/bypass), `-r`/`-ra`/`-rl` (resume: picker/all/last), `-ro` (read-only) |

`ccv -R`(`--restricted`, v2.1.248+)은 명령·코드 실행 도구와 WebFetch를 제거하고, 파일 도구를 cwd 안으로 묶고, **user/project/local 설정을 전부 무시**한다. 마지막 항목이 핵심 — 전역 `Bash(*)` allow와 `skipDangerousModePermissionPrompt: true`를 무력화하는 유일한 스위치다. 신뢰하지 않는 저장소를 열 때 쓴다. `-y`와 함께 쓰지 않는다 (restricted는 `bypassPermissions`를 거부).

백그라운드 세션 관리는 `claude attach <id>` / `logs` / `stop` / `respawn` / `rm` (v2.1.251에서 `--help`에 노출). 실행 중인 세션에 `--resume`을 걸면 정확한 `attach` 명령을 안내해준다.

`ccpu`는 전 scope의 플러그인을 업데이트하고, 이어서 `scripts/omc-companion-sync.sh -q`로 `~/.claude/CLAUDE-omc.md`를 갱신한다. 이 동기화는 **SessionStart 훅이 아니다** — 근거는 Gotchas 참조.

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
- `ssh host <command>`로 실행되는 원격 명령은 non-login·non-interactive 셸이라 `.zprofile`/`.zshrc`/`path_helper`가 모두 건너뛰어진다. brew 도구를 원격 명령에서 써야 하면 `.zshenv`에 PATH를 넣어야 한다 (mosh가 `mosh-server not found`로 실패하는 전형적 원인)
- `.claude/hooks/` 스크립트는 `ENABLE_*` env var로 개별 제어 — 새 hook 추가 시 `path.zsh`에 변수 추가 필요
- **CLAUDE-omc.md 동기화를 SessionStart 훅으로 되돌리지 말 것** (2026-08-29 이관). 이 문서가 기술하는 건 **설치된** 플러그인 버전이고, 그 버전은 `claude plugin update`(= `ccpu`)로만 바뀐다. 훅은 매 세션 돌면서 사용자가 직접 쳐야만 생기는 드리프트를 감시했고, 실제 5.0.0→5.0.2 버전업에서 동기화한 내용은 버전 주석 한 줄이었다(지침 본문은 바이트 동일). 그 대가로 버그를 두 번 고쳤다. 지금은 `ccpu`와 `install.sh`가 `scripts/omc-companion-sync.sh`를 명시 호출한다 — 감시를 폴링이 아니라 원인 지점에 붙인 것
- **마켓플레이스 `autoUpdate`는 카탈로그만 갱신한다** — 설치된 플러그인 버전은 올리지 않는다(그건 `ccpu`). 2026-07-01(`7e8eb77`)에 startup git pull이 간헐적 로드 에러를 내서 껐다가, 2026-08-29에 다시 켰다. 그 사이 v2.1.105·v2.1.232·v2.1.251로 근본 원인이 개선됐지만 2.1.251에서도 여전히 손보는 영역이다. **startup에 plugin load 에러나 스킬 누락이 재발하면 `autoUpdate`부터 의심할 것**
- `.claude/settings.json`은 **이중 역할**이다 — `~/.claude/settings.json` 심링크로 user 스코프이면서, `~/.dotfiles`에서 작업할 땐 같은 경로가 project 스코프다. Claude Code는 스킬은 inode로 중복 제거하지만 settings.json은 하지 않아 **양쪽 모두 로드된다**(실측: 동일 권한 규칙이 `userSettings`·`projectSettings` 양쪽에 적용). 그래서 `tipsFile`·`label`처럼 **user/managed 스코프에서만 유효한 키**를 쓰면 값은 정상 적용되지만 project 사본에 대해 `[WARN] ... are ignored` 한 줄이 남는다. 무해하지만 앞으로 그런 키마다 재발한다
- 설정 관련 경고는 `claude -p` 출력에 안 나온다. `--debug-file <path>`로 받아야 보인다 (2026-08-29에 이걸 못 찾아 "검증 불가"로 오판한 적 있음)
- `block-rm.sh`는 명령을 **줄 단위로** 검사한다 (2026-08-29 수정). 이전에는 개행을 공백으로 뭉개서 `touch x`⏎`rm x` 같은 멀티라인 삭제가 상시 가드를 그대로 통과했다. 대가로 heredoc 본문에 줄 처음부터 `rm`이 오면 오탐 차단되니, 그럴 때는 `\rm`을 쓴다. Codex 미러(`.codex/hooks/block-rm.sh`)는 exit 2가 아니라 `decision` 필드로 차단하므로 검증 기준이 다르다
- **SessionStart 훅 페이로드에는 `model` 필드가 없다** (2026-09-03, 2.1.259 실측: `{hook_event_name, source}`만 옴). PostModelSwitch도 초기 모델에는 안 뜬다. `model-context.sh`는 그래서 `ANTHROPIC_MODEL` → settings `model` 키 순으로 폴백해 새 세션의 모델을 판별한다. `claude --model X` 일회성 플래그는 이 경로에서 보이지 않는다. 페이로드 감사는 `MODEL_CONTEXT_DEBUG=<file>`로 원본을 받아서 한다
- Neovim plugin 충돌 시 `:Lazy clean` 후 재시작 — LazyVim 자동 sync가 해결 못하는 경우 있음
