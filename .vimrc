syntax on

highlight Comment term=bold cterm=bold ctermfg=86
highlight LineNr term=bold cterm=NONE ctermfg=Grey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE
set ruler                               " 화면 오른쪽 아래에 커서 위치 표시
set showcmd                             " 화면 오른쪽 아래에 입력되는 명령키를 표시
set expandtab                           " tab을 space로 인식
set tabstop=4                           " 한번의 tab을 4칸으로 인식
set softtabstop=4                       " tab 간격을 공백문자로 변환하며 삭제할 때 탭 간격만큼 삭제하지 않고, 마치 탭 문자를 삭제하는 것처럼 설정하며 4칸 단위로 삭제함
set shiftwidth=4                        " >>, << 사용시 들여쓰기 4칸으로 사용
set backspace=indent,eol,start          " 백스페이스로 인덴트, EOL, 앞글자 삭제 가능
set copyindent                          " 새 행이 기존 행의 들여 쓰기에 사용 된 문자를 복사하여 사용
set autoindent                          " 자동 들여쓰기를 사용
set smarttab                            " 앞에 space가 있는 곳에서 tab을 누르면 공백을 지워주고 탭만 들어감
set incsearch                           " /를 입력후 찾는 글자를 입력하는 순간 찾은 글자를 바료 표시
set nowrapscan                          " 검색할 때 문서의 끝에서 다시 처음으로 돌아가지 않음
set hlsearch                            " 검색어 강조
" 검색어의 배경색 설정
hi search ctermbg=3
set history=1000                        " 히스토리 개수 1000 설정
set undolevels=1000                     " undo 할 수 있는 히스토리 개수 1000 설정
set wrap                                " 텍스트 표시 방법을 설정(창 너비보다 길때 다음행에 표시)
set encoding=utf-8                      " vim 안에서 사용되는 문자의 인코딩 utf-8로 설정
set fileencodings=utf-8,cp949           " 파일 저장 인코딩 (cp949 가 ui message 한글이 깨지지 않게함)
set hidden                              " Controversial
set wildmenu                            " 명령 라인 완성이 향상된 기능으로 작동 (tab 눌렀을 때 작동)
set wildmode=list:longest               " 매칭되는 단어 목록을 리스트 형식으로 보여줌
set number                              " 라인 넘버 표시
set undofile                            " 자동으로 실행 취소(undo) 기록을 실행 취소 파일에 저장함
set undodir=~/.vim/undodir              " undo 파일을 한 곳에 모아서 관리
set ignorecase                          " 검색 시 대소문자를 무시함
set smartcase                           " 검색 문자열이 모두 소문자이면 대소문자를 구분하지 않고, 대문자가 하나라도 있으면 대소문자 구분
set gdefault                            " '찾아바꾸기' 할때 subtitute 플래그 'g'가 기본설정됨
set cursorline                          " 현재 커서가 위치한 행의 라인을 표시
set nojoinspaces                        " J 명령어로 줄을 이어 붙일 때 마침표 뒤에 한칸만 띄워 씀
