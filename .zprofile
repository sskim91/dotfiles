# ~/.zprofile - Login shell initialization
# Sourced once per login session. Interactive config lives in ~/.zshrc.

export DOTFILES="$HOME/.dotfiles"

# Homebrew
[[ -x /opt/homebrew/bin/brew ]] && eval "$(/opt/homebrew/bin/brew shellenv)"

# mise (asdf replacement) - runtime version management
command -v mise &>/dev/null && eval "$(mise activate zsh)"

# Environment variables and PATH (EDITOR, FZF_*, MANPAGER, Claude hooks, etc.)
source "$DOTFILES/zsh/path.zsh"

# LM Studio CLI
export PATH="$PATH:$HOME/.lmstudio/bin"

# Antigravity
export PATH="$HOME/.antigravity/antigravity/bin:$PATH"

# JetBrains Toolbox
export PATH="$PATH:$HOME/Library/Application Support/JetBrains/Toolbox/scripts"

# Obsidian CLI
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
