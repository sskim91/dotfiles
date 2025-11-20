# dotfiles

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sskim91/dotfiles)

Personal dotfiles for macOS development environment.

## Contents

- **zsh/** - Zsh configuration and custom functions
- **Brewfile** - Homebrew packages and applications
- **git/** - Git configuration files
- **claude/** - Claude Code configuration
- **gemini/** - Gemini CLI configuration
- **init.vim** - Neovim configuration

## Installation

```bash
# Clone repository
git clone https://github.com/sskim91/dotfiles.git ~/.dotfiles

# Run installation script
cd ~/.dotfiles
chmod +x install.sh
./install.sh
```

The install script will:
- Install Homebrew (if not present)
- Install all packages from Brewfile
- Set up Git configuration
- Install Oh-my-zsh with Dracula theme
- Install ZSH plugins
- Configure Vim/Neovim
- Install Node.js LTS via mise
- Install Python tools (uv, Poetry)
- Install Claude Code & Gemini CLI
- Link all configuration files

## Custom Functions

The `zsh/functions.zsh` includes useful shell functions:
- `mkd` - Create and enter directory
- `killport` - Kill process by port
- `findpid` - Find PID by port
- `extract` - Extract various archive formats
- `ccv` - Claude Code wrapper with optimized settings
- And more...

## License

MIT
