# dotfiles

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sskim91/dotfiles)

Personal dotfiles for macOS development environment.

## Installation

```bash
git clone https://github.com/sskim91/dotfiles.git ~/.dotfiles
cd ~/.dotfiles && ./install.sh
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
