#!/bin/bash

export DOTFILES=$HOME/.dotfiles

#-------------------------------------------------------------------------------
# Update dotfiles itself
#-------------------------------------------------------------------------------
if [ -d "$DOTFILES/.git" ]; then
  git --work-tree="$DOTFILES" --git-dir="$DOTFILES/.git" pull origin main
fi

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------
link_file() {
    local src="$1" dst="$2"
    if [ -e "$src" ]; then
        ln -nfs "$src" "$dst"
        echo "  ✓ $(basename "$dst")"
    else
        echo "  ⚠️  $(basename "$src") not found, skipping..."
    fi
}

#-------------------------------------------------------------------------------
# Check for Homebrew and install if we don't have it
#-------------------------------------------------------------------------------
if test ! $(which brew); then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for this session (Apple Silicon vs Intel)
    if [[ $(uname -m) == 'arm64' ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

brew bundle

#-------------------------------------------------------------------------------
# Install global Git configuration
#-------------------------------------------------------------------------------
echo "Linking Git configuration..."
for f in .gitconfig .gitconfig_personal .gitconfig_company .gitignore_global; do
    link_file "$DOTFILES/git/$f" "$HOME/$f"
done
git config --global core.excludesfile "$HOME/.gitignore_global"
git config --global core.editor "nvim"

#-------------------------------------------------------------------------------
# Tmux Plugin Manager
#-------------------------------------------------------------------------------
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
    git clone https://github.com/tmux-plugins/tpm $HOME/.tmux/plugins/tpm
fi

#-------------------------------------------------------------------------------
# Install Oh-my-zsh (non-interactive mode)
#-------------------------------------------------------------------------------
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    RUNZSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# Set ZSH variables for current session
export ZSH="$HOME/.oh-my-zsh"
export ZSH_CUSTOM="$ZSH/custom"

#-------------------------------------------------------------------------------
# Install Dracula theme
#-------------------------------------------------------------------------------
if [ ! -f "$ZSH/themes/dracula.zsh-theme" ]; then
    git clone https://github.com/dracula/zsh.git /tmp/zsh-dracula
    mkdir -p $ZSH/themes/lib
    cp /tmp/zsh-dracula/dracula.zsh-theme $ZSH/themes/
    cp /tmp/zsh-dracula/lib/async.zsh $ZSH/themes/lib/
    rm -rf /tmp/zsh-dracula
fi

#-------------------------------------------------------------------------------
# Install ZSH plugins
#-------------------------------------------------------------------------------
[ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ] && \
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting

[ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ] && \
    git clone https://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions

[ ! -d "$ZSH_CUSTOM/plugins/zsh-completions" ] && \
    git clone https://github.com/zsh-users/zsh-completions $ZSH_CUSTOM/plugins/zsh-completions

[ ! -d "$ZSH_CUSTOM/plugins/alias-tips" ] && \
    git clone https://github.com/djui/alias-tips.git $ZSH_CUSTOM/plugins/alias-tips

[ ! -d "$ZSH_CUSTOM/plugins/you-should-use" ] && \
    git clone https://github.com/MichaelAquilina/zsh-you-should-use.git $ZSH_CUSTOM/plugins/you-should-use

#-------------------------------------------------------------------------------
# Install fzf-git.sh (required by .zshrc)
#-------------------------------------------------------------------------------
[ ! -d "$HOME/fzf-git.sh" ] && \
    git clone https://github.com/junegunn/fzf-git.sh.git $HOME/fzf-git.sh

#-------------------------------------------------------------------------------
# Link home dotfiles
#-------------------------------------------------------------------------------
echo "Linking home dotfiles..."
for f in .zshrc .zprofile .tmux.conf .vimrc; do
    link_file "$DOTFILES/$f" "$HOME/$f"
done

#-------------------------------------------------------------------------------
# Link .config directories
#-------------------------------------------------------------------------------
echo "Linking .config directories..."
mkdir -p "${XDG_CONFIG_HOME:=$HOME/.config}"
for dir in nvim ghostty kitty yazi; do
    rm -rf "$HOME/.config/$dir" 2>/dev/null
    ln -nfs "$DOTFILES/.config/$dir" "$HOME/.config/$dir"
    echo "  ✓ .config/$dir"
done

#-------------------------------------------------------------------------------
# Neovim / LazyVim setup
#-------------------------------------------------------------------------------
echo "Setting up Neovim with LazyVim..."
if [ -d "$HOME/.local/share/nvim" ] && [ ! -f "$HOME/.local/share/nvim/.lazyvim-installed" ]; then
    echo "Cleaning up old Neovim data..."
    rm -rf "$HOME/.local/share/nvim"
    rm -rf "$HOME/.local/state/nvim"
    rm -rf "$HOME/.cache/nvim"
fi
if command -v nvim &> /dev/null; then
    echo "Installing LazyVim plugins..."
    nvim --headless "+Lazy! sync" +qa 2>/dev/null || true
    mkdir -p "$HOME/.local/share/nvim"
    touch "$HOME/.local/share/nvim/.lazyvim-installed"
    echo "  ✓ LazyVim plugins installed"
fi

#-------------------------------------------------------------------------------
# Install Node.js LTS using mise
#-------------------------------------------------------------------------------
if ! mise which node &>/dev/null; then
    echo "Installing Node.js LTS via mise..."
    mise install node@lts
    mise use -g node@lts
    eval "$(mise activate bash)"
fi

#-------------------------------------------------------------------------------
# Install Python 3.12 using mise
#-------------------------------------------------------------------------------
if test ! $(mise which python 2>/dev/null); then
    echo "Installing Python 3.12 via mise..."
    mise install python@3.12
    mise use -g python@3.12
    eval "$(mise activate bash)"
fi

#-------------------------------------------------------------------------------
# Install Python tools: uv and Poetry
#-------------------------------------------------------------------------------
echo "Setting up Python package managers..."

if test ! $(which uv); then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "  ✓ uv installed"
else
    echo "  ✓ uv already installed"
fi

if test ! $(which poetry); then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | sed 's/symlinks=False/symlinks=True/' | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "  ✓ Poetry installed"
else
    echo "  ✓ Poetry already installed"
fi

uv pip install --system youtube-transcript-api 2>/dev/null && echo "  ✓ youtube-transcript-api installed"
uv pip install --system detect-secrets 2>/dev/null && echo "  ✓ detect-secrets installed"

#-------------------------------------------------------------------------------
# Install LSP server binaries (npm-based)
#-------------------------------------------------------------------------------
echo "Setting up LSP servers..."
npm install -g pyright 2>/dev/null && echo "  ✓ pyright"
npm install -g typescript-language-server typescript 2>/dev/null && echo "  ✓ typescript-language-server"

#-------------------------------------------------------------------------------
# Install Claude Code (native binary)
#-------------------------------------------------------------------------------
echo "Setting up Claude Code..."
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash
    echo "  ✓ Claude Code installed"
else
    echo "  ✓ Claude Code already installed ($(claude --version 2>/dev/null))"
fi

#-------------------------------------------------------------------------------
# Link Claude Code configuration
#-------------------------------------------------------------------------------
echo "Setting up Claude Code configuration..."
mkdir -p "$HOME/.claude"
for dir in agents hooks output-styles skills rules; do
    link_file "$DOTFILES/.claude/$dir" "$HOME/.claude/$dir"
done
for f in statusline.sh settings.json CLAUDE.md; do
    link_file "$DOTFILES/.claude/$f" "$HOME/.claude/$f"
done

#-------------------------------------------------------------------------------
# Register Claude Code MCP servers (user scope)
#-------------------------------------------------------------------------------
"$DOTFILES/.claude/setup-mcp.sh"

#-------------------------------------------------------------------------------
# Link Gemini configuration
#-------------------------------------------------------------------------------
echo "Setting up Gemini configuration..."
mkdir -p "$HOME/.gemini"
link_file "$DOTFILES/.gemini/settings.json" "$HOME/.gemini/settings.json"
link_file "$DOTFILES/.gemini/policies" "$HOME/.gemini/policies"

#-------------------------------------------------------------------------------
# Link Codex CLI configuration
#-------------------------------------------------------------------------------
echo "Setting up Codex CLI configuration..."
mkdir -p "$HOME/.codex"
link_file "$DOTFILES/.codex/config.toml.example" "$HOME/.codex/config.toml.example"

#-------------------------------------------------------------------------------
# Link Karabiner-Elements configuration
#-------------------------------------------------------------------------------
echo "Setting up Karabiner-Elements..."
mkdir -p "$HOME/.config/karabiner/assets/complex_modifications"
link_file "$DOTFILES/.config/karabiner/my_custom_key.json" \
    "$HOME/.config/karabiner/assets/complex_modifications/my_custom_key.json"

#-------------------------------------------------------------------------------
# Link .config files
#-------------------------------------------------------------------------------
echo "Linking .config files..."
for file in ruff/ruff.toml zed/settings.json; do
    mkdir -p "$HOME/.config/$(dirname "$file")"
    link_file "$DOTFILES/.config/$file" "$HOME/.config/$file"
done

#-------------------------------------------------------------------------------
# Yazi plugins and flavors
#-------------------------------------------------------------------------------
if command -v ya &> /dev/null; then
    ya pkg add yazi-rs/plugins:fzf 2>/dev/null
    ya pkg add yazi-rs/flavors:catppuccin-mocha 2>/dev/null
    ya pkg add yazi-rs/flavors:catppuccin-latte 2>/dev/null
    echo "  ✓ Yazi plugins and flavors installed"
fi

#-------------------------------------------------------------------------------
# Install Serena MCP (AI semantic code analysis)
#-------------------------------------------------------------------------------
echo "Setting up Serena MCP..."
mkdir -p $HOME/dev

if [ ! -d "$HOME/dev/serena" ]; then
    echo "Cloning Serena repository..."
    git clone https://github.com/oraios/serena.git $HOME/dev/serena
    echo "  ✓ Serena cloned"
else
    echo "  ✓ Serena already installed"
fi

#-------------------------------------------------------------------------------
# Setup pre-commit hooks
#-------------------------------------------------------------------------------
echo "Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    (cd "$DOTFILES" && pre-commit install)
    echo "  ✓ pre-commit hooks installed"
else
    echo "  ⚠️  pre-commit not found, skipping..."
fi

#-------------------------------------------------------------------------------
# Make ZSH the default shell environment
#-------------------------------------------------------------------------------
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "Changing default shell to zsh..."
    chsh -s $(which zsh)
fi

echo "✅ Dotfiles installation completed!"
echo "Please restart your terminal or run: source ~/.zshrc"
