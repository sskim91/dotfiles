# LazyVim Cheatsheet

LazyVim 설정 가이드 및 자주 사용하는 키맵 정리.

## 디렉토리 구조

```
config/nvim/
├── init.lua              # 진입점 (lazy.nvim 부트스트랩)
├── lazyvim.json          # 활성화된 extras 목록
├── lazy-lock.json        # 플러그인 버전 잠금 파일
└── lua/
    ├── config/           # 설정 파일 (자동 로드)
    │   ├── options.lua   # vim 옵션 설정
    │   ├── keymaps.lua   # 커스텀 키 매핑
    │   └── autocmds.lua  # 자동 명령
    └── plugins/          # 커스텀 플러그인 설정
        ├── colorscheme.lua   # 테마 설정 (catppuccin)
        └── editor.lua        # 에디터 확장 설정
```

## 기존 Vim과의 차이점

| 항목 | 이전 (vim-plug 등) | LazyVim |
|------|-------------------|---------|
| 플러그인 관리자 | vim-plug, packer | **lazy.nvim** (지연 로딩) |
| 리더 키 | 다양 | **Space** |
| 로컬 리더 | - | **\\** (백슬래시) |
| 설정 언어 | VimScript | **Lua** |
| LSP 설정 | 수동 설치/설정 | **자동** (Mason) |
| 파일 탐색기 | NERDTree 등 | **Neo-tree** |
| 퍼지 파인더 | fzf.vim 등 | **Telescope** |

## 활성화된 언어 지원

`lazyvim.json`에서 관리되며, `:LazyExtras`로 추가/제거 가능.

| 언어 | LSP | 린터/포매터 |
|------|-----|------------|
| Python | pyright | ruff |
| TypeScript | tsserver | eslint |
| Java | jdtls | - |
| JSON | jsonls | - |
| Markdown | - | markdownlint |

## 핵심 키맵

### 리더 키 (Space)

`<leader>`는 **Space** 키. 누르고 잠시 기다리면 which-key가 사용 가능한 키 표시.

```
<leader>e      파일 탐색기 (Neo-tree) 토글
<leader>E      파일 탐색기 (현재 파일 위치)

<leader>ff     파일 찾기
<leader>fg     텍스트 검색 (grep)
<leader>fb     버퍼 목록
<leader>fr     최근 파일
<leader>fc     설정 파일 찾기

<leader>w      저장 (커스텀)
<leader>qq     Neovim 종료

<leader>l      Lazy 플러그인 관리자
<leader>cm     Mason (LSP 설치기)

<leader>/      현재 버퍼에서 검색
<leader>sg     전체 프로젝트 grep
```

### 윈도우 이동

```
Ctrl + h       왼쪽 윈도우로
Ctrl + j       아래 윈도우로
Ctrl + k       위 윈도우로
Ctrl + l       오른쪽 윈도우로
```

### 버퍼 탐색

```
<S-h>          이전 버퍼 (Shift + h)
<S-l>          다음 버퍼 (Shift + l)
<leader>bd     버퍼 삭제
<leader>bo     다른 버퍼 모두 삭제
```

### 코드 편집

```
gc             주석 토글 (visual 모드에서도 동작)
gcc            현재 줄 주석 토글

J              visual 모드에서 줄 아래로 이동 (커스텀)
K              visual 모드에서 줄 위로 이동 (커스텀)

Ctrl + d       반 페이지 아래 (커서 중앙 유지)
Ctrl + u       반 페이지 위 (커서 중앙 유지)
```

### LSP (코드 인텔리전스)

```
gd             정의로 이동 (Go to Definition)
gr             참조 찾기 (References)
gI             구현으로 이동 (Implementation)
gy             타입 정의로 이동

K              호버 문서 표시
<leader>ca     코드 액션 (Code Action)
<leader>cr     이름 변경 (Rename)
<leader>cf     포맷팅 (Format)

]d             다음 진단 (diagnostic)
[d             이전 진단
<leader>cd     현재 줄 진단 표시
```

### Git

```
]h             다음 hunk (변경 블록)
[h             이전 hunk
<leader>hs     hunk 스테이지
<leader>hr     hunk 리셋
<leader>gb     현재 줄 blame 표시
<leader>gB     blame (전체 파일)
```

### 검색

```
n              다음 검색 결과 (커서 중앙 유지)
N              이전 검색 결과 (커서 중앙 유지)
<Esc>          검색 하이라이트 제거
```

## 주요 명령어

```vim
:Lazy              플러그인 관리 UI
                   - i: 설치
                   - u: 업데이트
                   - c: 정리 (사용하지 않는 플러그인 제거)
                   - s: 동기화

:LazyExtras        언어/기능 extras 활성화/비활성화
                   - x: 토글

:Mason             LSP/포매터/린터 설치 관리
                   - i: 설치
                   - u: 업데이트
                   - X: 제거

:Telescope         검색 기능 모음
:checkhealth       설정 상태 확인
:LspInfo           현재 LSP 상태 확인
```

## 커스텀 설정 (options.lua)

현재 적용된 주요 설정:

```lua
-- 탭/들여쓰기
tabstop = 4           -- 탭 4칸
shiftwidth = 4        -- 들여쓰기 4칸
expandtab = true      -- 탭을 스페이스로

-- 검색
ignorecase = true     -- 대소문자 무시
smartcase = true      -- 대문자 포함시 구분
wrapscan = false      -- 끝에서 처음으로 안 돌아감

-- UI
number = true         -- 줄 번호
relativenumber = true -- 상대 줄 번호
cursorline = true     -- 현재 줄 강조
wrap = true           -- 긴 줄 줄바꿈

-- 편집
undofile = true       -- undo 기록 저장
undolevels = 1000     -- undo 히스토리 1000개
```

## 테마

기본 테마: **Catppuccin Mocha**

사용 가능한 테마:
- `catppuccin` (mocha, macchiato, frappe, latte)
- `tokyonight`
- `dracula`

테마 변경: `lua/plugins/colorscheme.lua`에서 수정

```lua
opts = {
  colorscheme = "catppuccin",  -- 원하는 테마로 변경
},
```

## 내장 플러그인

| 플러그인 | 용도 |
|---------|------|
| neo-tree | 파일 탐색기 |
| telescope | 퍼지 파인더 |
| treesitter | 구문 강조 |
| gitsigns | Git 변경 표시 |
| which-key | 키맵 도움말 |
| mini.pairs | 자동 괄호 |
| mini.comment | 주석 토글 |
| lualine | 상태바 |
| bufferline | 버퍼 탭 |
| indent-blankline | 들여쓰기 가이드 |
| noice | 향상된 UI |
| notify | 알림 |

## 문제 해결

### 플러그인 동기화
```bash
nvim --headless "+Lazy! sync" +qa
```

### 건강 상태 확인
```vim
:checkhealth
```

### LSP가 동작하지 않을 때
1. `:LspInfo`로 상태 확인
2. `:Mason`에서 해당 LSP 설치 확인
3. `:LspRestart`로 재시작

### 설정 초기화
```bash
# 캐시 삭제
rm -rf ~/.local/share/nvim
rm -rf ~/.local/state/nvim
rm -rf ~/.cache/nvim
```
