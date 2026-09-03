# Repository Guidelines

## Symlink Architecture (Critical)
- All configs are symlinked from `~/.dotfiles/` into `$HOME` (e.g. `~/.zshrc` → `~/.dotfiles/.zshrc`). **Always edit files inside `~/.dotfiles/`, never the symlinked locations.**
- Exceptions that are NOT symlinks: `~/.gitconfig` is a local stub that `[include]`s `~/.dotfiles/git/.gitconfig`; some `~/.gemini/` files and home-side hook files are managed at runtime. Editing them directly silently diverges from the tracked source.
- cmux hook handling is host-specific: Codex merges hooks from `.codex/config/global.json`, while Antigravity may replace `~/.gemini/config/hooks.json`. Keep the Gemini file on `merge_hooks_json` in `install.sh`; never convert it to `link_file`.

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
- `.codex/hooks/` mirrors `.claude/hooks/`: file-dispatcher, pre-commit-gate, and prompt-rewriter. Hook enablement's source of truth is the `ENABLE_*` variables in `zsh/path.zsh`; Python/Ruff is the only language checker.
- If a hook reports a real violation, fix the flagged content. Do not bypass the hook or change an `ENABLE_*` gate as an agent workaround.

## Gotchas
- After editing `.tmux.conf`, reload with `Prefix(Ctrl+a) + r` — no tmux restart needed. Copy mode is `Prefix + y` (default `[` is rebound).
- Both Ghostty and kitty configs exist; Ghostty is the primary terminal.
- Remote commands run via `ssh host <command>` get a non-login, non-interactive shell: `.zprofile`, `.zshrc`, and `path_helper` are all skipped. Homebrew tools needed there must get their PATH from `.zshenv` (this is why mosh fails with `mosh-server not found`).
- When adding a new hook script, also add its `ENABLE_*` toggle in `zsh/path.zsh`.
- Keep `CLAUDE-omc.md` sync cause-bound: only `ccpu` and `install.sh` call `scripts/omc-companion-sync.sh`. Do not restore it as a `SessionStart` hook.
- Marketplace `autoUpdate` refreshes the catalog; `ccpu` updates installed plugins. If startup plugin-load errors or missing skills recur, investigate `autoUpdate` first.
- `.claude/settings.json` loads as both user and project scope when cwd is `~/.dotfiles`; warnings for user-only keys such as `tipsFile` and `label` are harmless. Capture settings warnings with `--debug-file <path>`, not `claude -p` output.
- `block-rm.sh` inspects commands line by line, so heredoc content beginning with `rm` is also blocked; use `\rm` there. The Codex mirror signals a block through the `decision` field with exit 0, so validate the field rather than the exit code.
- Neovim plugin conflicts: run `:Lazy clean` and restart — LazyVim's auto-sync does not always resolve them.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `type(scope): subject` in imperative mood, no trailing period (for example: `feat(codex-hooks): add lint dispatcher`, `chore(claude): refresh spinner tips`).
- Do NOT use Gitmoji or emoji prefixes; recent history uses Conventional Commits.
- PRs should include:
  - what changed and why
  - impacted paths (for example `zsh/path.zsh`, `.config/nvim/**`)
  - local verification steps and results
- Never include secrets or real `.env` values; keep using `.env.local.example`.
