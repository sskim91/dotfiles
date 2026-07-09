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
    iconv -c -f EUC-KR -t UTF-8 "$1" >utf8_"$1"
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
    local pids
    pids=$(lsof -t -i :"$PORT" 2>/dev/null)
    if [ -z "$pids" ]; then
        echo -e "\033[0;31mNo process found on port ${PORT}\033[0m"
        return 1
    fi
    echo "$pids" | xargs kill
    echo -e "\033[0;33m${PORT} port has been closed\033[0m"
}

#-------------------------------------------------------------------------------
# Reload zsh
#-------------------------------------------------------------------------------
function rr() {
    source "$HOME/.zshrc"
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
# FortiGate SSL-VPN (openfortivpn) — background daemon via launchd
#
# The tunnel runs as a root LaunchDaemon so it survives closing the terminal
# and needs no per-connect sudo/VPN prompts. Auto-reconnect is handled natively
# by openfortivpn's `persistent` config key (not a shell loop).
#
# Secrets & endpoint live in /etc/openfortivpn/config (root:wheel 600), NOT in
# this tracked repo. The plist (no secrets) is copied to /Library/LaunchDaemons.
# One-time setup lives in the repo docs; see `vpn -h`.
#-------------------------------------------------------------------------------
function vpn() {
    local CONFIG="/etc/openfortivpn/config"
    local PLIST="/Library/LaunchDaemons/openfortivpn.plist"
    local SERVICE="system/openfortivpn"
    local LOG="/var/log/openfortivpn.log"

    case "$1" in
        up)
            [ -f "$PLIST" ] || { echo -e "\033[0;31mDaemon not installed: ${PLIST}\nRun the one-time setup (vpn -h).\033[0m"; return 1; }
            sudo launchctl bootstrap system "$PLIST" 2>/dev/null  # no-op if already loaded
            sudo launchctl kickstart -k "$SERVICE" \
                && echo -e "\033[0;33mVPN starting in background. Check: vpn status\033[0m"
            ;;
        down)
            sudo launchctl kill TERM "$SERVICE" \
                && echo -e "\033[0;33mVPN stopped.\033[0m"
            ;;
        status)
            if pgrep -x openfortivpn >/dev/null 2>&1; then
                echo -e "\033[0;32mVPN running.\033[0m"
                # openfortivpn on macOS uses a ppp interface (utun on some setups).
                ifconfig 2>/dev/null | grep -A2 -E "^(ppp|utun)[0-9]" | grep "inet " | sed 's/^/  /'
            else
                echo -e "\033[0;31mVPN not running.\033[0m"
            fi
            ;;
        log)
            [ -f "$LOG" ] && sudo tail -f "$LOG" || echo -e "\033[0;31mNo log yet: ${LOG}\033[0m"
            ;;
        fg)
            shift  # drop "fg" so extra args pass through cleanly
            # Foreground run — for first-time cert discovery / debugging.
            if [ -f "$CONFIG" ]; then
                sudo openfortivpn -c "$CONFIG" "$@"
            else
                sudo openfortivpn "$@"
            fi
            ;;
        -h|--help|"")
            echo "FortiGate SSL-VPN via openfortivpn (background launchd daemon)"
            echo ""
            echo "Usage:"
            echo "  vpn up        # start tunnel in background (one Mac-password prompt)"
            echo "  vpn down      # stop tunnel"
            echo "  vpn status    # is it connected? show utun IP"
            echo "  vpn log       # tail the daemon log"
            echo "  vpn fg        # run in foreground (setup/debug)"
            echo ""
            echo "One-time setup:"
            echo "  1. brew install openfortivpn"
            echo "  2. sudo openfortivpn <host>:443 -u <id>   # note the --trusted-cert digest, Ctrl-C"
            echo "  3. write /etc/openfortivpn/config (host/port/username/password/trusted-cert/persistent), chmod 600"
            echo "  4. sudo cp ~/.dotfiles/.config/openfortivpn/openfortivpn.plist /Library/LaunchDaemons/"
            echo "     sudo chown root:wheel /Library/LaunchDaemons/openfortivpn.plist"
            echo "     sudo launchctl bootstrap system /Library/LaunchDaemons/openfortivpn.plist"
            echo "  5. vpn up"
            ;;
        *)
            echo -e "\033[0;31mUnknown: vpn $1  (try: vpn -h)\033[0m"; return 1 ;;
    esac
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

#-------------------------------------------------------------------------------
# Update all: Homebrew + Claude Code + Antigravity CLI + Codex CLI
#-------------------------------------------------------------------------------
function update() {
    brew update && brew upgrade -y && brew cleanup
    echo "==> Updating Claude Code..."
    claude update
    if (( $+commands[agy] )); then
        echo "==> Updating Antigravity CLI..."
        agy update
    fi
    if (( $+commands[codex] )); then
        echo "==> Updating Codex CLI..."
        codex update
    fi
    echo "==> Updating Claude Code plugins..."
    ccpu
}

# Claude Code plugin update (on-demand replacement for startup autoUpdate)
# autoUpdate가 startup마다 git pull을 돌려 로드 에러를 유발하므로 settings.json에서 껐다.
# 대신 원할 때 이 함수로 marketplace + 설치된 플러그인을 일괄 갱신한다.
# scope(project/user)와 projectPath는 installed_plugins.json에서 읽어 정확히 지정한다.
function ccpu() {
    local ip="$HOME/.claude/plugins/installed_plugins.json"
    echo "==> Refreshing marketplaces..."
    claude plugin marketplace update
    echo "==> Updating installed plugins..."
    local name scope ppath
    jq -r '.plugins | to_entries[] | .key as $n | .value[] | [$n, .scope, (.projectPath // "")] | @tsv' "$ip" 2>/dev/null | \
    while IFS=$'\t' read -r name scope ppath; do
        echo "  -> $name ($scope)"
        if [[ "$scope" == "project" && -n "$ppath" ]]; then
            (cd "$ppath" && claude plugin update "$name" --scope project) 2>&1 | sed 's/^/     /'
        else
            claude plugin update "$name" --scope "$scope" 2>&1 | sed 's/^/     /'
        fi
    done
    echo "==> Done. Restart Claude Code to apply."
}

# Claude
ccv() {
  local claude_args=(--fallback-model claude-sonnet-4-6)

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -y)  claude_args+=("--dangerously-skip-permissions"); shift ;;
      -d)  claude_args+=("--permission-mode" "dontAsk"); shift ;;
      -r)  claude_args+=("--resume"); shift ;;
      -ry|-yr) claude_args+=("--resume" "--dangerously-skip-permissions"); shift ;;
      -rd|-dr) claude_args+=("--resume" "--permission-mode" "dontAsk"); shift ;;
      *)   break ;;
    esac
  done

  claude "${claude_args[@]}" "$@"
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

  env "${env_vars[@]}" claude --model "$model" "${claude_args[@]}" "$@"
}

# Antigravity CLI
agy() {
  if (( ! $+commands[agy] )); then
    print -u2 "Antigravity CLI is not installed. Run: curl -fsSL https://antigravity.google/cli/install.sh | bash"
    return 127
  fi

  local agy_args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -y)  agy_args+=("--dangerously-skip-permissions"); shift ;;
      -s)  agy_args+=("--sandbox"); shift ;;
      -r)  agy_args+=("--continue"); shift ;;
      -ry|-yr) agy_args+=("--continue" "--dangerously-skip-permissions"); shift ;;
      *)   break ;;
    esac
  done

  command agy "${agy_args[@]}" "$@"
}

# Gemini CLI compatibility wrapper (muscle-memory alias for `agy`).
# Gemini CLI stopped serving free/Pro/Ultra tiers on 2026-06-18 and was
# superseded by Antigravity CLI, so `gem` now always routes to `agy`.
gem() {
  if (( ! $+commands[agy] )); then
    print -u2 "Gemini CLI was superseded by Antigravity CLI on 2026-06-18."
    print -u2 "Install it with: curl -fsSL https://antigravity.google/cli/install.sh | bash"
    return 127
  fi

  agy "$@"
}

# Codex (workspace-write sandbox + on-request approval by default)
#
# 기본값:
#   - 작업 디렉토리 안에서는 파일 수정 가능: --sandbox workspace-write
#   - 명령 실행 승인은 Codex가 필요하다고 판단할 때만 요청: --ask-for-approval on-request
#
# Resume 동작:
#   - codex resume은 기본적으로 "현재 cwd의 이전 interactive session 목록" picker를 띄운다.
#   - --all을 붙이면 cwd 필터를 해제해서 전체 세션 picker를 띄운다.
#   - --last를 붙이면 picker 없이 가장 최근 세션으로 바로 들어간다.
#
# Shorthand:
#   cdx         → 새 Codex 세션 시작 (workspace-write + on-request approval)
#   cdx -y      → 새 Codex 세션 시작, yolo mode (sandbox/승인 전부 해제, 위험)
#   cdx -r      → 현재 디렉토리의 이전 세션 목록 picker에서 선택해 재개
#   cdx -ra     → 전체 이전 세션 목록 picker에서 선택해 재개 (cwd 필터 해제)
#   cdx -rl     → 현재 디렉토리의 가장 최근 세션으로 바로 재개
#   cdx -ry     → 현재 디렉토리의 이전 세션 목록 picker에서 선택해 재개, yolo mode
#   cdx -rly    → 현재 디렉토리의 가장 최근 세션으로 바로 재개, yolo mode
#   cdx -ro     → read-only mode로 새 세션 시작 (코드 탐색/리뷰 전용, 수정 불가)
cdx() {
  local subcmd=""
  local codex_args=("--sandbox" "workspace-write" "--ask-for-approval" "on-request")

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -y)     codex_args=("--dangerously-bypass-approvals-and-sandbox"); shift ;;
      -r)     subcmd="resume"; codex_args=("--sandbox" "workspace-write" "--ask-for-approval" "on-request"); shift ;;
      -ra|-ar) subcmd="resume"; codex_args=("--all" "--sandbox" "workspace-write" "--ask-for-approval" "on-request"); shift ;;
      -rl|-lr) subcmd="resume"; codex_args=("--last" "--sandbox" "workspace-write" "--ask-for-approval" "on-request"); shift ;;
      -ry|-yr) subcmd="resume"; codex_args=("--dangerously-bypass-approvals-and-sandbox"); shift ;;
      -rly|-ryl|-lry|-lyr|-yrl|-ylr) subcmd="resume"; codex_args=("--last" "--dangerously-bypass-approvals-and-sandbox"); shift ;;
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

#-------------------------------------------------------------------------------
# Fetch DESIGN.md from awesome-design-md repo
# Usage: design <site-name>   # e.g. design linear.app
#        design --list         # list available sites
#-------------------------------------------------------------------------------
function design() {
    local repo="VoltAgent/awesome-design-md"
    local base="https://raw.githubusercontent.com/${repo}/main/design-md"

    if [[ "$1" == "--list" ]]; then
        gh api "repos/${repo}/contents/design-md" --jq '.[].name' | sort
        return
    fi

    [[ -z "$1" ]] && { echo "Usage: design <site-name> | design --list"; return 1; }

    curl -sL "${base}/$1/DESIGN.md" -o DESIGN.md \
        && echo "✓ DESIGN.md ($1) → $(pwd)/DESIGN.md" \
        || echo "✗ Failed to fetch DESIGN.md for '$1'"
}
