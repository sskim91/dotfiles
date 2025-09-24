#TLDR
export TLDR_AUTO_UPDATE_DISABLED="FALSE"

# JENV
#export PATH="$HOME/.jenv/bin:$PATH"
#if which jenv > /dev/null; then eval "$(jenv init -)"; fi

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

# asdf
export ASDF_DATA_DIR="/Users/sskim/.asdf"
export PATH="$ASDF_DATA_DIR/shims:$PATH"

# rust
export PATH="$HOME/.asdf/installs/rust/stable/bin:$PATH"

#HOMEBREW
export HOMEBREW_GITHUB_API_TOKEN="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"

# node
# export PATH="/usr/local/opt/icu4c/bin:$PATH"
# export PATH="/usr/local/opt/icu4c/sbin:$PATH"
# export PATH="/usr/local/sbin:$PATH"

# NVM
# export NVM_DIR="$HOME/.nvm"
# [ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"                                       # This loads nvm
# [ -s "/usr/local/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/usr/local/opt/nvm/etc/bash_completion.d/nvm" # This loads nvm bash_completion

#poetry
export PATH="$HOME/.local/bin:$PATH"

#fd fzf
# export FZF_DEFAULT_COMMAND="fd --type file --color=always"
# export FZF_DEFAULT_OPTS="--height 60% --layout=reverse --ansi"
export FZF_DEFAULT_COMMAND="fd --hidden --strip-cwd-prefix --exclude .git --exclude bower_components --exclude node_modules"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="fd --type=d --hidden --strip-cwd-prefix --exclude .git --exclude bower_components --exclude node_modules"

# Use fd (https://github.com/sharkdp/fd) for listing path candidates.
# - The first argument to the function ($1) is the base path to start traversal
# - See the source code (completion.{bash,zsh}) for the details.
_fzf_compgen_path() {
  fd --hidden --exclude .git . "$1"
}

# Use fd to generate the list for directory completion
_fzf_compgen_dir() {
  fd --type=d --hidden --exclude .git . "$1"
}

export FZF_CTRL_T_OPTS="--preview 'bat -n --color=always --line-range :500 {}'"
export FZF_ALT_C_OPTS="--preview 'eza --tree --color=always {} | head -200'"

# Advanced customization of fzf options via _fzf_comprun function
# - The first argument to the function is the name of the command.
# - You should make sure to pass the rest of the arguments to fzf.
_fzf_comprun() {
  local command=$1
  shift

  case "$command" in
  cd) fzf --preview 'eza --tree --color=always {} | head -200' "$@" ;;
  export | unset) fzf --preview "eval 'echo \$'{}" "$@" ;;
  ssh) fzf --preview 'dig {}' "$@" ;;
  *) fzf --preview "bat -n --color=always --line-range :500 {}" "$@" ;;
  esac
}

#ngrok
if command -v ngrok &>/dev/null; then
  eval "$(ngrok completion)"
fi

export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Claude Hooks Configuration

# JavaScript 개발 도구 (javascript-check.sh, javascript-format.sh)
#export ENABLE_ESLINT=1         # ESLint - JavaScript 린팅 (check)
#export ENABLE_PRETTIER=1       # Prettier - 코드 포맷터 (format - 기본값 1)
# export ENABLE_BIOME=0        # Biome - 올인원 도구 (필요시 활성화)
# export ENABLE_OXC=0          # OXC - Rust 기반 린터 (필요시 활성화)
# export ENABLE_STANDARD=0     # Standard JS - 제로 설정 스타일 (필요시 활성화)
# export ENABLE_DPRINT=0       # dprint - 빠른 포맷터 (필요시 활성화)

# TypeScript 개발 도구 (typescript-check.sh, typescript-format.sh)
#export ENABLE_TSC=1            # TypeScript Compiler - 타입 체크 (check)
# PRETTIER는 위에서 이미 선언 (TypeScript format에도 사용)

# Python 개발 도구 (python-check.sh, python-format.sh)
#export ENABLE_RUFF=1           # Ruff - Python 린터/포맷터 (format - 기본값 1, check에서는 0)
#export ENABLE_BLACK=1          # Black - Python 포맷터 (format - 기본값 1)
#export ENABLE_ISORT=1          # isort - import 정렬 (format - 기본값 1)
# export ENABLE_TY=0           # Typos - 오타 검사 (check - 필요시 활성화)
# export ENABLE_PYREFLY=0      # Pyrefly - 정적 분석 (check - 필요시 활성화)

# Java 개발 도구 (java-check.sh, java-format.sh)
#export ENABLE_GOOGLE_JAVA_FORMAT=1  # Google Java Format (format - 기본값 1)
# export ENABLE_CHECKSTYLE=0         # Checkstyle - 스타일 체커 (check - 필요시 활성화)
# export ENABLE_SPOTBUGS=0           # SpotBugs - 버그 검출 (check - 필요시 활성화)
# export ENABLE_PMD=0                 # PMD - 코드 분석 (check - 필요시 활성화)
