alias cd..="cd .."
alias ..='cd ..'
alias ...='cd ../../'
alias ....='cd ../../../'
alias .....='cd ../../../../'
alias .2='cd ../../'
alias .3='cd ../../../'
alias .4='cd ../../../../'
alias .5='cd ../../../../../'

# navigation aliases
alias dl="cd ~/Downloads"
alias desk="cd ~/Desktop"
alias dot="cd ~/.dotfiles"
alias dev="cd ~/dev"

alias vim="nvim"
alias vi="nvim"
alias vimdiff="nvim -d"
alias cat="bat"

alias top="htop"
alias zshconfig="vim ~/.zshrc"
alias ohmyzsh="vim ~/.oh-my-zsh"

alias rm="rm -i"
alias cp='cp -i'
alias ln='ln -i'
alias mv='mv -i'

alias update="brew update && brew upgrade && brew cleanup"
alias services="brew services"

alias ll="eza --color-scale all --icons --time-style long-iso -lhbg"
alias la="eza --color-scale all --icons --time-style long-iso -lahbg"
alias ls="eza"
alias lt="eza --tree --level=2"

alias c="clear"

alias h="history"
alias hs="history | grep"
alias hsi="history -i | grep"

alias d='date +%F'
alias now='date +"%T"'
alias nowtime=now
alias nowdate='date +"%Y-%m-%d"'

# ping: stop after 5 pings
alias ping='ping -c 5'

# curl: only display HTTP header
alias header='curl -I'

## set some other defaults ##
alias df='duf'
alias du='du -ch'

alias ag="alias | grep " # +command

