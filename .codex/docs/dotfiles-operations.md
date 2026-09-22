# Dotfiles 운영 메모

터미널·플러그인·훅의 해당 문제를 다룰 때 필요한 항목만 참고한다.

- After editing `.tmux.conf`, reload with `Prefix(Ctrl+a) + r` — no tmux restart needed. Copy mode is `Prefix + y` (default `[` is rebound).
- Both Ghostty and kitty configs exist; Ghostty is the primary terminal.
- Remote commands run via `ssh host <command>` get a non-login, non-interactive shell: `.zprofile`, `.zshrc`, and `path_helper` are all skipped. Homebrew tools needed there must get their PATH from `.zshenv` (this is why mosh fails with `mosh-server not found`).
- Hook settings belong to the host: Codex uses `CODEX_ENABLE_*` in `.codex/config/hook-settings.sh`; Claude uses `ENABLE_*` in `zsh/path.zsh`.
- Marketplace `autoUpdate` updates installed plugins too, in the background up to ten minutes after a session starts; the running session keeps the version it loaded. A plugin's own "update available" notice therefore shows once per release, in the first session after it, and needs no manual action. There is no `ccpu` any more (removed 2026-09-05; `claude plugin update` has no update-all form). If startup plugin-load errors or missing skills recur, investigate `autoUpdate` first.
- `.claude/settings.json` loads as both user and project scope when cwd is `~/.dotfiles`; warnings for user-only keys such as `tipsFile` and `label` are harmless. Capture settings warnings with `--debug-file <path>`, not `claude -p` output.
- `block-rm.sh` inspects commands line by line, so heredoc content beginning with `rm` is also blocked; use `\rm` there. The Codex mirror signals a block through the `decision` field with exit 0, so validate the field rather than the exit code.
- Neovim plugin conflicts: run `:Lazy clean` and restart — LazyVim's auto-sync does not always resolve them.
