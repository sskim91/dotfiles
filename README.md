# dotfiles

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sskim91/dotfiles)

Personal dotfiles for macOS development environment.

## Installation

```bash
git clone https://github.com/sskim91/dotfiles.git ~/.dotfiles
cd ~/.dotfiles && ./install.sh
```

The installer updates a clean `main` checkout with `git pull --ff-only` before
installing. It stops on local changes, another branch, or a failed update; it
does not stash, reset, or merge divergent history.

Existing Neovim data, sessions, and cache are preserved. Replaced configuration
files/directories are backed up, and existing Git settings retain precedence over
the included repository defaults. Configuration links use `XDG_CONFIG_HOME`
(default: `~/.config`). Existing Codex runtime configuration is kept.

Required-step failures stop installation. Optional-step failures are listed at
the end with exit code `2` (partial completion); a fully completed run exits `0`.

Installer regression tests run in temporary directories without installing apps:

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
```

## Structure

- **zsh/** - Aliases, functions, PATH/env vars
- **git/** - Git config with conditional identity switching
- **.config/** - Neovim (LazyVim), Ghostty, Kitty, Karabiner, Zed
- **.claude/** - Hooks, skills, agents, rules
- **.gemini/** - Gemini CLI and Antigravity CLI config
- **Brewfile** - Required Homebrew CLI packages
- **Brewfile.cask** - Optional Homebrew GUI applications

## Key Aliases

```bash
vim → nvim    cat → bat    ls → eza    top → htop    df → duf
```

## AI CLI Wrappers

| Function | Tool | Flags |
|----------|------|-------|
| `ccv` | Claude Code | `-y` `-d` `-r` `-ry` `-rd` |
| `cco` | Claude + Ollama | `-y` `-r` `-ry` `-m <model>` |
| `agy` | Antigravity CLI | `-y` `-s` `-r` `-ry` |
| `gem` | Antigravity CLI if installed, Gemini CLI fallback | `-y` `-r` `-ry` |
| `cdx` | Codex CLI | `-y` `-r` `-ra` `-rl` `-ro` |

## License

MIT
