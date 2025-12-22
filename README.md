# dotfiles

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sskim91/dotfiles)

Personal dotfiles for macOS development environment.

## Contents

- **zsh/** - Zsh configuration (aliases, functions, path)
- **git/** - Git configuration with conditional includes
- **config/** - Application configurations
  - **nvim/** - Neovim with LazyVim
  - **ghostty/** - Ghostty terminal
  - **kitty/** - Kitty terminal
  - **karabiner/** - Keyboard customization
- **claude/** - Claude Code configuration
  - **agents/** - 24+ custom agent configurations
  - **skills/** - 14 custom skills for common patterns
  - **hooks/** - File dispatcher & language-specific hooks
  - **commands/** - Custom slash commands (git:commit, git:push)
  - **rules/** - Global rules (Context7, Tavily, npm, python)
- **gemini/** - Gemini CLI configuration
- **Brewfile** - Homebrew packages and applications

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
- Set up Git configuration with conditional includes
- Install Oh-my-zsh with Dracula theme
- Install ZSH plugins (syntax-highlighting, autosuggestions, completions, alias-tips, you-should-use)
- Configure Neovim with LazyVim
- Install Node.js LTS (v22) via mise
- Install Python tools (uv, Poetry)
- Link Claude Code & Gemini CLI configurations
- Link Ghostty, Kitty, Karabiner configurations

## Karabiner-Elements

Caps Lock을 Modifier Key로 활용하는 커스텀 설정 (`my_custom_key.json`)

**Caps Lock + 키 조합:**

| 키 | 동작 |
|---|------|
| `i` | ↑ (위 화살표) |
| `k` | ↓ (아래 화살표) |
| `j` | ← (왼쪽 화살표) |
| `l` | → (오른쪽 화살표) |
| `e` | Page Up |
| `d` | Page Down |
| `r` | Home |
| `f` | End |
| `n` | Backspace |
| `m` | Delete (Forward) |

> Caps Lock만 단독으로 누르면 원래 Caps Lock 기능 동작

## Claude Code Integration

Hook system with file dispatcher pattern for automatic code quality:

| Hook Type | Trigger | Description |
|-----------|---------|-------------|
| check | PostToolUse (Write/Edit) | Validate code quality |
| review | PostToolUse (Write/Edit) | Post-edit code review |

**Supported Languages:** Python (ruff), JavaScript/TypeScript (prettier, eslint), Java (google-java-format)

**Custom Skills (14):** fastapi-templates, javascript-testing-patterns, microservices-patterns, sql-optimization-patterns, rag-implementation, tech-blog-writer, and more.

**Custom Agents (24+):** Categorized by Backend, Frontend, Data/ML, DevOps, Testing, Analysis, Strategy, Documentation.

## Key Aliases

```bash
# Enhanced tools (modern replacements)
vim → nvim    cat → bat    ls → eza    top → htop    df → duf

# Navigation
dot, dev, til, comp, desk, dl

# Listings
ll   # eza with git status
la   # eza with hidden files
lt   # eza tree view (2 levels)
```

## Custom Functions

The `zsh/functions.zsh` includes useful shell functions:
- `mkd` - Create and enter directory
- `killport` - Kill process by port
- `findpid` - Find PID by port
- `extract` - Extract various archive formats
- `ccv` - Claude Code wrapper with optimization env vars
- `cdx` - Codex CLI wrapper
- `fh` / `fd` / `fzfv` - FZF integrations
- `catcp` - Copy file content to clipboard
- `battail` - tail -f with bat syntax highlighting

## License

MIT
