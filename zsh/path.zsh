# JENV
export PATH="$HOME/.jenv/bin:$PATH"
if which jenv > /dev/null; then eval "$(jenv init -)"; fi

# NEOVIM
export EDITOR="/usr/local/bin/nvim"

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PATH"

# maven
export PATH="/usr/local/opt/maven/bin:$PATH"

# bat
export MANPAGER="sh -c 'col -bx | bat -l man -p'"

# oracle cloud
#export ORACLE_HOME=~/Oracle/instantclient_19_8
#export TNS_ADMIN=$ORACLE_HOME/network/admin
#export NLS_LANG=English_America.UTF8
#export PATH=$PATH:$ORACLE_HOME

#HOMEBREW
export HOMEBREW_GITHUB_API_TOKEN="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"

# node
export PATH="/usr/local/opt/icu4c/bin:$PATH"
export PATH="/usr/local/opt/icu4c/sbin:$PATH"
export PATH="/usr/local/sbin:$PATH"

# NVM
export NVM_DIR="$HOME/.nvm"
  [ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"  # This loads nvm
  [ -s "/usr/local/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/usr/local/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
