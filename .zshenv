# ~/.zshenv - 모든 zsh 실행에서 읽히는 유일한 파일
#
# zsh 초기화 순서: .zshenv -> (login) .zprofile -> (interactive) .zshrc
# `ssh host <command>` 는 login 도 interactive 도 아니라서 .zprofile / .zshrc 가
# 둘 다 실행되지 않고, /etc/zprofile 의 path_helper 도 돌지 않는다. 그 결과
# /opt/homebrew/bin 이 PATH 에서 빠져 원격 명령이 brew 로 설치한 도구를 못 찾는다.
#
# 대표 증상: mosh 클라이언트(iPad Moshi 등)가 `ssh host -- mosh-server new ...`
# 를 실행하면서 "mosh-server not found" 로 실패한다.
#
# 여기에는 PATH 최소 보정만 둔다. 로그인 설정은 .zprofile, 대화형 설정은 .zshrc.

if [[ -x /opt/homebrew/bin/brew && ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
  export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
fi
