-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua

local opt = vim.opt

-- Migrated from previous .vimrc / init.vim settings
opt.tabstop = 4                    -- tab을 4칸으로 인식
opt.softtabstop = 4                -- 탭 간격 4칸 단위
opt.shiftwidth = 4                 -- >>, << 사용시 들여쓰기 4칸
opt.expandtab = true               -- tab을 space로 변환
opt.copyindent = true              -- 새 행이 기존 행의 들여쓰기 복사
opt.autoindent = true              -- 자동 들여쓰기

opt.wrap = true                    -- 창 너비보다 길때 다음행에 표시
opt.history = 1000                 -- 히스토리 개수 1000
opt.undolevels = 1000              -- undo 히스토리 개수 1000
opt.undofile = true                -- undo 기록 파일에 저장

opt.ignorecase = true              -- 검색 시 대소문자 무시
opt.smartcase = true               -- 대문자 포함시 대소문자 구분
opt.hlsearch = true                -- 검색어 강조
opt.incsearch = true               -- 검색 즉시 표시
opt.wrapscan = false               -- 문서 끝에서 처음으로 돌아가지 않음

opt.cursorline = true              -- 현재 커서 행 표시
opt.number = true                  -- 라인 넘버 표시
opt.relativenumber = true          -- 상대 라인 넘버 (LazyVim 기본)

opt.encoding = "utf-8"             -- 인코딩 utf-8
opt.fileencodings = "utf-8,cp949"  -- 파일 저장 인코딩

opt.hidden = true                  -- 버퍼 숨기기 허용
opt.wildmenu = true                -- 명령 라인 완성 향상
opt.wildmode = "list:longest"      -- 매칭 단어 리스트 표시

opt.backspace = "indent,eol,start" -- 백스페이스 동작
opt.joinspaces = false             -- J 명령시 한칸만 띄움
