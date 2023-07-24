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
    man -t "${1}" | open -f -a /System/Applications/Preview.app
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
    tail -f "$@" | bat -plaintext --paging=never -l log
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
