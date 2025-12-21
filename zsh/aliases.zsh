# 디렉토리 이동 단축키
alias cd..="cd .."
alias ..='cd ..'
alias ...='cd ../../'
alias ....='cd ../../../'
alias .....='cd ../../../../'
alias .2='cd ../../'
alias .3='cd ../../../'
alias .4='cd ../../../../'
alias .5='cd ../../../../../'

# 자주 사용하는 디렉토리 바로가기
alias dl="cd ~/Downloads"
alias desk="cd ~/Desktop"
alias dot="cd ~/.dotfiles"
alias dev="cd ~/dev"
alias til="cd ~/dev/TIL"
alias comp="cd ~/company-src"

# 향상된 도구로 대체
alias vim="nvim"         # Neovim 사용
alias vi="nvim"
alias vimdiff="nvim -d"  # diff 모드
alias cat="bat"          # 문법 강조 지원

# 시스템 모니터링 및 설정
alias top="htop"                  # 향상된 프로세스 모니터
alias zshconfig="vim ~/.zshrc"    # zsh 설정 편집
alias ohmyzsh="vim ~/.oh-my-zsh"  # Oh My Zsh 편집

# 안전한 파일 조작 (확인 프롬프트 표시)
alias rm="rm-safely"              # 휴지통으로 이동 (복구 가능)
alias rmf="/bin/rm -i"            # 진짜 삭제 (확인 있음)
alias RMF="/bin/rm -rf"           # 강제 삭제 (주의!)
alias cp='cp -i'
alias ln='ln -i'
alias mv='mv -i'

# Homebrew 관리
alias update="brew update && brew upgrade && brew cleanup"  # 패키지 업데이트
alias services="brew services"                              # 서비스 관리

# eza를 사용한 향상된 파일 목록 표시
alias ll="eza --color-scale all --icons --time-style long-iso -lhbg --git"   # 자세한 목록 + Git 상태
alias la="eza --color-scale all --icons --time-style long-iso -lahbg --git"  # 숨김 파일 포함
alias ls="eza"                                                                # 기본 목록
alias lt="eza --tree --level=2"                                              # 트리 뷰 (2단계)

# 화면 정리
alias c="clear"

# 명령어 기록 검색
alias h="history"
alias hs="history | grep"       # 히스토리 검색
alias hsi="history -i | grep"   # 타임스탬프 포함 검색

# 날짜와 시간
alias d='date +%F'                  # YYYY-MM-DD 형식
alias now='date +"%T"'              # HH:MM:SS 형식
alias nowtime=now
alias nowdate='date +"%Y-%m-%d"'    # 날짜만

# 네트워크 도구
alias ping='ping -c 5'  # 5회 핑 후 중지

# HTTP 헤더만 표시
alias header='curl -I'

# 디스크 사용량
alias df='duf'      # 향상된 디스크 사용량 표시
alias du='du -ch'   # 사람이 읽기 쉬운 형식

# 별칭 검색
alias ag="alias | grep "  # 특정 별칭 찾기

# Serena MCP - AI 코드 분석 도구
alias add-serena="bash ~/.dotfiles/add-serena-uvx.sh"

# 터미널 이미지 뷰어 (Kitty 프로토콜)
alias img='kitten icat'                      # 이미지 보기 (기본 중앙)
alias imgl='kitten icat --align left'        # 왼쪽 정렬
alias imgclear='kitten icat --clear'         # 화면 이미지 지우기

