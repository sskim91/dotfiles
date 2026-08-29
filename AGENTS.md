# Repository Guidelines

## Symlink Architecture (Critical)
- All configs are symlinked from `~/.dotfiles/` into `$HOME` (e.g. `~/.zshrc` → `~/.dotfiles/.zshrc`). **Always edit files inside `~/.dotfiles/`, never the symlinked locations.**
- Exceptions that are NOT symlinks: `~/.gitconfig` is a local stub that `[include]`s `~/.dotfiles/git/.gitconfig`; some `~/.gemini/` files get overwritten by Antigravity at runtime; `~/.codex/hooks.json` gets overwritten by cmux, which merges its own hooks alongside ours (tracked source: `.codex/config/global.json`). Editing those home-side files silently diverges from the tracked source.
- cmux behaves differently per host: on Codex it merges and our 8 hooks survive, on Antigravity it replaces the file and only its own block remains (measured 2026-08-27). `~/.gemini/config/hooks.json` therefore goes through `merge_hooks_json` in `install.sh`, never `link_file` — re-linking it deletes cmux's hooks.

## Project Structure & Module Organization
- Root setup files: `install.sh`, `Brewfile`, `Brewfile.cask`, `.zshenv`, `.zprofile`, `.zshrc`, `.vimrc`, `.pre-commit-config.yaml`.
- Shell customizations live in `zsh/`:
  - `aliases.zsh` for aliases
  - `functions.zsh` for reusable functions
  - `path.zsh` for PATH/env/hook toggles (sourced by `.zprofile`)
- Tool/app configs live in `.config/` (notably `nvim/`, `ghostty/`, `kitty/`, `karabiner/`, `yazi/`, `zed/`).
- Git identity and defaults live in `git/`.
- Automation and checks live in `.claude/hooks/`.
- Utility scripts live in `scripts/` (example: `scripts/yt-transcript.py`).

## Build, Test, and Development Commands
- `./install.sh`: full bootstrap (Homebrew packages, symlinks, runtimes, hooks).
- `brew bundle`: install/update required CLI packages from `Brewfile`.
- `brew bundle --file=Brewfile.cask`: install/update optional GUI applications.
- `source ~/.zshrc` (or `rr`): reload shell configuration after edits.
- `pre-commit install`: install local Git hooks.
- `pre-commit run --all-files`: run formatting, JSON/YAML checks, and secret scanning.
- `zsh -n .zshrc zsh/*.zsh`: syntax-check shell configuration changes.

## Coding Style & Naming Conventions
- Preserve existing style per file type:
  - Shell (`*.sh`, `*.zsh`): POSIX/Bash-friendly syntax, clear guard clauses, lowercase kebab-case file names.
  - Python (`scripts/*.py`): 4-space indentation, type hints where practical, snake_case for functions.
  - Lua (`.config/nvim/lua/**`): follow LazyVim-style modular layout (`config/` vs `plugins/`).
- Keep edits minimal and localized; avoid broad rewrites of stable dotfiles.
- Name new scripts/configs descriptively by tool and purpose (example: `check-hardcoded-secrets.sh`).

## Testing Guidelines
- This repo uses validation checks rather than a dedicated unit-test suite.
- Required before PR/merge: `pre-commit run --all-files`.
- For changed scripts, run targeted checks (for example `python3 -m py_compile scripts/yt-transcript.py`).
- For shell changes, validate with `zsh -n` and a quick interactive reload.

## AI Harness & Hooks
- `.codex/hooks/` mirrors `.claude/hooks/`: file-dispatcher (language checks on edit), pre-commit-gate (sensitive key files always blocked; `.env`/config-file and hardcoded-secret checks are toggled via `ENABLE_ENV_FILE_CHECK` / `ENABLE_SECRET_SCAN` in `zsh/path.zsh`, currently 0 = disabled by user choice), and prompt-rewriter.
- If a hook blocks an operation, fix the flagged content (remove the secret, exclude the file) — do not bypass the hook; toggling `ENABLE_*` gates is a user decision, not an agent workaround.
- Hook language checks are toggled via `ENABLE_*` env vars in `zsh/path.zsh` (e.g. `ENABLE_RUFF=1`; Python/Ruff is the only language checker — JS/TS/Java checkers were removed in the 2026-07 hook audit).

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

## Commit & Pull Request Guidelines
- Use Conventional Commits: `type(scope): subject` in imperative mood, no trailing period (for example: `feat(codex-hooks): add lint dispatcher`, `chore(claude): refresh spinner tips`).
- Do NOT use Gitmoji or emoji prefixes. Recent history is 100% Conventional Commits, and the `git-commit` skill bans emoji prefixes.
- PRs should include:
  - what changed and why
  - impacted paths (for example `zsh/path.zsh`, `.config/nvim/**`)
  - local verification steps and results
- Never include secrets or real `.env` values; keep using `.env.local.example`.
