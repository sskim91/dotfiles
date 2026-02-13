#!/bin/bash

export DOTFILES=$HOME/.dotfiles

#-------------------------------------------------------------------------------
# Update dotfiles itself
#-------------------------------------------------------------------------------
if [ -d "$DOTFILES/.git" ]; then
  git --work-tree="$DOTFILES" --git-dir="$DOTFILES/.git" pull origin main
fi

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
ln -nfs $DOTFILES/git/.gitconfig $HOME/.gitconfig
ln -nfs $DOTFILES/git/.gitconfig_personal $HOME/.gitconfig_personal
ln -nfs $DOTFILES/git/.gitconfig_company $HOME/.gitconfig_company
ln -nfs $DOTFILES/git/.gitignore_global $HOME/.gitignore_global
git config --global core.excludesfile $HOME/.gitignore_global
git config --global core.editor "nvim"

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
# Link .zshrc configuration
#-------------------------------------------------------------------------------
ln -nfs $DOTFILES/.zshrc $HOME/.zshrc

#-------------------------------------------------------------------------------
# Vim setting (basic vim with .vimrc)
#-------------------------------------------------------------------------------
echo "Setting up Vim..."
ln -nfs $DOTFILES/.vimrc $HOME/.vimrc
echo "✓ Vim setup complete"

#-------------------------------------------------------------------------------
# Neovim setting (LazyVim with Lua configuration)
#-------------------------------------------------------------------------------
echo "Setting up Neovim with LazyVim..."

# Clean up old Neovim data for fresh LazyVim install
if [ -d "$HOME/.local/share/nvim" ] && [ ! -f "$HOME/.local/share/nvim/.lazyvim-installed" ]; then
    echo "Cleaning up old Neovim data..."
    rm -rf "$HOME/.local/share/nvim"
    rm -rf "$HOME/.local/state/nvim"
    rm -rf "$HOME/.cache/nvim"
fi

# Link Neovim configuration directory
mkdir -p ${XDG_CONFIG_HOME:=$HOME/.config}
rm -rf $HOME/.config/nvim 2>/dev/null
ln -nfs $DOTFILES/.config/nvim $HOME/.config/nvim

# Install LazyVim plugins (headless mode)
if command -v nvim &> /dev/null; then
    echo "Installing LazyVim plugins (this may take a moment)..."
    nvim --headless "+Lazy! sync" +qa 2>/dev/null || true
    # Mark LazyVim as installed
    mkdir -p "$HOME/.local/share/nvim"
    touch "$HOME/.local/share/nvim/.lazyvim-installed"
    echo "✓ LazyVim plugins installed"
fi

echo "✓ Neovim/LazyVim setup complete"

#-------------------------------------------------------------------------------
# Install Node.js LTS using mise
#-------------------------------------------------------------------------------
if ! mise which node &>/dev/null; then
    echo "Installing Node.js LTS via mise..."
    mise install node@lts
    mise use -g node@lts
    # Activate mise for current session to make node available immediately
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

# Install uv (fast Python package installer)
if test ! $(which uv); then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Activate uv for current session
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv already installed"
fi

# Install Poetry with symlinks=True for mise compatibility
if test ! $(which poetry); then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | sed 's/symlinks=False/symlinks=True/' | python3 -
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ Poetry installed"
else
    echo "✓ Poetry already installed"
fi

# Install Python packages for dotfiles scripts (using uv installed above)
uv pip install --system youtube-transcript-api 2>/dev/null && echo "✓ youtube-transcript-api installed"
uv pip install --system detect-secrets 2>/dev/null && echo "✓ detect-secrets installed"

#-------------------------------------------------------------------------------
# Install LSP server binaries (npm-based)
# brew-based LSP servers (jdtls, kotlin-language-server, lua-language-server)
# are installed via Brewfile
#-------------------------------------------------------------------------------
echo "Setting up LSP servers..."
MISE_NPM="$HOME/.local/share/mise/shims/npm"
$MISE_NPM install -g pyright 2>/dev/null && echo "✓ pyright installed"
$MISE_NPM install -g typescript-language-server typescript 2>/dev/null && echo "✓ typescript-language-server installed"

#-------------------------------------------------------------------------------
# Link Claude customizable directories and files individually
#-------------------------------------------------------------------------------
echo "Setting up Claude Code configuration..."
mkdir -p $HOME/.claude

# Link customizable directories
for dir in agents hooks output-styles skills rules; do
    if [ -d "$DOTFILES/.claude/$dir" ]; then
        ln -nfs "$DOTFILES/.claude/$dir" "$HOME/.claude/$dir"
        echo "✓ Linked $dir"
    else
        echo "⚠️  $dir directory not found, skipping..."
    fi
done

# Link customizable files
if [ -f "$DOTFILES/.claude/statusline.sh" ]; then
    ln -nfs "$DOTFILES/.claude/statusline.sh" "$HOME/.claude/statusline.sh"
    echo "✓ Linked statusline.sh"
fi

if [ -f "$DOTFILES/.claude/settings.json" ]; then
    ln -nfs "$DOTFILES/.claude/settings.json" "$HOME/.claude/settings.json"
    echo "✓ Linked settings.json"
fi

# Link global CLAUDE.md
if [ -f "$DOTFILES/.claude/CLAUDE.md" ]; then
    ln -nfs "$DOTFILES/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
    echo "✓ Linked global CLAUDE.md"
fi

echo "✅ Claude Code customizable directories and files linked"

#-------------------------------------------------------------------------------
# Register Claude Code MCP servers (user scope)
#-------------------------------------------------------------------------------
"$DOTFILES/.claude/setup-mcp.sh"

#-------------------------------------------------------------------------------
# Link Gemini configuration
#-------------------------------------------------------------------------------
echo "Setting up Gemini configuration..."
mkdir -p $HOME/.gemini

if [ -f "$DOTFILES/.gemini/settings.json" ]; then
    ln -nfs "$DOTFILES/.gemini/settings.json" "$HOME/.gemini/settings.json"
    echo "✓ Linked Gemini settings.json"
else
    echo "⚠️  Gemini settings.json not found, skipping..."
fi

echo "✅ Gemini configuration linked"

#-------------------------------------------------------------------------------
# Link Codex CLI configuration example
#-------------------------------------------------------------------------------
echo "Setting up Codex CLI configuration..."
mkdir -p $HOME/.codex

if [ -f "$DOTFILES/.codex/config.toml.example" ]; then
    ln -nfs "$DOTFILES/.codex/config.toml.example" "$HOME/.codex/config.toml.example"
    echo "✓ Linked Codex config.toml.example"
else
    echo "⚠️  Codex config.toml.example not found, skipping..."
fi

echo "✅ Codex CLI configuration linked"

#-------------------------------------------------------------------------------
# Link Karabiner-Elements configuration
#-------------------------------------------------------------------------------
echo "Setting up Karabiner-Elements configuration..."
mkdir -p $HOME/.config/karabiner/assets/complex_modifications

if [ -f "$DOTFILES/.config/karabiner/my_custom_key.json" ]; then
    ln -nfs "$DOTFILES/.config/karabiner/my_custom_key.json" "$HOME/.config/karabiner/assets/complex_modifications/my_custom_key.json"
    echo "✓ Linked Karabiner custom key configuration"
else
    echo "⚠️  .config/karabiner/my_custom_key.json not found, skipping..."
fi

echo "✅ Karabiner-Elements configuration linked"

#-------------------------------------------------------------------------------
# Link Ghostty configuration
#-------------------------------------------------------------------------------
echo "Setting up Ghostty configuration..."
mkdir -p $HOME/.config

if [ -d "$DOTFILES/.config/ghostty" ]; then
    rm -rf $HOME/.config/ghostty 2>/dev/null
    ln -nfs "$DOTFILES/.config/ghostty" "$HOME/.config/ghostty"
    echo "✓ Linked Ghostty config"
else
    echo "⚠️  .config/ghostty not found, skipping..."
fi

echo "✅ Ghostty configuration linked"

#-------------------------------------------------------------------------------
# Link Kitty configuration
#-------------------------------------------------------------------------------
echo "Setting up Kitty configuration..."

if [ -d "$DOTFILES/.config/kitty" ]; then
    rm -rf $HOME/.config/kitty 2>/dev/null
    ln -nfs "$DOTFILES/.config/kitty" "$HOME/.config/kitty"
    echo "✓ Linked Kitty config"
else
    echo "⚠️  .config/kitty not found, skipping..."
fi

echo "✅ Kitty configuration linked"

#-------------------------------------------------------------------------------
# Link Yazi configuration & install runtime packages
#-------------------------------------------------------------------------------
echo "Setting up Yazi configuration..."

if [ -d "$DOTFILES/.config/yazi" ]; then
    rm -rf $HOME/.config/yazi 2>/dev/null
    ln -nfs "$DOTFILES/.config/yazi" "$HOME/.config/yazi"
    echo "✓ Linked Yazi config"
else
    echo "⚠️  .config/yazi not found, skipping..."
fi

# Install yazi plugins and flavors (not tracked in git)
if command -v ya &> /dev/null; then
    ya pkg add yazi-rs/plugins:fzf 2>/dev/null
    ya pkg add yazi-rs/flavors:catppuccin-mocha 2>/dev/null
    ya pkg add yazi-rs/flavors:catppuccin-latte 2>/dev/null
    echo "✓ Yazi plugins and flavors installed"
fi

echo "✅ Yazi configuration linked"

#-------------------------------------------------------------------------------
# Link Zed configuration
#-------------------------------------------------------------------------------
echo "Setting up Zed configuration..."
mkdir -p $HOME/.config/zed

if [ -f "$DOTFILES/.config/zed/settings.json" ]; then
    ln -nfs "$DOTFILES/.config/zed/settings.json" "$HOME/.config/zed/settings.json"
    echo "✓ Linked Zed settings.json"
else
    echo "⚠️  .config/zed/settings.json not found, skipping..."
fi

echo "✅ Zed configuration linked"

#-------------------------------------------------------------------------------
# Install Serena MCP (AI semantic code analysis)
#-------------------------------------------------------------------------------
echo "Setting up Serena MCP..."

# Create dev directory if not exists
mkdir -p $HOME/dev

# Clone Serena repository if not exists
if [ ! -d "$HOME/dev/serena" ]; then
    echo "Cloning Serena repository..."
    git clone https://github.com/oraios/serena.git $HOME/dev/serena
    echo "✓ Serena cloned"
else
    echo "✓ Serena already installed"
fi

# Serena will create its own config at ~/.serena/serena_config.yml on first run
echo "✅ Serena MCP setup complete"
echo "   Run 'add-serena' in your project directory to add Serena MCP"

#-------------------------------------------------------------------------------
# Setup pre-commit hooks
#-------------------------------------------------------------------------------
echo "Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    (cd "$DOTFILES" && pre-commit install)
    echo "✓ pre-commit hooks installed"
else
    echo "⚠️  pre-commit not found, skipping..."
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
