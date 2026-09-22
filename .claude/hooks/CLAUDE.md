# Claude Code Hooks

이 디렉터리의 훅 스크립트 구조와 토글. 훅 관련 함정(`block-rm.sh` 줄 단위 검사, SessionStart 페이로드에 `model` 없음)은 루트 `CLAUDE.md`의 Gotchas에 있다.

## Hook System

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

`link-skills.sh`는 add-only라 dotfiles에서 스킬 디렉터리를 지워도 `~/.claude/skills/`의 심링크는 남는다. 스킬을 삭제하면 끊어진 링크를 직접 정리한다 (2026-09-16 `/doctor`에서 11개 정리).

**File Dispatcher Pattern**: Routes to `{language}-check.sh` based on extension. Currently `.py` → `python-check.sh` (Ruff lint + fix) only — JS/TS/Java checkers were removed in the 2026-07 hook audit (their tools were all permanently disabled, making the scripts no-ops). To add a language: create `{language}-check.sh`, add a case branch in `file-dispatcher.sh` (both `.claude/hooks/` and `.codex/hooks/`), and add an `ENABLE_*` toggle in `zsh/path.zsh`.

**Hook Environment Variables** (configured in `zsh/path.zsh`):

Each hook tool is individually controlled via `ENABLE_*` environment variables:
- `ENABLE_RUFF=1` - Python Ruff linter (default enabled)
- `ENABLE_TIL_REVIEW=1`, `ENABLE_VAULT_LINKER=0` - document/review hooks
- `ENABLE_ENV_FILE_CHECK=0`, `ENABLE_SECRET_SCAN=0` - commit security gates (currently disabled by user choice; set to 1 to re-enable)

## Known slow path

`til-review.sh`는 외부 CLI(Codex·Antigravity)를 호출하며 도구별 190초 타임아웃과 1회 재시도를 가진다(settings.json 훅 timeout 400). 2026-08-15~16 TIL 세션에서 45회 연속 약 190초로 끝난 기록이 있어, 한 도구가 매번 타임아웃에 걸린 것으로 보인다. 재발하면 어느 도구가 멈추는지 확인하거나 훅을 `async`로 전환한다.
