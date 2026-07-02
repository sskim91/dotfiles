#!/bin/bash

export DOTFILES=$HOME/.dotfiles

#-------------------------------------------------------------------------------
# Bootstrap: Xcode Command Line Tools
# Everything below (git, brew, compilers) depends on CLT. On a fresh macOS,
# /usr/bin/git is just a stub that triggers this install dialog anyway — we
# do it here explicitly and wait, so the rest of the script can run unattended.
#-------------------------------------------------------------------------------
if ! xcode-select -p &>/dev/null; then
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install 2>/dev/null || true
    echo "Waiting for CLT installation to finish (typically 10-15 minutes)..."
    until xcode-select -p &>/dev/null; do
        sleep 10
    done
    echo "  ✓ Xcode Command Line Tools installed"
fi

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
    if [ -e "$src" ] || [ -L "$src" ]; then
        if [ -e "$dst" ] && [ ! -L "$dst" ]; then
            local backup="${dst}.backup.$(date +%Y%m%d%H%M%S)"
            mv "$dst" "$backup"
            echo "  ↳ backed up existing $(basename "$dst") to $(basename "$backup")"
        fi
        ln -nfs "$src" "$dst"
        echo "  ✓ $(basename "$dst")"
    else
        echo "  ⚠️  $(basename "$src") not found, skipping..."
    fi
}

cleanup_antigravity_installer_path_edits() {
    # The official installer appends a PATH block to shell profiles. ~/.local/bin
    # is already managed in zsh/path.zsh, so keep bootstrap idempotent.
    for profile in "$DOTFILES/.zshrc" "$DOTFILES/.zprofile" "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.profile"; do
        [ -f "$profile" ] || continue
        perl -0pi -e 's/\n{0,2}# Added by Antigravity CLI installer\nexport PATH="[^"\n]*\/\.local\/bin:\$PATH"\n//g' "$profile"
    done
}

#-------------------------------------------------------------------------------
# Check for Homebrew and install if we don't have it
#-------------------------------------------------------------------------------
if ! command -v brew &>/dev/null; then
    # NONINTERACTIVE=1 skips "Press RETURN to continue" prompts but cannot
    # prompt for sudo password — pre-warm the sudo timestamp cache so brew's
    # /usr/bin/sudo calls (mkdir/chown under /opt/homebrew) succeed unattended.
    # CLT is guaranteed by the bootstrap block above.
    sudo -v
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Sanity check: abort early if brew install silently failed (sudo timeout,
# network error). Otherwise every downstream step cascades into failure.
if ! command -v brew &>/dev/null; then
    echo "❌ Homebrew installation failed or not in PATH. Aborting."
    echo "   Try: eval \"\$(/opt/homebrew/bin/brew shellenv)\" and re-run."
    exit 1
fi

echo "Installing Homebrew CLI tools..."
if ! brew bundle --file="$DOTFILES/Brewfile"; then
    echo "❌ Homebrew CLI bundle failed. Aborting."
    echo "   Re-run after fixing the failed formula: brew bundle --file=\"$DOTFILES/Brewfile\""
    exit 1
fi

if [ -f "$DOTFILES/Brewfile.cask" ]; then
    echo "Installing Homebrew GUI apps..."
    if ! brew bundle --file="$DOTFILES/Brewfile.cask"; then
        echo "⚠️  Some Homebrew casks failed to install. Continuing bootstrap."
        echo "   Re-run later: brew bundle --file=\"$DOTFILES/Brewfile.cask\""
    fi
fi

#-------------------------------------------------------------------------------
# Install Antigravity CLI
#-------------------------------------------------------------------------------
echo "Setting up Antigravity CLI..."
export PATH="$HOME/.local/bin:$PATH"
cleanup_antigravity_installer_path_edits
if ! command -v agy &>/dev/null; then
    curl -fsSL https://antigravity.google/cli/install.sh | bash
    cleanup_antigravity_installer_path_edits
    echo "  ✓ Antigravity CLI installed"
else
    echo "  ✓ Antigravity CLI already installed ($(agy --version 2>/dev/null))"
fi

#-------------------------------------------------------------------------------
# Install global Git configuration
#-------------------------------------------------------------------------------
echo "Linking Git configuration..."
# .gitconfig is intentionally NOT symlinked. Sourcetree rewrites ~/.gitconfig
# on launch, which would dirty the tracked file. Instead, ~/.gitconfig is a
# thin local stub that [include]s the tracked base; tool-managed sections
# (Sourcetree difftool/mergetool, commit.template) live in the stub only.
if [ ! -e "$HOME/.gitconfig" ] || [ -L "$HOME/.gitconfig" ]; then
    [ -L "$HOME/.gitconfig" ] && unlink "$HOME/.gitconfig"
    cat > "$HOME/.gitconfig" <<'GITCONFIG_STUB'
# Local layer for ~/.gitconfig. Tracked base lives in ~/.dotfiles/git/.gitconfig.
# Tool-managed sections (Sourcetree etc.) belong here, NOT in the tracked file.

[include]
	path = ~/.dotfiles/git/.gitconfig
GITCONFIG_STUB
    echo "  ✓ ~/.gitconfig stub created"
fi
for f in .gitconfig_personal .gitconfig_company .gitignore_global; do
    link_file "$DOTFILES/git/$f" "$HOME/$f"
done
git config --global core.excludesfile "$HOME/.gitignore_global"
git config --global core.editor "nvim"

# Git LFS: register global clean/smudge filters (binary comes from Brewfile).
# --skip-repo avoids planting LFS hooks in this non-LFS dotfiles repo. Writes
# filter.lfs.* into the ~/.gitconfig stub (untracked). Existing LFS repos still
# need `git lfs install` run once in-repo for the pre-push hook (fresh clones
# pick the hooks up on checkout).
if command -v git-lfs &>/dev/null; then
    git lfs install --skip-repo >/dev/null 2>&1 && echo "  ✓ Git LFS filters registered"
fi

#-------------------------------------------------------------------------------
# Tmux Plugin Manager
#-------------------------------------------------------------------------------
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
    git clone https://github.com/tmux-plugins/tpm $HOME/.tmux/plugins/tpm
fi
if [ -x "$HOME/.tmux/plugins/tpm/bin/install_plugins" ]; then
    "$HOME/.tmux/plugins/tpm/bin/install_plugins"
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
# Link standalone scripts into ~/.local/bin (on PATH)
#-------------------------------------------------------------------------------
echo "Linking scripts to ~/.local/bin..."
mkdir -p "$HOME/.local/bin"
for s in admin-api-token.sh; do
    link_file "$DOTFILES/scripts/$s" "$HOME/.local/bin/$s"
done

#-------------------------------------------------------------------------------
# Link .config directories
#-------------------------------------------------------------------------------
echo "Linking .config directories..."
mkdir -p "${XDG_CONFIG_HOME:=$HOME/.config}"
for dir in nvim ghostty kitty yazi; do
    target="$HOME/.config/$dir"
    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup="${target}.backup.$(date +%Y%m%d%H%M%S)"
        mv "$target" "$backup"
        echo "  ↳ backed up existing $dir to $(basename "$backup")"
    elif [ -L "$target" ]; then
        rm -f "$target"
    fi
    ln -nfs "$DOTFILES/.config/$dir" "$target"
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
if ! mise which python &>/dev/null; then
    echo "Installing Python 3.12 via mise..."
    mise install python@3.12
    mise use -g python@3.12
    eval "$(mise activate bash)"
fi

#-------------------------------------------------------------------------------
# Install Python tools: uv and Poetry
#-------------------------------------------------------------------------------
echo "Setting up Python package managers..."

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "  ✓ uv installed"
else
    echo "  ✓ uv already installed"
fi

if ! command -v poetry &>/dev/null; then
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
eval "$(mise activate bash)"
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
for dir in agents hooks output-styles rules; do
    link_file "$DOTFILES/.claude/$dir" "$HOME/.claude/$dir"
done
for f in settings.json CLAUDE.md; do
    link_file "$DOTFILES/.claude/$f" "$HOME/.claude/$f"
done

# Per-skill symlinks: ~/.claude/skills/ is a real directory so external tools
# (gstack, etc.) can write siblings without touching dotfiles.
# Ongoing sync (skills added after install) is handled by the link-skills.sh
# SessionStart hook — this loop just seeds the links on a fresh install.
echo "Linking custom skills individually..."
mkdir -p "$HOME/.claude/skills"
# If old setup left a directory-level symlink, replace it with a real directory.
if [ -L "$HOME/.claude/skills" ]; then
    unlink "$HOME/.claude/skills"
    mkdir -p "$HOME/.claude/skills"
fi
for src in "$DOTFILES/.claude/skills"/*/; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    ln -nfs "$src" "$HOME/.claude/skills/$name"
done
echo "  ✓ custom skills linked"

#-------------------------------------------------------------------------------
# Link shared agent skills
#-------------------------------------------------------------------------------
mkdir -p "$HOME/.agents"
link_file "$DOTFILES/.claude/skills" "$HOME/.agents/skills"

#-------------------------------------------------------------------------------
# Register Claude Code MCP servers (user scope)
#-------------------------------------------------------------------------------
"$DOTFILES/.claude/setup-mcp.sh"

#-------------------------------------------------------------------------------
# Link Antigravity CLI configuration
#-------------------------------------------------------------------------------
# (Legacy Gemini CLI config — settings.json/hooks/agents/policies — was removed
#  after Gemini CLI stopped serving free/Pro/Ultra tiers on 2026-06-18.
#  Antigravity CLI keeps its own config under ~/.gemini/antigravity-cli/.)
echo "Setting up Antigravity CLI configuration..."
mkdir -p "$HOME/.gemini/antigravity-cli"
mkdir -p "$HOME/.gemini/antigravity"
mkdir -p "$HOME/.gemini/config"
# Antigravity CLI reads ~/.gemini/GEMINI.md as the global developer context.
# Share the single collaboration-style source (same file Claude/Codex use).
link_file "$DOTFILES/.claude/docs/working-style.md" "$HOME/.gemini/GEMINI.md"
# NOTE: Antigravity CLI rewrites settings.json and hooks.json as REAL files at
# runtime, breaking these symlinks (same pattern as Sourcetree vs ~/.gitconfig).
# That drift is expected: this block only seeds links on a fresh machine.
# Treat the dotfiles copies as the canonical source and re-run install.sh
# (or re-link manually) after Antigravity clobbers them.
link_file "$DOTFILES/.gemini/antigravity-cli/settings.json" "$HOME/.gemini/antigravity-cli/settings.json"
link_file "$DOTFILES/.gemini/antigravity-cli/hooks" "$HOME/.gemini/antigravity-cli/hooks"
link_file "$DOTFILES/.gemini/antigravity-cli/mcp_config.json" "$HOME/.gemini/config/mcp_config.json"
link_file "$DOTFILES/.gemini/antigravity-cli/hooks.json" "$HOME/.gemini/config/hooks.json"
link_file "$HOME/.gemini/config/mcp_config.json" "$HOME/.gemini/antigravity-cli/mcp_config.json"
link_file "$HOME/.gemini/config/hooks.json" "$HOME/.gemini/antigravity-cli/hooks.json"
link_file "$DOTFILES/.claude/skills" "$HOME/.gemini/config/skills"
link_file "$DOTFILES/.claude/skills" "$HOME/.gemini/antigravity-cli/skills"
link_file "$DOTFILES/.claude/skills" "$HOME/.gemini/antigravity/skills"

#-------------------------------------------------------------------------------
# Link Codex CLI configuration
#-------------------------------------------------------------------------------
echo "Setting up Codex CLI configuration..."
mkdir -p "$HOME/.codex"
link_file "$DOTFILES/.codex/config.toml.example" "$HOME/.codex/config.toml.example"
link_file "$DOTFILES/.codex/config/global.json" "$HOME/.codex/hooks.json"
link_file "$DOTFILES/.codex/hooks" "$HOME/.codex/hooks"
link_file "$DOTFILES/.codex/rules" "$HOME/.codex/rules"
# 전역 협업 방식 정본 공유 (Claude working-style.md와 단일 소스)
link_file "$DOTFILES/.claude/docs/working-style.md" "$HOME/.codex/AGENTS.md"
if [ ! -f "$HOME/.codex/config.toml" ]; then
    cp "$HOME/.codex/config.toml.example" "$HOME/.codex/config.toml"
    echo "  ✓ config.toml created from example"
fi
"$DOTFILES/.codex/setup-mcp.sh"

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
if [ "$SHELL" != "$(command -v zsh)" ]; then
    echo "Changing default shell to zsh..."
    chsh -s "$(command -v zsh)"
fi

echo "✅ Dotfiles installation completed!"
echo "Please restart your terminal or run: source ~/.zshrc"
