#!/bin/bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

brew bundle

git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-completions $ZSH_CUSTOM/plugins/zsh-autosuggestions
git clone https://github.com/djui/alias-tips.git $ZSH_CUSTOM/plugins/zsh-autosuggestions

# Neovim 관련
#mkdir -p ${XDG_CONFIG_HOME:=$HOME/.config}
#ln -s ~/.vim $XDG_CONFIG_HOME/nvim
#ln -s ~/.vimrc $XDG_CONFIG_HOME/nvim/init.vim
