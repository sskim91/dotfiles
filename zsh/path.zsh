# TLDR - 명령어 간단 설명 도구
export TLDR_AUTO_UPDATE_DISABLED="FALSE"

# Neovim - 기본 에디터 설정 (Apple Silicon 호환)
export EDITOR="$(which nvim 2>/dev/null || echo 'nvim')"

# Python 버전 관리는 mise를 사용 (pyenv 제거됨)

# Maven - Java 빌드 도구
# Apple Silicon과 Intel Mac 모두 지원
if [ -d "/opt/homebrew/opt/maven/bin" ]; then
  export PATH="/opt/homebrew/opt/maven/bin:$PATH"  # Apple Silicon
elif [ -d "/usr/local/opt/maven/bin" ]; then
  export PATH="/usr/local/opt/maven/bin:$PATH"     # Intel Mac
fi

# Bat - 향상된 cat 명령어 (매뉴얼 페이지에도 사용)
export MANPAGER="sh -c 'col -bx | bat -l man -p'"

# Poetry - Python 패키지 관리 도구
export PATH="$HOME/.local/bin:$PATH"

# FZF + FD - 향상된 파일 검색 도구
export FZF_DEFAULT_COMMAND="fd --hidden --strip-cwd-prefix --exclude .git --exclude bower_components --exclude node_modules"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="fd --type=d --hidden --strip-cwd-prefix --exclude .git --exclude bower_components --exclude node_modules"

# FZF 미리보기 옵션 설정
export FZF_CTRL_T_OPTS="--preview 'bat -n --color=always --line-range :500 {}'"
export FZF_ALT_C_OPTS="--preview 'eza --tree --color=always {} | head -200'"

# FZF 관련 함수들은 functions.zsh에 정의됨

# ngrok - 로컬 서버 터널링 도구
if command -v ngrok &>/dev/null; then
  eval "$(ngrok completion)"
fi

# PostgreSQL 클라이언트 도구 (Apple Silicon 경로)
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# ============================================================================
# Claude Hooks Configuration
# ============================================================================
#
# 📌 동작 원리
# -------------
# Hook은 Claude Code가 파일을 Write/Edit할 때 자동 실행됩니다:
# - check hook:  린팅, 타입 체크 등 (pre/post Write|Edit|MultiEdit)
# - review hook: AI 코드 리뷰 (post Write|Edit|MultiEdit only)
#
# 🔧 설정 방법
# ------------
# ENABLE_XXX=0/1 → 개별 도구 활성화 여부
#
# 📝 현재 상태: 모든 도구 비활성화 (필요한 것만 선택적으로 1로 변경)
# ============================================================================

# ----------------------------------------------------------------------------
# JavaScript 개발 도구 (javascript-check.sh)
# ----------------------------------------------------------------------------
export ENABLE_ESLINT=0               # ESLint - JavaScript 린팅
export ENABLE_OXC=0                  # OXC - Rust 기반 고속 린터
export ENABLE_STANDARD=0             # Standard JS - 제로 설정 스타일

# ----------------------------------------------------------------------------
# TypeScript 개발 도구 (typescript-check.sh)
# ----------------------------------------------------------------------------
export ENABLE_TSC=0                  # TypeScript Compiler - 타입 체크

# ----------------------------------------------------------------------------
# Python 개발 도구 (python-check.sh)
# ----------------------------------------------------------------------------
export ENABLE_RUFF=0                 # Ruff - 린터
export ENABLE_TY=0                   # Typos - 오타 검사
export ENABLE_PYREFLY=0              # Pyrefly - 정적 분석

# ----------------------------------------------------------------------------
# Java 개발 도구 (java-check.sh)
# ----------------------------------------------------------------------------
export ENABLE_CHECKSTYLE=0           # Checkstyle - 스타일 체커
export ENABLE_SPOTBUGS=0             # SpotBugs - 버그 검출
export ENABLE_PMD=0                  # PMD - 코드 분석

# ----------------------------------------------------------------------------
# Code Review (모든 언어 공통 - *-review.sh)
# ----------------------------------------------------------------------------
export ENABLE_GEMINI_REVIEW=0        # Gemini AI 코드 리뷰 (.py, .java, .ts, .js)
export ENABLE_TIL_REVIEW=1           # Gemini TIL 문서 리뷰 (~/dev/TIL/*.md)
