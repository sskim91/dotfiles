alias cd..="cd .."
alias ..='cd ..'
alias ...='cd ../../../'
alias ....='cd ../../../../'
alias .....='cd ../../../../'
alias .4='cd ../../../../'
alias .5='cd ../../../../..'
alias dl="cd ~/Downloads"

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

alias ll="exa --color-scale --icons --time-style long-iso -lhbg"
alias la="exa --color-scale --icons --time-style long-iso -lahbg"
alias ls="exa"
alias lt="exa --tree --level=2"

alias c="clear"

alias h="history"
alias hs="history | grep"
alias hsi="history -i | grep"

alias d='date +%F'
alias now='date +"%T"'
alias nowtime=now
alias nowdate='date +"%Y-%m-%d"'

