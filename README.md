# dotfiles

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sskim91/dotfiles)

Personal dotfiles for an Apple Silicon macOS development environment.

AI agents asked to install this repository: follow [Agent Installation](#agent-installation) step by step. It separates what you can run from what only the human at the keyboard can do.

## Quick Install (human, in a terminal)

```bash
git clone https://github.com/sskim91/dotfiles.git ~/.dotfiles
cd ~/.dotfiles && ./install.sh
```

Run from a real terminal, `install.sh` handles everything below by itself, including password prompts. Then do [After Installation](#after-installation).

## Agent Installation

Your shell has no TTY. `sudo` cannot ask for a password there and fails immediately, so a few steps must be handed to the human. Everything else you can run.

### 1. Check prerequisites

```bash
uname -m                     # must be arm64 (Homebrew is expected under /opt/homebrew)
xcode-select -p              # Command Line Tools; fails if missing
command -v brew || ls /opt/homebrew/bin/brew
ls -d ~/.dotfiles            # existing checkout?
```

| Missing | Who | What to do |
|---|---|---|
| Command Line Tools | Human | Run `xcode-select --install` and click Install in the dialog (10-15 min). Without it, `git` is only a stub that opens the same dialog. |
| Homebrew | Human | In a terminal: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`. It needs the account password. If you let `install.sh` do it, its `sudo -v` fails in your shell and the run stops with exit 1. |

Ask the human for the missing items, wait until they confirm, then re-check. Do not start `install.sh` until `xcode-select -p` succeeds: without Command Line Tools it opens the install dialog and waits in a loop with no timeout.

### 2. Get the repository

- No `~/.dotfiles`: `git clone https://github.com/sskim91/dotfiles.git ~/.dotfiles`
- `~/.dotfiles` is a git checkout of this repository: do not clone again. `install.sh` updates it itself with `git pull --ff-only`.
- `~/.dotfiles` exists but is not a git checkout: stop and ask the human. The installer would install from it as-is, without updating.

### 3. Run the installer

It takes tens of minutes (Homebrew bundles, GUI apps, Neovim plugins), longer than a typical tool-call timeout. Start it detached, then poll the log:

```bash
nohup bash -c 'eval "$(/opt/homebrew/bin/brew shellenv)" && cd ~/.dotfiles && ./install.sh; echo "exit=$?"' \
  > /tmp/dotfiles-install.log 2>&1 &

tail -n 20 /tmp/dotfiles-install.log   # repeat until the last line is exit=<code>
```

Claude Code: instead of `nohup ... &`, run the inner command with the Bash tool's `run_in_background`; its completion notice replaces polling. Foreground `sleep` is blocked there; if you used `nohup`, wait with a background `until grep -q '^exit=' /tmp/dotfiles-install.log; do sleep 10; done`.

The `brew shellenv` prefix matters on a fresh Mac. Right after Homebrew is installed, `brew` is not on PATH in a new shell yet, and `install.sh` would try to install Homebrew again (and hit `sudo`).

Each real file the installer replaces is moved into a backup directory next to it (`<name>.backup.XXXXXXXX/`). Existing Neovim data, Codex runtime config and Git settings are kept.

### 4. Interpret the result

Judge by the log text, not the exit code alone. A required step that fails returns that command's own status, which can be any non-zero value, including `2`.

| Log shows | Meaning | Your action |
|---|---|---|
| `Dotfiles installation completed!` and `exit=0` | Completed | Go to step 5. |
| `Dotfiles installation partially completed` and `exit=2` | Required steps done, optional steps failed | Report the listed failures. GUI apps that need a password fail in your shell; the human re-runs `brew bundle --file=~/.dotfiles/Brewfile.cask` in a terminal. |
| Anything else with a non-zero exit | Stopped | Report the exit code and the last error lines of the log (most start with `❌`). |

If it stops on the self-update (`requires the main branch`, `requires a clean checkout`, `Self-update failed`), report and stop. Do not stash, reset, merge, or switch branches; those local changes belong to the human.

Re-running is how optional failures are retried. The installer leaves the checkout clean: Neovim plugins are pinned to the tracked `.config/nvim/lazy-lock.json` without rewriting it.

If it stops right after `Changing default shell to zsh...`, `chsh` asked for a password. Everything else is already installed; the human runs `chsh -s /bin/zsh` in a terminal.

### 5. Verify

```bash
readlink ~/.zshrc                              # -> ~/.dotfiles/.zshrc
readlink ~/.claude/settings.json               # -> ~/.dotfiles/.claude/settings.json
git config --global --get-all include.path     # includes ~/.dotfiles/git/.gitconfig
zsh -ic 'whence -w ccv cdx'                    # ccv: function / cdx: function
brew bundle check --file=~/.dotfiles/Brewfile  # dependencies satisfied
zsh -ic 'claude --version; codex --version'    # Codex CLI lives under mise's node, so use the new shell
```

Report each result. A failing check is a finding to report, not something to work around.

### 6. Hand off to the human

End with this list. These steps need the human's accounts, secrets, or GUI approvals:

- [ ] API keys: `cp ~/.dotfiles/.env.local.example ~/.dotfiles/.env.local`, fill in the values, then re-run `~/.dotfiles/.claude/setup-mcp.sh` and `~/.dotfiles/.codex/setup-mcp.sh` (Claude's YouTrack MCP is registered only when its keys are set).
- [ ] Logins: `gh auth login`, `claude` (first run), `codex login`.
- [ ] Company GitHub: SSH key and host alias, see [git/CLAUDE.md](git/CLAUDE.md).
- [ ] Karabiner-Elements: approve the driver extension and Input Monitoring in System Settings.
- [ ] GUI apps that failed in the agent run: `brew bundle --file=~/.dotfiles/Brewfile.cask`.
- [ ] Restart the terminal (or `source ~/.zshrc`).

### Rules for agents

- Never run `sudo` or try to get around a password prompt. Hand that step to the human.
- Do not read, create, or fill `.env.local`. Secrets are entered by the human.
- After installation, edit configuration in `~/.dotfiles`, not the symlinked paths under `$HOME`. `~/.gitconfig` is a small stub file that includes `~/.dotfiles/git/.gitconfig`, not a symlink.
- Do not commit or push unless asked.
- For later work inside the repository, read the guidance file for your tool: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex), `GEMINI.md` (Antigravity/Gemini).

## After Installation

The same checklist as step 6 of the agent flow, for a human-only install: API keys in `.env.local` and the MCP setup scripts, `gh`/`claude`/`codex` logins, the company GitHub SSH key ([git/CLAUDE.md](git/CLAUDE.md)), Karabiner permissions, and a terminal restart.

## Structure

- **zsh/** - Aliases, functions, PATH/env vars
- **git/** - Git config with conditional identity switching
- **.config/** - Neovim (LazyVim), Ghostty, Kitty, Karabiner, Zed
- **.claude/** - Claude Code hooks, skills, rules, settings
- **.codex/** - Codex CLI config template, hooks, skills
- **.gemini/** - Gemini CLI and Antigravity CLI config
- **vault/** - Obsidian vault tooling (`vk`)
- **Brewfile** - Required Homebrew CLI packages
- **Brewfile.cask** - Optional Homebrew GUI applications

## Key Aliases

```bash
vim → nvim    cat → bat    ls → eza    top → htop    df → duf
```

## AI CLI Wrappers

| Function | Tool | Flags |
|----------|------|-------|
| `ccv` | Claude Code | `-y` `-d` `-r` `-ry` `-rd` `-R` |
| `cco` | Claude + Ollama | `-y` `-r` `-ry` `-m <model>` |
| `agy` | Antigravity CLI | `-y` `-s` `-r` `-ry` |
| `gem` | Antigravity CLI if installed, Gemini CLI fallback | `-y` `-r` `-ry` |
| `cdx` | Codex CLI | `-y` `-r` `-ra` `-rl` `-ro` |

## Development

Installer regression tests run in temporary directories without installing apps:

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
pre-commit run --all-files
```

## License

MIT
