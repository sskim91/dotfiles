#!/bin/bash

# Required steps must not fall through to the final success message. pipefail
# also catches a failed download piped into a shell that receives empty input.
set -Ee -o pipefail
trap 'status=$?; echo "❌ Installation stopped at line $LINENO (exit $status)." >&2; exit "$status"' ERR

export DOTFILES="$HOME/.dotfiles"

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
# bash reads a script incrementally while running it, so a pull that rewrites
# install.sh would make the rest execute from a shifted offset. If the pull moved
# HEAD, re-exec the fresh copy from the top. The whole `if` block is parsed before
# it runs, so the exec here is safe; the env guard prevents a second pull.
if [ -e "$DOTFILES/.git" ] && [ -z "${DOTFILES_SELF_UPDATED:-}" ]; then
  if [ "$(git -C "$DOTFILES" symbolic-ref --short -q HEAD || true)" != main ]; then
    echo "❌ Self-update requires the main branch. Checkout main and re-run." >&2
    exit 1
  fi
  if [ -n "$(git -C "$DOTFILES" status --porcelain)" ]; then
    echo "❌ Self-update requires a clean checkout. Preserve local changes before re-running." >&2
    exit 1
  fi
  before=$(git -C "$DOTFILES" rev-parse HEAD)
  if ! git -C "$DOTFILES" -c pull.rebase=false -c merge.autostash=false \
      pull --ff-only origin main; then
    echo "❌ Self-update failed. No installation steps will follow." >&2
    exit 1
  fi
  if [ "$(git -C "$DOTFILES" rev-parse HEAD 2>/dev/null)" != "$before" ]; then
    echo "  ↻ dotfiles updated; re-running the new install.sh"
    export DOTFILES_SELF_UPDATED=1
    exec bash "$DOTFILES/install.sh" "$@"
  fi
fi

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------
optional_failures=()

warn_optional() {
    optional_failures+=("$1")
    echo "  ⚠️  $1" >&2
}

# Use for individual optional commands, not multi-command shell functions:
# running a function in an `if` disables errexit throughout that function.
run_optional() {
    local label="$1"
    shift
    if "$@"; then
        echo "  ✓ $label"
    else
        warn_optional "$label failed; re-run after resolving the error"
    fi
}

link_file() {
    local src="$1" dst="$2"
    if [ -e "$src" ] || [ -L "$src" ]; then
        if [ -e "$dst" ] && [ ! -L "$dst" ]; then
            local backup
            backup=$(mktemp -d "${dst}.backup.XXXXXXXX") || return 1
            mv "$dst" "$backup/$(basename "$dst")" || return 1
            echo "  ↳ backed up existing $(basename "$dst") to $(basename "$backup")"
        fi
        ln -nfs "$src" "$dst" || return 1
        echo "  ✓ $(basename "$dst")"
    else
        echo "  ❌ Required source not found: $src" >&2
        return 1
    fi
}

# Merge a canonical hooks.json into a destination that a third party owns at runtime.
#
# Why this exists: cmux rewrites ~/.gemini/config/hooks.json as a real file containing
# only its own "cmux" block. Re-running link_file there would restore our canonical file
# and delete cmux's 8 hooks — the "just re-run install.sh" advice was actively harmful
# (found 2026-08-27). A top-level merge keeps both.
#
# Only safe when the two sides own DIFFERENT top-level keys. That holds for Antigravity
# ("cmux" vs "file-write-safety"), but NOT for ~/.codex/hooks.json, where cmux and our
# hooks share one ".hooks" object and `*` would replace whole event arrays. Codex keeps
# plain link_file: cmux re-merges our scripts on its next launch, so it self-heals.
merge_hooks_json() {
    local src="$1" dst="$2"
    # Nothing there yet, or still our symlink: plain link is correct.
    if [ ! -e "$dst" ] || [ -L "$dst" ]; then
        link_file "$src" "$dst"
        return
    fi
    if ! command -v jq >/dev/null 2>&1; then
        echo "  ⚠️  jq not found; left existing $(basename "$dst") untouched"
        return 1
    fi
    local backup="${dst}.backup.$(date +%Y%m%d%H%M%S)"
    if ! command cp "$dst" "$backup"; then
        echo "  ⚠️  could not back up $(basename "$dst"); left unchanged"
        return 1
    fi
    # `command mv -f`: an interactive mv alias/function would otherwise prompt, decline,
    # and leave the merge unapplied. The success message is gated on the mv itself —
    # printing it unconditionally is how a rename that never happened looks like a win.
    if jq -s '.[0] * .[1]' "$dst" "$src" > "$dst.tmp" 2>/dev/null \
        && jq empty "$dst.tmp" 2>/dev/null \
        && command mv -f "$dst.tmp" "$dst"; then
        echo "  ✓ merged $(basename "$src") into existing $(basename "$dst") (backup: $(basename "$backup"))"
    else
        command rm -f "$dst.tmp"
        echo "  ⚠️  merge failed for $(basename "$dst"); left unchanged (backup: $(basename "$backup"))"
        return 1
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
    brew_installer=$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)
    NONINTERACTIVE=1 /bin/bash -c "$brew_installer"

    brew_environment=$(/opt/homebrew/bin/brew shellenv)
    eval "$brew_environment"
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
        warn_optional "Some Homebrew casks failed to install"
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
    command -v agy >/dev/null
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
git config --file "$HOME/.gitconfig" --no-includes --list >/dev/null
if git_includes=$(git config --file "$HOME/.gitconfig" --no-includes --get-all include.path); then
    :
else
    # A missing key is expected; other Git errors must stop installation.
    [ "$?" -eq 1 ] || exit 1
fi
if ! printf '%s\n' "$git_includes" | grep -Fxq -e '~/.dotfiles/git/.gitconfig' -e "$DOTFILES/git/.gitconfig"; then
    git_backup=$(mktemp "${HOME}/.gitconfig.backup.XXXXXXXX")
    cp -p "$HOME/.gitconfig" "$git_backup"
    git_stub=$(mktemp "${HOME}/.gitconfig.tmp.XXXXXXXX")
    # Put the base first so the existing host layer keeps its precedence.
    printf '[include]\n\tpath = ~/.dotfiles/git/.gitconfig\n\n' > "$git_stub"
    cat "$HOME/.gitconfig" >> "$git_stub"
    git config --file "$git_stub" --no-includes --list >/dev/null
    mv -f "$git_stub" "$HOME/.gitconfig"
    echo "  ✓ Git base include added (backup: $git_backup)"
fi
for f in .gitconfig_personal .gitconfig_company .gitignore_global; do
    link_file "$DOTFILES/git/$f" "$HOME/$f"
done
# core.excludesfile / core.editor live in the tracked git/.gitconfig — not written here.

# Git LFS: register global clean/smudge filters (binary comes from Brewfile).
# --skip-repo avoids planting LFS hooks in this non-LFS dotfiles repo. Writes
# filter.lfs.* into the ~/.gitconfig stub (untracked). Existing LFS repos still
# need `git lfs install` run once in-repo for the pre-push hook (fresh clones
# pick the hooks up on checkout).
if command -v git-lfs &>/dev/null; then
    git lfs install --skip-repo
    echo "  ✓ Git LFS filters registered"
fi

#-------------------------------------------------------------------------------
# Tmux Plugin Manager
#-------------------------------------------------------------------------------
link_file "$DOTFILES/.tmux.conf" "$HOME/.tmux.conf"
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
    git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi
"$HOME/.tmux/plugins/tpm/bin/install_plugins"

#-------------------------------------------------------------------------------
# Install Oh-my-zsh (non-interactive mode)
#-------------------------------------------------------------------------------
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    omz_installer=$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)
    RUNZSH=no KEEP_ZSHRC=yes sh -c "$omz_installer"
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
for f in .zshenv .zshrc .zprofile .vimrc; do
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
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
mkdir -p "$XDG_CONFIG_HOME"
for dir in nvim ghostty kitty yazi; do
    link_file "$DOTFILES/.config/$dir" "$XDG_CONFIG_HOME/$dir"
done

#-------------------------------------------------------------------------------
# Neovim / LazyVim setup
#-------------------------------------------------------------------------------
echo "Setting up Neovim with LazyVim..."
# Preserve existing data/state/cache, including sessions and undo history.
nvim_data="${XDG_DATA_HOME:-$HOME/.local/share}/nvim"
if command -v nvim &> /dev/null; then
    echo "Installing LazyVim plugins..."
    # Neovim may exit 0 after command/task errors. Convert them to a failed
    # process explicitly; Lazy! waits for sync before inspecting task results.
    if nvim --headless -c 'lua
        local ok, err = pcall(function()
            assert(vim.v.errmsg == "", vim.v.errmsg)
            vim.cmd("Lazy! sync")
            local config = require("lazy.core.config")
            local plugin = require("lazy.core.plugin")
            for _, group in ipairs({ config.plugins, config.to_clean }) do
                for _, item in pairs(group) do
                    assert(not plugin.has_errors(item), "Lazy task failed: " .. item.name)
                end
            end
            assert(vim.v.errmsg == "", vim.v.errmsg)
        end)
        if not ok then
            vim.api.nvim_err_writeln(tostring(err))
            vim.cmd("cquit 1")
        end
    ' +qa; then
        mkdir -p "$nvim_data"
        touch "$nvim_data/.lazyvim-installed"
        echo "  ✓ LazyVim plugins installed"
    else
        warn_optional "LazyVim sync failed; existing Neovim data was preserved"
    fi
else
    warn_optional "nvim not found; LazyVim setup skipped"
fi

#-------------------------------------------------------------------------------
# Install Node.js LTS using mise
#-------------------------------------------------------------------------------
if ! mise which node &>/dev/null; then
    echo "Installing Node.js LTS via mise..."
    mise install node@lts
    mise use -g node@lts
    mise_activation=$(mise activate bash)
    eval "$mise_activation"
fi

#-------------------------------------------------------------------------------
# Install Python 3.12 using mise
#-------------------------------------------------------------------------------
if ! mise which python &>/dev/null; then
    echo "Installing Python 3.12 via mise..."
    mise install python@3.12
    mise use -g python@3.12
    mise_activation=$(mise activate bash)
    eval "$mise_activation"
fi

#-------------------------------------------------------------------------------
# Install Python tools: uv and Poetry
#-------------------------------------------------------------------------------
echo "Setting up Python package managers..."

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null
    echo "  ✓ uv installed"
else
    echo "  ✓ uv already installed"
fi

if ! command -v poetry &>/dev/null; then
    echo "Installing Poetry..."
    curl -fsSL https://install.python-poetry.org | sed 's/symlinks=False/symlinks=True/' | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    command -v poetry >/dev/null
    echo "  ✓ Poetry installed"
else
    echo "  ✓ Poetry already installed"
fi

run_optional "youtube-transcript-api installation" uv pip install --system youtube-transcript-api
run_optional "detect-secrets installation" uv pip install --system detect-secrets

#-------------------------------------------------------------------------------
# Install LSP server binaries (npm-based)
#-------------------------------------------------------------------------------
echo "Setting up LSP servers..."
mise_activation=$(mise activate bash)
eval "$mise_activation"
run_optional "pyright installation" npm install -g pyright
run_optional "typescript-language-server installation" npm install -g typescript-language-server typescript

#-------------------------------------------------------------------------------
# Install Codex CLI (npm, under mise node)
# The codex-app cask is the desktop app only; .codex/setup-mcp.sh below needs the CLI.
#-------------------------------------------------------------------------------
echo "Setting up Codex CLI..."
if ! command -v codex &>/dev/null; then
    if npm install -g @openai/codex && command -v codex >/dev/null; then
        echo "  ✓ Codex CLI installed"
    else
        warn_optional "Codex CLI install failed; Codex MCP setup will be skipped"
    fi
else
    echo "  ✓ Codex CLI already installed ($(codex --version 2>/dev/null))"
fi

#-------------------------------------------------------------------------------
# Install Claude Code (native binary)
#-------------------------------------------------------------------------------
echo "Setting up Claude Code..."
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash
    command -v claude >/dev/null
    echo "  ✓ Claude Code installed"
else
    echo "  ✓ Claude Code already installed ($(claude --version 2>/dev/null))"
fi

#-------------------------------------------------------------------------------
# Link Claude Code configuration
#-------------------------------------------------------------------------------
echo "Setting up Claude Code configuration..."
mkdir -p "$HOME/.claude"
for dir in hooks output-styles rules; do
    link_file "$DOTFILES/.claude/$dir" "$HOME/.claude/$dir"
done
# spinner-tips.json must be linked: settings.json references it by absolute
# path (`~/.claude/spinner-tips.json`), because tipsFile rejects relative paths.
for f in settings.json CLAUDE.md spinner-tips.json; do
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
# Prune dangling links left by skills deleted from dotfiles (link-skills.sh is
# add-only). Only links that point into $DOTFILES/.claude/skills are touched;
# external/plugin siblings are left alone.
for link in "$HOME/.claude/skills"/*; do
    [ -L "$link" ] && [ ! -e "$link" ] || continue
    case "$(readlink "$link")" in
        "$DOTFILES/.claude/skills/"*)
            unlink "$link"
            echo "  ↳ removed stale skill link $(basename "$link")"
            ;;
    esac
done
echo "  ✓ custom skills linked"

#-------------------------------------------------------------------------------
# Link Codex-owned agent skills
#-------------------------------------------------------------------------------
mkdir -p "$HOME/.agents"
link_file "$DOTFILES/.codex/skills" "$HOME/.agents/skills"

#-------------------------------------------------------------------------------
# Register Claude Code MCP servers (user scope)
#-------------------------------------------------------------------------------
run_optional "Claude MCP setup" "$DOTFILES/.claude/setup-mcp.sh"

#-------------------------------------------------------------------------------
# Link Antigravity CLI configuration
#-------------------------------------------------------------------------------
# (Legacy Gemini CLI config — settings.json/hooks/agents/policies — was removed
#  after Gemini CLI stopped serving free/Pro/Ultra tiers on 2026-06-18.
#  Antigravity CLI keeps its own config under ~/.gemini/antigravity-cli/.)
echo "Setting up Antigravity CLI configuration..."
mkdir -p "$HOME/.gemini/antigravity-cli"
mkdir -p "$HOME/.gemini/config"
# Antigravity CLI reads ~/.gemini/GEMINI.md as the global developer context.
# Share the collaboration-style source with Claude; Codex has its own AGENTS.md.
link_file "$DOTFILES/.claude/docs/working-style.md" "$HOME/.gemini/GEMINI.md"
# NOTE: Antigravity CLI rewrites settings.json as a REAL file at runtime, breaking
# that symlink (same pattern as Sourcetree vs ~/.gitconfig). That drift is expected:
# the dotfiles copy stays canonical and re-running install.sh re-links it.
#
# hooks.json is different and must NOT be re-linked: cmux owns that file at runtime and
# writes only its own "cmux" block. Re-linking would restore our canonical file and
# delete cmux's hooks, so it goes through merge_hooks_json (top-level merge, both kept).
link_file "$DOTFILES/.gemini/antigravity-cli/settings.json" "$HOME/.gemini/antigravity-cli/settings.json"
link_file "$DOTFILES/.gemini/antigravity-cli/hooks" "$HOME/.gemini/antigravity-cli/hooks"
link_file "$DOTFILES/.gemini/antigravity-cli/mcp_config.json" "$HOME/.gemini/config/mcp_config.json"
merge_hooks_json "$DOTFILES/.gemini/antigravity-cli/hooks.json" "$HOME/.gemini/config/hooks.json"
link_file "$HOME/.gemini/config/mcp_config.json" "$HOME/.gemini/antigravity-cli/mcp_config.json"
link_file "$HOME/.gemini/config/hooks.json" "$HOME/.gemini/antigravity-cli/hooks.json"
# Skills: ~/.gemini/config/skills is the ONLY path recognized by all Antigravity
# flavors (app/CLI/IDE) — verified empirically 2026-07. Per-flavor paths
# (antigravity-cli/skills, antigravity/skills) are redundant; do not re-add.
link_file "$DOTFILES/.claude/skills" "$HOME/.gemini/config/skills"

#-------------------------------------------------------------------------------
# Link Codex CLI configuration
#-------------------------------------------------------------------------------
echo "Setting up Codex CLI configuration..."
mkdir -p "$HOME/.codex"
link_file "$DOTFILES/.codex/config.toml.example" "$HOME/.codex/config.toml.example"
link_file "$DOTFILES/.codex/config/global.json" "$HOME/.codex/hooks.json"
link_file "$DOTFILES/.codex/hooks" "$HOME/.codex/hooks"
link_file "$DOTFILES/.codex/rules" "$HOME/.codex/rules"
# Codex uses a concise model-specific contract; Claude/Gemini share working-style.md.
link_file "$DOTFILES/.codex/AGENTS.md" "$HOME/.codex/AGENTS.md"
if [ ! -f "$HOME/.codex/config.toml" ]; then
    cp "$HOME/.codex/config.toml.example" "$HOME/.codex/config.toml"
    echo "  ✓ config.toml created from example"
fi
if command -v codex >/dev/null; then
    run_optional "Codex MCP setup" "$DOTFILES/.codex/setup-mcp.sh"
fi

#-------------------------------------------------------------------------------
# Link Karabiner-Elements configuration
#-------------------------------------------------------------------------------
echo "Setting up Karabiner-Elements..."
mkdir -p "$XDG_CONFIG_HOME/karabiner/assets/complex_modifications"
link_file "$DOTFILES/.config/karabiner/my_custom_key.json" \
    "$XDG_CONFIG_HOME/karabiner/assets/complex_modifications/my_custom_key.json"

#-------------------------------------------------------------------------------
# Link .config files
#-------------------------------------------------------------------------------
echo "Linking .config files..."
for file in ruff/ruff.toml zed/settings.json; do
    mkdir -p "$XDG_CONFIG_HOME/$(dirname "$file")"
    link_file "$DOTFILES/.config/$file" "$XDG_CONFIG_HOME/$file"
done

#-------------------------------------------------------------------------------
# Yazi plugins and flavors
#-------------------------------------------------------------------------------
if command -v ya &> /dev/null; then
    run_optional "Yazi fzf plugin" ya pkg add yazi-rs/plugins:fzf
    run_optional "Yazi catppuccin-mocha flavor" ya pkg add yazi-rs/flavors:catppuccin-mocha
    run_optional "Yazi catppuccin-latte flavor" ya pkg add yazi-rs/flavors:catppuccin-latte
else
    warn_optional "ya not found; Yazi packages skipped"
fi

#-------------------------------------------------------------------------------
# Setup pre-commit hooks
#-------------------------------------------------------------------------------
echo "Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    (cd "$DOTFILES" && pre-commit install)
    echo "  ✓ pre-commit hooks installed"
else
    warn_optional "pre-commit not found; hook installation skipped"
fi

#-------------------------------------------------------------------------------
# Make ZSH the default shell environment
#-------------------------------------------------------------------------------
if [ "$SHELL" != "$(command -v zsh)" ]; then
    echo "Changing default shell to zsh..."
    chsh -s "$(command -v zsh)"
fi

#-------------------------------------------------------------------------------
# Installation summary
#-------------------------------------------------------------------------------
if [ "${#optional_failures[@]}" -gt 0 ]; then
    echo "⚠️  Dotfiles installation partially completed:" >&2
    printf '  - %s\n' "${optional_failures[@]}" >&2
    echo "Resolve the errors above and re-run install.sh." >&2
    exit 2
fi
echo "✅ Dotfiles installation completed!"
echo "Please restart your terminal or run: source ~/.zshrc"
