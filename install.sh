#!/bin/bash

export DOTFILES=$HOME/.dotfiles

#-------------------------------------------------------------------------------
# Update dotfiles itself
#-------------------------------------------------------------------------------
if [ -d "$DOTFILES/.git" ]; then
  git --work-tree="$DOTFILES" --git-dir="$DOTFILES/.git" pull origin master
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
ln -nfs $DOTFILES/.gitconfig $HOME/.gitconfig
git config --global core.excludesfile $DOTFILES/.gitignore_global
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
# Vim setting
#-------------------------------------------------------------------------------
echo "Setting up Vim/Neovim..."

# Install Vundle if not present
[ ! -d "$HOME/.vim/bundle/Vundle.vim" ] && \
    git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

# Detect Homebrew installation path (Apple Silicon vs Intel Mac)
if [ -d "/opt/homebrew" ]; then
    BREW_PREFIX="/opt/homebrew"
elif [ -d "/usr/local/Homebrew" ]; then
    BREW_PREFIX="/usr/local"
else
    BREW_PREFIX=$(brew --prefix 2>/dev/null || echo "/opt/homebrew")
fi

echo "Detected Homebrew prefix: $BREW_PREFIX"

# Update fzf path in init.vim if needed
if [ -f "$DOTFILES/init.vim" ]; then
    FZF_PATH="$BREW_PREFIX/opt/fzf"
    if [ -d "$FZF_PATH" ]; then
        echo "Updating fzf path in init.vim to: $FZF_PATH"
        # Use sed to update fzf path (macOS compatible)
        sed -i.bak "s|set rtp+=.*/opt/fzf|set rtp+=$FZF_PATH|g" "$DOTFILES/init.vim"
        rm -f "$DOTFILES/init.vim.bak"
    fi
fi

# Link vim config
ln -nfs $DOTFILES/.vimrc $HOME/.vimrc

# Neovim configuration
echo "Setting up Neovim configuration..."
mkdir -p ${XDG_CONFIG_HOME:=$HOME/.config}/nvim
ln -nfs $DOTFILES/init.vim $HOME/.config/nvim/init.vim

# Install plugins for both vim and neovim
echo "Installing Vim plugins..."
vim +PluginInstall +qall 2>/dev/null || true

# Install plugins for neovim (if available)
if command -v nvim &> /dev/null; then
    echo "Installing Neovim plugins..."
    nvim +PluginInstall +qall 2>/dev/null || true
fi

echo "✓ Vim/Neovim setup complete"

#-------------------------------------------------------------------------------
# Install Node.js LTS (v22) using mise
#-------------------------------------------------------------------------------
if test ! $(which node); then
    echo "Installing Node.js LTS 22 via mise..."
    mise install node@22
    mise use -g node@22
    # Activate mise for current session to make node available immediately
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

#-------------------------------------------------------------------------------
# Install npm global packages (Claude Code CLI & Gemini CLI)
#-------------------------------------------------------------------------------
echo "Installing npm global packages..."
npm install -g @anthropic-ai/claude-code 2>/dev/null || echo "⚠️  @anthropic-ai/claude-code installation failed"
npm install -g @google/gemini-cli 2>/dev/null || echo "⚠️  @google/gemini-cli installation failed"

#-------------------------------------------------------------------------------
# Link Claude customizable directories and files individually
#-------------------------------------------------------------------------------
echo "Setting up Claude Code configuration..."
mkdir -p $HOME/.claude

# Link customizable directories
for dir in agents commands hooks output-styles skills; do
    if [ -d "$DOTFILES/claude/$dir" ]; then
        ln -nfs "$DOTFILES/claude/$dir" "$HOME/.claude/$dir"
        echo "✓ Linked $dir"
    else
        echo "⚠️  $dir directory not found, skipping..."
    fi
done

# Link customizable files
if [ -f "$DOTFILES/claude/statusline.sh" ]; then
    ln -nfs "$DOTFILES/claude/statusline.sh" "$HOME/.claude/statusline.sh"
    echo "✓ Linked statusline.sh"
fi

if [ -f "$DOTFILES/claude/settings.json" ]; then
    ln -nfs "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"
    echo "✓ Linked settings.json"
fi

echo "✅ Claude Code customizable directories and files linked"

#-------------------------------------------------------------------------------
# Make ZSH the default shell environment
#-------------------------------------------------------------------------------
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "Changing default shell to zsh..."
    chsh -s $(which zsh)
fi

echo "✅ Dotfiles installation completed!"
echo "Please restart your terminal or run: source ~/.zshrc"
