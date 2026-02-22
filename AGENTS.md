# Repository Guidelines

## Project Structure & Module Organization
- Root setup files: `install.sh`, `Brewfile`, `.zshrc`, `.vimrc`, `.pre-commit-config.yaml`.
- Shell customizations live in `zsh/`:
  - `aliases.zsh` for aliases
  - `functions.zsh` for reusable functions
  - `path.zsh` for PATH/runtime/env toggles
- Tool/app configs live in `.config/` (notably `nvim/`, `ghostty/`, `kitty/`, `karabiner/`, `yazi/`, `zed/`).
- Git identity and defaults live in `git/`.
- Automation and checks live in `.claude/hooks/`.
- Utility scripts live in `scripts/` (example: `scripts/yt-transcript.py`).

## Build, Test, and Development Commands
- `./install.sh`: full bootstrap (Homebrew packages, symlinks, runtimes, hooks).
- `brew bundle`: install/update packages from `Brewfile`.
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

## Commit & Pull Request Guidelines
- Follow the existing concise, imperative style used in history (for example: `fix zsh PATH ordering`, `add yazi flavor setup`).
- Gitmoji-style prefixes are acceptable when consistent with recent commits (for example `:wrench:`, `:sparkles:`, `:memo:`).
- PRs should include:
  - what changed and why
  - impacted paths (for example `zsh/path.zsh`, `.config/nvim/**`)
  - local verification steps and results
- Never include secrets or real `.env` values; keep using `.env.local.example`.
