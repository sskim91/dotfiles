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
    man -t "${1}" | open -f -a /Applications/Preview.app/
}

#-------------------------------------------------------------------------------
# Convert EUC-KR to UTF-8
#-------------------------------------------------------------------------------
function enc() {
    iconv -c -f EUC-KR -t UTF-8 $1 >utf8_"$1"
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

# ref: https://www.lesstif.com/lpt/tail-bat-pipe-123338881.html
#-------------------------------------------------------------------------------
# tail 과 bat 명령을 pipe로 연결해서 더 편리하게 로그 파일 보기
#-------------------------------------------------------------------------------
function battail {
    tail -f "$@" | bat --paging=never -l log
}
