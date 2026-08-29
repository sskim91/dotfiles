# API Keys - .env.local에서 로드 (gitignored)
[[ -f "$DOTFILES/.env.local" ]] && source "$DOTFILES/.env.local"

# 관리자 API 설정 - .env.admin-api에서 로드 (gitignored, 비번 제외)
[[ -f "$DOTFILES/.env.admin-api" ]] && source "$DOTFILES/.env.admin-api"

# TLDR - 명령어 간단 설명 도구
export TLDR_AUTO_UPDATE_DISABLED="FALSE"

# Neovim - 기본 에디터 설정 (Apple Silicon 호환)
export EDITOR="$(which nvim 2>/dev/null || echo 'nvim')"

# Python 버전 관리는 mise를 사용 (pyenv 제거됨)

# Maven - Java 빌드 도구
if [ -d "/opt/homebrew/opt/maven/bin" ]; then
  export PATH="/opt/homebrew/opt/maven/bin:$PATH"
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
# - check hook:  린팅 등 (post Write|Edit)
#
# 🔧 설정 방법
# ------------
# ENABLE_XXX=0/1 → 개별 도구 활성화 여부
#
# 📝 현재 상태: Ruff(ENABLE_RUFF)·TIL review(ENABLE_TIL_REVIEW)만 기본 활성.
#    2026-07 훅 감사에서 영구 비활성이던 JS/TS/Java 체커(스크립트 포함)를 제거 —
#    새 언어 지원 시 {language}-check.sh + ENABLE_* 토글 + dispatcher 라우트를 함께 추가
# ============================================================================

# ----------------------------------------------------------------------------
# Python 개발 도구 (python-check.sh)
# ----------------------------------------------------------------------------
export ENABLE_RUFF=1                 # Ruff - 린터

# ----------------------------------------------------------------------------
# Code Review (모든 언어 공통 - *-review.sh)
# ----------------------------------------------------------------------------
export ENABLE_TIL_REVIEW=1           # Antigravity TIL 문서 리뷰 (~/dev/TIL/*.md)
export ENABLE_VAULT_LINKER=0         # Obsidian vault 노트 자동 링킹 제안
export SKIP_TRANSLATED_REVIEW=1      # 번역 문서는 TIL 리뷰 스킵

# ----------------------------------------------------------------------------
# Commit 보안 게이트 (pre-commit-gate.sh — Claude/Codex 공통)
# ----------------------------------------------------------------------------
export ENABLE_ENV_FILE_CHECK=0       # .env류/구조화 시크릿 파일 커밋 차단 (check-env-files.sh)
export ENABLE_SECRET_SCAN=0          # 코드 내 하드코딩 시크릿 패턴 차단 (check-hardcoded-secrets.sh)
# check-sensitive-files.sh(id_rsa·.pem 등 키 파일 차단)는 토글 없이 상시 활성

# ----------------------------------------------------------------------------
# Claude Code — 앱 레벨 설정
# (settings.json env 블록은 subprocess에만 전달; 앱 자체 로직엔 셸 export 필요)
# ----------------------------------------------------------------------------
# autocompact: context window의 몇 % 시점에 자동 압축을 발동할지 (기본값 ~83%)
# 낮을수록 일찍 압축 → 더 자주 / 높을수록 늦게 압축 → 맥락 보존
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70

# ENABLE_OMC_COMPANION_SYNC는 2026-08-29에 제거됐다. CLAUDE-omc.md 동기화가
# SessionStart 훅이 아니라 ccpu(플러그인 업데이트 함수)와 install.sh에서 명시적으로
# 호출되므로, 켜고 끌 상시 동작 자체가 없다.
