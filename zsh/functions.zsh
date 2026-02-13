# ref: https://github.com/appkr/dotfiles/blob/master/functions.sh
#-------------------------------------------------------------------------------
# Create a new directory and enter it
#-------------------------------------------------------------------------------
function mkd() {
    mkdir -p "$@" && cd "$_"
}

#-------------------------------------------------------------------------------
# Open man page as PDF
#-------------------------------------------------------------------------------
function manpdf() {
    mandoc -T pdf "$(man -w "${1}")" | open -f -a /System/Applications/Preview.app
}

#-------------------------------------------------------------------------------
# Convert EUC-KR to UTF-8
#-------------------------------------------------------------------------------
function enc() {
    iconv -c -f EUC-KR -t UTF-8 $1 >utf8_"$1"
}

#-------------------------------------------------------------------------------
# find pid
#-------------------------------------------------------------------------------
function findpid() {
  if [ "$1" = "" ]; then
    echo "Find Pid by Port"
    echo ""
    echo "Usage:"
    echo '  findpid "<port>"'
    return 0
  fi

  local PORT="$1"
  echo -e "\033[0;33m$(lsof -t -i :$PORT)\033[0m"
}

#-------------------------------------------------------------------------------
# Kill Port
#-------------------------------------------------------------------------------
function killport() {
    if [ "$1" = "" ]; then
        echo "Print text in \033[0;33mYellow\033[0m color"
        echo ""
        echo "Usage:"
        echo '  killport "<port>"'
        return 0
    fi

    local PORT="$1"
    kill $(lsof -t -i :$PORT)
    echo -e "\033[0;33m${PORT} port has been closed\033[0m"
}

#-------------------------------------------------------------------------------
# Reload zsh
#-------------------------------------------------------------------------------
function rr() {
    source $HOME/.zshrc
    # PATH 중복 제거 (재로드 시 동일 경로 누적 방지)
    export PATH=$(printf "%s" "$PATH" | /usr/bin/awk -v RS=':' -v ORS=':' '!seen[$0]++' | /usr/bin/sed 's/:$//')
}

#-------------------------------------------------------------------------------
# Search Java Home
#-------------------------------------------------------------------------------
function javahome() {
    if [ "$1" = "" ]; then
        echo "Find java home"
        echo ""
        echo "Usage:"
        echo '  javahome <version>'
        echo "  e.g. javahome 1.8"
        return 0
    fi

    /usr/libexec/java_home -v $1
}

#-------------------------------------------------------------------------------
# Extract many types of compressed packages
#-------------------------------------------------------------------------------
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.bz2)  tar -jxvf "$1"                        ;;
      *.tar.gz)   tar -zxvf "$1"                        ;;
      *.bz2)      bunzip2 "$1"                          ;;
      *.dmg)      hdiutil mount "$1"                    ;;
      *.gz)       gunzip "$1"                           ;;
      *.tar)      tar -xvf "$1"                         ;;
      *.tbz2)     tar -jxvf "$1"                        ;;
      *.tgz)      tar -zxvf "$1"                        ;;
      *.zip)      unzip "$1"                            ;;
      *.ZIP)      unzip "$1"                            ;;
      *.pax)      cat "$1" | pax -r                     ;;
      *.pax.Z)    uncompress "$1" --stdout | pax -r     ;;
      *.Z)        uncompress "$1"                       ;;
      *) echo "'$1' cannot be extracted/mounted via extract()" ;;
    esac
  else
     echo "'$1' is not a valid file to extract"
  fi
}

#-------------------------------------------------------------------------------
# IP check
#-------------------------------------------------------------------------------
function myip() {
  curl -s "ifconfig.me"
}

#-------------------------------------------------------------------------------
# TCP LISTEN
#-------------------------------------------------------------------------------
function tcp() {
  lsof -iTCP -sTCP:LISTEN -n -P
}

#-------------------------------------------------------------------------------
# Echo with yellow color
#-------------------------------------------------------------------------------
function e() {
  if [ "$1" = "" ]; then
    echo "Print text in \033[0;33mYellow\033[0m color"
    echo ""
    echo "Usage:"
    echo '  e "<text>"'
    return 0;
  fi;

  local TEXT="$1"
  echo -e "\033[0;33m${TEXT}\033[0m"
}


# ref: https://www.lesstif.com/lpt/tail-bat-pipe-123338881.html
#-------------------------------------------------------------------------------
# tail 과 bat 명령을 pipe로 연결해서 더 편리하게 로그 파일 보기
#-------------------------------------------------------------------------------
function battail {
    tail -f "$@" | bat --style=plain --paging=never -l log
}

#-------------------------------------------------------------------------------
#  search google
#-------------------------------------------------------------------------------
function google() {
    open /Applications/Google\ Chrome.app/ "http://www.google.com/search?q= $1";
}

#-------------------------------------------------------------------------------
#  copy cat content
#-------------------------------------------------------------------------------
function catcp() {
  if [ "$1" = "" ]; then
    echo "Copy File to Clipboard"
    echo "Usage:"
    echo '  e "<file>"'
    return 0
  fi

  cat "$1" | pbcopy
}


#-------------------------------------------------------------------------------
#  fh - search in your command history and execute selected command
#  ref - https://sourabhbajaj.com/mac-setup/iTerm/fzf.html
#-------------------------------------------------------------------------------
function fh() {
  eval $( ([ -n "$ZSH_NAME" ] && fc -l 1 || history) | fzf +s --tac | sed 's/ *[0-9]* *//')
}

#-------------------------------------------------------------------------------
#  fd - cd to selected directory
#  ref - https://sourabhbajaj.com/mac-setup/iTerm/fzf.html
#-------------------------------------------------------------------------------
function fcd() {
  local dir
  dir=$(find ${1:-.} -path '*/\.*' -prune \
                  -o -type d -print 2> /dev/null | fzf +m) &&
  cd "$dir"
}

#-------------------------------------------------------------------------------
#  preview fzf
#  ref - https://github.com/junegunn/fzf
#-------------------------------------------------------------------------------
function fzfv() {
  fzf --preview '[[ $(file --mime {}) =~ binary ]] &&
                echo {} is a binary file ||
                (bat --style=plain --color=always {}) 2> /dev/null | head -500'
}

#-------------------------------------------------------------------------------
# FZF 자동완성 헬퍼 함수
#-------------------------------------------------------------------------------
# FD를 사용한 경로 자동완성 (파일 및 디렉토리)
_fzf_compgen_path() {
  fd --hidden --exclude .git . "$1"
}

# FD를 사용한 디렉토리 자동완성
_fzf_compgen_dir() {
  fd --type=d --hidden --exclude .git . "$1"
}

# FZF 명령어별 미리보기 커스터마이징
_fzf_comprun() {
  local command=$1
  shift

  case "$command" in
    cd)           fzf --preview 'eza --tree --color=always {} | head -200' "$@" ;;
    export|unset) fzf --preview "eval 'echo \$'{}" "$@" ;;
    ssh)          fzf --preview 'dig {}' "$@" ;;
    *)            fzf --preview "bat -n --color=always --line-range :500 {}" "$@" ;;
  esac
}


#-------------------------------------------------------------------------------
# yazi - 종료 시 현재 디렉토리를 셸에 동기화
#-------------------------------------------------------------------------------
function y() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
    yazi "$@" --cwd-file="$tmp"
    if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
        builtin cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}

# Claude
ccv() {
  local env_vars=(
    "ENABLE_BACKGROUND_TASKS=true"
    "FORCE_AUTO_BACKGROUND_TASKS=true"
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=true"
    "CLAUDE_CODE_ENABLE_UNIFIED_READ_TOOL=true"
    "CLAUDE_CODE_ENABLE_TASKS=true"
    "ENABLE_TOOL_SEARCH=1"
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=55000"
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000"
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
  )

  local claude_args=()

  if [ "$1" = "-y" ]; then
    claude_args+=("--dangerously-skip-permissions")
  elif [ "$1" = "-r" ]; then
    claude_args+=("--resume")
  elif [ "$1" = "-ry" ] || [ "$1" = "-yr" ]; then
    claude_args+=("--resume" "--dangerously-skip-permissions")
  fi
    env "${env_vars[@]}" claude "${claude_args[@]}"
}

# Claude with Ollama (로컬 모델)
cco() {
  local env_vars=(
    "ANTHROPIC_AUTH_TOKEN=ollama"
    "ANTHROPIC_BASE_URL=http://localhost:11434"
    "ENABLE_BACKGROUND_TASKS=true"
    "FORCE_AUTO_BACKGROUND_TASKS=true"
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=true"
    "CLAUDE_CODE_ENABLE_UNIFIED_READ_TOOL=true"
  )

  local claude_args=()
  local model="qwen3-coder:30b"  # 기본 모델

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -y) claude_args+=("--dangerously-skip-permissions"); shift ;;
      -r) claude_args+=("--resume"); shift ;;
      -ry|-yr) claude_args+=("--resume" "--dangerously-skip-permissions"); shift ;;
      -m) model="$2"; shift 2 ;;
      *) break ;;
    esac
  done

  env "${env_vars[@]}" claude --model "$model" "${claude_args[@]}"
}

# Gemini CLI
gem() {
  local gemini_args=()

  case "$1" in
    -y)
      gemini_args+=("--yolo")
      ;;
    -r)
      gemini_args+=("--resume")
      ;;
    -ry|-yr)
      gemini_args+=("--resume" "--yolo")
      ;;
  esac

  gemini "${gemini_args[@]}"
}

# Codex (workspace-write sandbox + on-request approval by default)
#   cdx         → full-auto (workspace-write sandbox, 작업 디렉토리 내 수정 허용)
#   cdx -y      → yolo (sandbox/승인 전부 해제, 위험)
#   cdx -r      → 최근 세션 이어서 시작 (full-auto)
#   cdx -ry     → 최근 세션 이어서 시작 (yolo)
#   cdx -ro     → read-only (코드 탐색/리뷰 전용, 수정 불가)
cdx() {
  local subcmd=""
  local codex_args=("--full-auto")

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -y)     codex_args=("--dangerously-bypass-approvals-and-sandbox"); shift ;;
      -r)     subcmd="resume"; codex_args=("--last" "--full-auto"); shift ;;
      -ry|-yr) subcmd="resume"; codex_args=("--last" "--dangerously-bypass-approvals-and-sandbox"); shift ;;
      -ro)    codex_args=("--sandbox" "read-only"); shift ;;
      *) break ;;
    esac
  done

  if [[ -n "$subcmd" ]]; then
    codex "$subcmd" "${codex_args[@]}" "$@"
  else
    codex "${codex_args[@]}" "$@"
  fi
}
