# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

All configurations are managed via symlinks from home directory to dotfiles. The full link map lives in `install.sh`; only the entries that are **not** plain symlinks, or that carry a trap, are recorded here:

| Home Location | Dotfiles Source |
|---------------|-----------------|
| `~/.gitconfig` | local stub file (not a symlink) — `[include]`s `~/.dotfiles/git/.gitconfig`; Sourcetree-managed sections live here to avoid dirtying tracked file |
| `~/.gemini/GEMINI.md` | `~/.dotfiles/.claude/docs/working-style.md` (Antigravity 글로벌 컨텍스트 — Claude/Codex와 동일 정본) |
| `~/.gemini/antigravity-cli/settings.json` | `~/.dotfiles/.gemini/antigravity-cli/settings.json` — Antigravity가 실행 시 실파일로 덮어써 심링크가 깨질 수 있음(`.gitconfig`의 Sourcetree 패턴과 동일). dotfiles 쪽이 정본이며 install.sh 재실행으로 재링크 |
| `~/.gemini/config/mcp_config.json` | `~/.dotfiles/.gemini/antigravity-cli/mcp_config.json` — 심링크 |
| `~/.gemini/config/hooks.json` | `~/.dotfiles/.gemini/antigravity-cli/hooks.json` — **심링크가 아니라 병합 대상.** cmux가 이 파일을 실파일로 **교체**하며 자기 `cmux` 블록만 남긴다(Codex와 달리 사용자 훅을 보존하지 않음 — 2026-08-27 실측). install.sh는 `merge_hooks_json`으로 최상위 키를 병합해 양쪽을 살린다. 재링크하면 cmux 훅이 삭제되므로 `link_file`을 쓰지 말 것 |
| `~/.codex/hooks.json` | `~/.dotfiles/.codex/config/global.json` — cmux가 실파일로 덮어쓰되 **사용자 훅 8종을 보존한 채 자기 것을 추가**한다(Antigravity와 동작이 다름). `.hooks` 객체를 공유하는 구조라 최상위 병합이 불가하므로 `link_file`을 유지한다. install.sh 재실행 시 cmux 훅이 일시적으로 사라지지만 cmux 다음 실행에서 다시 병합된다 |

**Important**: Edit files in `~/.dotfiles/`, not the symlinked locations.

## Git Configuration

Author identity switches by directory via `includeIf` in `git/.gitconfig` (`~/dev/` personal, `~/work/`·`~/company-src/` company). Company GitHub uses a second account over an SSH host alias — setup steps and the two-layer (identity vs. authentication) rationale are in `git/CLAUDE.md`.

## Claude Code Integration

### Hook System

Settings in `.claude/settings.json`. The hook flow, file-dispatcher pattern, and `ENABLE_*` toggles are documented in `.claude/hooks/CLAUDE.md` (loaded when working on files in that directory). Hook-related traps stay in Gotchas below.

### Skills

Located in `.claude/skills/`. Classification, review criteria, authoring conventions, and removal history are in `.claude/skills/CLAUDE.md`.

2026-09에 삭제한 스킬은 복원하지 않는다. `.claude/skills/`와 `.codex/skills/`는 독립된 정본이다 — 한쪽에만 필요한 스킬의 추가·삭제를 다른 쪽에 강제하지 않는다. Codex 구성은 [.codex/README.md](.codex/README.md)를 참고한다.

### Agents

커스텀 에이전트 10개는 역할 중복을 줄이기 위해 2026-09에 제거했다. `.claude/agents/`는 복원하지 않는다. 이후 작업은 현재 설치·활성화된 도구와 플러그인의 실제 기능을 확인해 수행한다. 플러그인이 이전 에이전트의 작업 품질을 동등하게 대체하는지는 별도 작업 검증이 필요하다.

새 에이전트는 기존 도구와 역할이 겹치는지, 고유한 업무 규칙이나 자원이 필요한지 확인한 뒤 검토한다.

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

Claude Code 플러그인은 수동 갱신 명령이 없다. 마켓플레이스 `autoUpdate`가 설치본까지 백그라운드로 올린다 — 상세는 Gotchas 참조.

작업 프로세스 레이어는 superpowers 플러그인이다(글로벌 `.claude/CLAUDE.md`의 "기본 프로세스" 절). oh-my-claudecode(OMC)는 2026-09-22에 플러그인·마켓플레이스·companion 파일·동기화 훅·`.omc/` 상태를 모두 제거했다. 복원하지 않는다.

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

## Gotchas

- `.tmux.conf` 변경 후 반드시 `Prefix(Ctrl+a) + r`로 reload — tmux 재시작 불필요
- tmux copy mode 진입: `Prefix + y` (기본 `[`는 window navigation으로 재바인딩됨)
- Ghostty/kitty 둘 다 설정 존재 — 현재 주 터미널은 Ghostty
- `ssh host <command>`로 실행되는 원격 명령은 non-login·non-interactive 셸이라 `.zprofile`/`.zshrc`/`path_helper`가 모두 건너뛰어진다. brew 도구를 원격 명령에서 써야 하면 `.zshenv`에 PATH를 넣어야 한다 (mosh가 `mosh-server not found`로 실패하는 전형적 원인)
- `.claude/hooks/` 스크립트는 `ENABLE_*` env var로 개별 제어 — 새 hook 추가 시 `path.zsh`에 변수 추가 필요
- **마켓플레이스 `autoUpdate`는 설치된 플러그인까지 올린다** (공식 문서·2026-09-05 실측). 세션 시작 후 최대 10분 무작위 지연을 두고 백그라운드로 카탈로그 갱신과 설치본 업데이트를 함께 수행한다. 실행 중인 세션은 시작 시점 버전을 계속 쓰고, 새 버전은 다음 실행 또는 `/reload-plugins`에서 로드된다. 플러그인 자체의 "업데이트 있음" 경고가 새 릴리스 직후 첫 세션에 한 번 뜨는 것은 이 순서 때문이며 수동 조치가 필요 없다. 2026-08-29~09-05 사이 이 저장소는 "카탈로그만 갱신한다"고 잘못 적어 두었고, 그 전제로 `ccpu` 함수를 유지했다(09-05 삭제. `claude plugin update`는 플러그인 이름을 요구해 update-all 형태가 없다). 2026-07-01(`7e8eb77`)에 startup git pull이 간헐적 로드 에러를 내서 껐다가 2026-08-29에 다시 켠 이력은 그대로다. **startup에 plugin load 에러나 스킬 누락이 재발하면 `autoUpdate`부터 의심할 것**
- `.claude/settings.json`은 **이중 역할**이다 — `~/.claude/settings.json` 심링크로 user 스코프이면서, `~/.dotfiles`에서 작업할 땐 같은 경로가 project 스코프다. Claude Code는 스킬은 inode로 중복 제거하지만 settings.json은 하지 않아 **양쪽 모두 로드된다**(실측: 동일 권한 규칙이 `userSettings`·`projectSettings` 양쪽에 적용). 그래서 `tipsFile`·`label`처럼 **user/managed 스코프에서만 유효한 키**를 쓰면 값은 정상 적용되지만 project 사본에 대해 `[WARN] ... are ignored` 한 줄이 남는다. 무해하지만 앞으로 그런 키마다 재발한다
- 설정 관련 경고는 `claude -p` 출력에 안 나온다. `--debug-file <path>`로 받아야 보인다 (2026-08-29에 이걸 못 찾아 "검증 불가"로 오판한 적 있음)
- `block-rm.sh`는 명령을 **줄 단위로** 검사한다 (2026-08-29 수정). 이전에는 개행을 공백으로 뭉개서 `touch x`⏎`rm x` 같은 멀티라인 삭제가 상시 가드를 그대로 통과했다. 대가로 heredoc 본문에 줄 처음부터 `rm`이 오면 오탐 차단되니, 그럴 때는 `\rm`을 쓴다. Codex 미러(`.codex/hooks/block-rm.sh`)는 exit 2가 아니라 `decision` 필드로 차단하므로 검증 기준이 다르다
- **SessionStart 훅 페이로드에는 `model` 필드가 없다** (2026-09-03, 2.1.259 실측: `{hook_event_name, source}`만 옴). PostModelSwitch도 초기 모델에는 안 뜬다. `model-context.sh`는 그래서 `ANTHROPIC_MODEL` → settings `model` 키 순으로 폴백해 새 세션의 모델을 판별한다. `claude --model X` 일회성 플래그는 이 경로에서 보이지 않는다. 페이로드 감사는 `MODEL_CONTEXT_DEBUG=<file>`로 원본을 받아서 한다
- **`claude-plugins-official`은 플러그인을 커밋 sha로 고정한다.** superpowers가 upstream 6.4.1인데 official은 6.3.0을 가리켜(2026-09-22) `obra/superpowers-marketplace`(sha 없이 upstream URL 추적)로 전환했다. 두 마켓플레이스에서 같은 플러그인을 동시에 켜면 스킬이 중복되니 하나만 활성화한다. 설치 스코프가 user·project 둘로 남아 있으면 `claude plugin uninstall`을 스코프별로 두 번 해야 레지스트리에서 사라진다
- `superpowers-context.sh`(SessionStart `resume|fork`)는 superpowers 플러그인 훅의 matcher가 `startup|clear|compact`뿐이라 추가한 보강이다 (2026-09-22, 6.4.1 기준). 플러그인이 자기 matcher에 `resume`을 넣으면 `<EXTREMELY_IMPORTANT>` 블록이 이중 주입되니 그때 이 훅을 제거한다
- Neovim plugin 충돌 시 `:Lazy clean` 후 재시작 — LazyVim 자동 sync가 해결 못하는 경우 있음
