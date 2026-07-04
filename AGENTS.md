# Repository Guidelines

## Symlink Architecture (Critical)
- All configs are symlinked from `~/.dotfiles/` into `$HOME` (e.g. `~/.zshrc` → `~/.dotfiles/.zshrc`). **Always edit files inside `~/.dotfiles/`, never the symlinked locations.**
- Exceptions that are NOT symlinks: `~/.gitconfig` is a local stub that `[include]`s `~/.dotfiles/git/.gitconfig`; some `~/.gemini/` files get overwritten by Antigravity at runtime. Editing those home-side files silently diverges from the tracked source.

## Project Structure & Module Organization
- Root setup files: `install.sh`, `Brewfile`, `Brewfile.cask`, `.zprofile`, `.zshrc`, `.vimrc`, `.pre-commit-config.yaml`.
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
- `.codex/hooks/` mirrors `.claude/hooks/`: file-dispatcher (language checks on edit), pre-commit-gate (blocks commits touching sensitive files, `.env` files, or hardcoded secrets), and prompt-rewriter.
- If a hook blocks an operation, fix the flagged content (remove the secret, exclude the file) — do not bypass or disable the hook.
- Hook language checks are toggled via `ENABLE_*` env vars in `zsh/path.zsh` (e.g. `ENABLE_RUFF=1`; ESLint/tsc/Biome/Checkstyle default off).

## Gotchas
- After editing `.tmux.conf`, reload with `Prefix(Ctrl+a) + r` — no tmux restart needed. Copy mode is `Prefix + y` (default `[` is rebound).
- Both Ghostty and kitty configs exist; Ghostty is the primary terminal.
- When adding a new hook script, also add its `ENABLE_*` toggle in `zsh/path.zsh`.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `type(scope): subject` in imperative mood, no trailing period (for example: `feat(codex-hooks): add lint dispatcher`, `chore(claude): refresh spinner tips`).
- Do NOT use Gitmoji or emoji prefixes. Recent history is 100% Conventional Commits, and the `git-commit` skill bans emoji prefixes.
- PRs should include:
  - what changed and why
  - impacted paths (for example `zsh/path.zsh`, `.config/nvim/**`)
  - local verification steps and results
- Never include secrets or real `.env` values; keep using `.env.local.example`.
