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
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

brew bundle
#-------------------------------------------------------------------------------
# Install global Git configuration
#-------------------------------------------------------------------------------

ln -nfs $DOTFILES/.gitconfig $HOME/.gitconfig
git config --global core.excludesfile $DOTFILES/.gitignore_global
git config --global core.editor "nvim"

#-------------------------------------------------------------------------------
# Make ZSH the default shell environment
#-------------------------------------------------------------------------------
chsh -s $(which zsh)

#-------------------------------------------------------------------------------
# Install Oh-my-zsh
#-------------------------------------------------------------------------------
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"


git clone https://github.com/dracula/zsh.git zsh-dracular
mkdir -p $ZSH/themes/lib
mv zsh-dracula/dracula.zsh-theme $ZSH/themes
mv zsh-dracula/lib/async.zsh $ZSH/themes/lib

git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-completions $ZSH_CUSTOM/plugins/zsh-completions
git clone https://github.com/djui/alias-tips.git $ZSH_CUSTOM/plugins/alias-tips

#-------------------------------------------------------------------------------
# Vim setting
#-------------------------------------------------------------------------------
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
ln -nfs $DOTFILES/.vimrc $HOME/.vimrc
vim +PluginInstall +qall

# Neovim 관련
#mkdir -p ${XDG_CONFIG_HOME:=$HOME/.config}
#ln -s ~/.vim $XDG_CONFIG_HOME/nvim
#ln -s ~/.vimrc $XDG_CONFIG_HOME/nvim/init.vim
