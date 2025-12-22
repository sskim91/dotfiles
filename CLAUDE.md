# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal dotfiles repository managing macOS development environment. Centralized at `~/.dotfiles` with automated installation and configuration management.

## Installation and Setup

### Initial Setup
```bash
# Clone and install everything
./install.sh
```

The install script performs:
1. Updates dotfiles from Git repository
2. Installs Homebrew (Apple Silicon/Intel auto-detection)
3. Installs packages via `brew bundle` (from Brewfile) - includes Claude Code CLI and Gemini CLI
4. Sets up Git config with conditional includes
5. Installs Oh-My-Zsh with Dracula theme
6. Installs ZSH plugins (syntax highlighting, autosuggestions, completions, alias-tips, you-should-use)
7. Links configuration files (.zshrc, .vimrc, nvim/)
8. Sets up Neovim with LazyVim (Lua-based modern configuration)
9. Installs Node.js LTS (v22) via mise
10. Links Claude configuration directory to ~/.claude
11. Links Gemini CLI configuration directory to ~/.gemini

### Update Commands
```bash
# Update all Homebrew packages
update                    # Alias for: brew update && brew upgrade && brew cleanup

# Reload shell configuration after changes
rr                        # Alias for: source ~/.zshrc
source ~/.zshrc

# Add Serena MCP to current project
add-serena               # Runs add-serena-uvx.sh script
```

## Key Configuration Architecture

### Git Conditional Configuration
The repository uses Git's `includeIf` directive for automatic identity switching:
- **Personal projects** (`~/dev/`): Uses `.gitconfig_personal`
- **Company projects** (`~/company-src/`): Uses `.gitconfig_company`
- **Base config**: `.gitconfig` with delta pager and Neovim editor

This ensures correct author information without manual switching.

### Shell Configuration Structure
Modular ZSH configuration loaded from `$DOTFILES/zsh/`:
- **`aliases.zsh`**: Command shortcuts and enhanced tool aliases
- **`functions.zsh`**: Custom functions (mkd, killport, findpid, extract, fzf integrations)
- **`path.zsh`**: PATH configuration and tool environment variables

All loaded via: `source <(cat $DOTFILES/zsh/*zsh)`

### Tool Version Management
Uses **mise** (modern asdf replacement) for version management:
- Faster and more modern than asdf
- Activated via: `eval "$(mise activate zsh)"`
- Node.js LTS 22 installed globally by default

### Neovim Configuration (LazyVim)
Modern Lua-based Neovim setup using LazyVim distribution:

**Directory Structure**:
```
config/nvim/
├── init.lua              # Bootstrap lazy.nvim and load config
├── lazyvim.json          # LazyVim extras configuration
└── lua/
    ├── config/
    │   ├── options.lua   # Editor options (migrated from .vimrc)
    │   ├── keymaps.lua   # Custom key mappings
    │   └── autocmds.lua  # Auto commands
    └── plugins/
        ├── colorscheme.lua  # Theme configuration (catppuccin)
        └── editor.lua       # Editor enhancements
```

**Enabled Language Support** (via LazyVim extras):
- Python (pyright, ruff)
- TypeScript/JavaScript (tsserver, eslint)
- Java (jdtls)
- JSON, Markdown

**Key Features**:
- **lazy.nvim**: Fast plugin manager with lazy loading
- **Catppuccin**: Default colorscheme (mocha flavor)
- **Telescope**: Fuzzy finder (`<leader>ff`, `<leader>fg`)
- **Neo-tree**: File explorer (`<leader>e`)
- **LSP**: Built-in language server support
- **Treesitter**: Advanced syntax highlighting

**Common Commands**:
```bash
nvim                      # Start Neovim (auto-syncs plugins)
:Lazy                     # Plugin manager UI
:Mason                    # LSP/formatter installer
:LazyExtras              # Enable/disable language extras
```

## Claude Code Integration

### Session Hooks
- **temporal-context.sh**: Injects current date/time at session start
  - Provides context: `Current time and date: HH:MM:SS YYYY-MM-DD`
  - Configured via `SessionStart` hook in settings.json

### Hook System Architecture
Located in `claude/hooks/` with dispatcher pattern:

1. **file-dispatcher.sh**: Main entry point that routes to language-specific handlers
   - Routes by file extension: `.py`, `.java`, `.ts/.tsx`, `.js/.jsx`, `.go`, `.rs`, `.cpp`
   - Supports three hook types: `format`, `check`, `review`

2. **Language-specific hooks**: `{language}-{type}.sh`
   - **format**: Auto-format code (runs pre/post Write|Edit|MultiEdit)
   - **check**: Validate code quality (runs pre/post Write|Edit|MultiEdit)
   - **review**: Post-edit code review (runs post Write|Edit|MultiEdit only)

3. **Configured timeouts**: 180s (3 minutes) for all hook types

4. **Supported languages**:
   - Python: ruff, black, isort
   - JavaScript: prettier, eslint
   - TypeScript: prettier, tsc
   - Java: google-java-format

5. **TIL Review Hook** (`til-review.sh`):
   - Reviews markdown files in `~/dev/TIL` directory using Gemini
   - Requires `ENABLE_GEMINI_REVIEW=1` environment variable
   - Uses gemini-2.5-pro model for document review
   - Provides feedback on technical accuracy, mermaid syntax, and content quality

### Output Styles
Located in `claude/output-styles/`:
- **pragmatic-test-driven-developer.md**: TDD-focused output style

### Custom Slash Commands
Located in `claude/commands/`:
- **`git:commit`**: Structured commit workflow with safety checks
- **`git:push`**: Safe push with validation
- **`git:commit-and-push`**: Combined workflow

### Custom Agents
The `claude/agents/` directory contains custom agent configurations for specialized tasks.

### Status Line
Custom status line via `claude/statusline.sh` for enhanced CLI experience.

### Settings Configuration
`claude/settings.json` controls:
- Hook configurations (SessionStart, PreToolUse, PostToolUse)
- Status line command
- `alwaysThinkingEnabled: true` for extended reasoning

### Environment Variables
```bash
ENABLE_GEMINI_REVIEW=1      # Enable Gemini TIL review hook
ENABLE_BACKGROUND_TASKS=1   # Enable background task execution
```

## Development Environment

### Enhanced CLI Tools
The dotfiles replace standard tools with modern alternatives:
- `cat` → `bat` (syntax highlighting)
- `ls` → `eza` (icons, git status, tree view)
- `top` → `htop` (better process monitor)
- `vim` → `nvim` (Neovim)
- `df` → `duf` (disk usage)
- Git pager → `delta` (enhanced diffs with side-by-side view)

### Key Aliases
```bash
# Navigation
dot         # cd ~/.dotfiles
dev         # cd ~/dev
desk        # cd ~/Desktop
dl          # cd ~/Downloads

# Enhanced listings
ll          # eza with detailed list + git status
la          # eza with hidden files
lt          # eza tree view (2 levels)

# Tools
vim         # Neovim
cat         # bat with syntax highlighting
top         # htop

# Homebrew
update      # Update all brew packages
services    # Manage brew services
```

### Useful Functions
```bash
mkd <dir>             # Create directory and cd into it
killport <port>       # Kill process on specified port
findpid <port>        # Find PID using specified port
extract <file>        # Extract various archive formats
myip                  # Get public IP address
tcp                   # List all TCP LISTEN ports
battail <file>        # tail -f with bat syntax highlighting
fh                    # Search command history with fzf
fd                    # cd to directory with fzf
fzfv                  # Preview files with fzf

# 1Password integration
load-token            # Load GitHub token from 1Password
token-status          # Check GitHub token status

# Claude wrapper with optimization flags
ccv                   # Claude with background tasks enabled
ccv -y                # Skip permissions prompts
ccv -r                # Resume last session
ccv -ry               # Resume with skip permissions
```

### Oh-My-Zsh Plugins
Carefully selected for development productivity:
- `git`: Git aliases and status
- `zsh-syntax-highlighting`: Command syntax highlighting
- `zsh-autosuggestions`: Command suggestions from history
- `zsh-completions`: Additional completions
- `alias-tips`: Remind about existing aliases
- `you-should-use`: Suggest aliases for commands
- `fzf`: Fuzzy finder integration
- `docker`, `docker-compose`, `kubectl`: Container tools
- `poetry`: Python package management

### FZF Configuration
Advanced fuzzy finding with fd integration:
- Default command excludes `.git`, `node_modules`, `bower_components`
- File preview with bat
- Directory preview with eza tree view
- Custom completion for different commands (cd, ssh, export)

## Working with This Repository

### Testing Configuration Changes
```bash
# After editing .zshrc or zsh/*.zsh
source ~/.zshrc        # or use 'rr' alias

# After editing .gitconfig
# Changes apply automatically on next git command

# After editing Neovim config (config/nvim/lua/*)
nvim                        # LazyVim auto-syncs plugins on startup
# Or manually: nvim --headless "+Lazy! sync" +qa
```

### Hook System Development
When modifying Claude hooks:
- Hooks receive JSON input via stdin
- Extract file paths using jq: `jq -r '.tool_input.file_path'`
- Exit 0 for success, non-zero for blocking
- Timeout enforcement: format/check (30s), review (20s)
- Language detection based on file extension in dispatcher

### Conditional Git Configuration Pattern
When adding new directory-based Git configs:
```bash
# In .gitconfig
[includeIf "gitdir:~/path/to/dir/"]
    path = .gitconfig_custom_name
```

### Adding New Aliases
Add to `zsh/aliases.zsh` following existing patterns:
- Group related aliases together
- Use descriptive comments in Korean or English
- Prefer safety flags (rm -i, cp -i, mv -i)
- Chain commands with && for dependent operations

### Adding New Functions
Add to `zsh/functions.zsh`:
- Include usage help when parameters required
- Use colored output for visibility: `echo -e "\033[0;33m${TEXT}\033[0m"`
- Follow existing naming conventions
