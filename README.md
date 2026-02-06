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
- **.claude/** - Hooks, skills (17), agents (9), rules
- **.gemini/** - Gemini CLI config
- **Brewfile** - Homebrew packages

## Key Aliases

```bash
vim → nvim    cat → bat    ls → eza    top → htop    df → duf
```

## AI CLI Wrappers

| Function | Tool | Flags |
|----------|------|-------|
| `ccv` | Claude Code | `-y` `-r` `-ry` |
| `cco` | Claude + Ollama | `-y` `-r` `-m <model>` |
| `gem` | Gemini CLI | `-y` `-r` `-ry` |
| `cdx` | Codex CLI | `update` |

## License

MIT
