#!/bin/bash

# vault-maintenance.sh — Cron으로 실행되는 Obsidian vault 자동 유지보수
# 매주 일요일 새벽 2시 실행 권장: 0 2 * * 0 ~/.dotfiles/scripts/vault-maintenance.sh
#
# 동작:
# Phase 1: vault-linter 기본 (고아 노트, 깨진 링크, 태그 비일관성 점검)
# Phase 2: vault-linter --semantic (임베딩 기반 유사도 → 관련 노트 자동 연결)
# Phase 3: vault-linter --index (카탈로그 vault-index.md + 유지보수 로그 vault-log.md)
# 결과를 00.Inbox/Vault-Lint-Report-{date}.md / vault-index.md / vault-log.md에 저장
#
# Max 구독 모델 — 추가 비용 없음

LOG_DIR="$HOME/.local/log/vault-maintenance"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/vault-maintenance-${DATE}.log"

echo "=== Vault Maintenance Start: $(date) ===" >> "$LOG_FILE"

# Phase 1: 기본 vault-linter
echo "--- Phase 1: Basic Lint ---" >> "$LOG_FILE"
/Users/sskim/.local/bin/claude -p \
  "/vault-linter" \
  --permission-mode bypassPermissions \
  --allowedTools "Read,Grep,Glob,Write,Bash,Skill" \
  >> "$LOG_FILE" 2>&1

PHASE1_EXIT=$?
echo "--- Phase 1 Exit: $PHASE1_EXIT ---" >> "$LOG_FILE"

# Phase 2: semantic linking
echo "--- Phase 2: Semantic Linking ---" >> "$LOG_FILE"
/Users/sskim/.local/bin/claude -p \
  "/vault-linter --semantic" \
  --permission-mode bypassPermissions \
  --allowedTools "Read,Grep,Glob,Write,Edit,Bash,Skill" \
  >> "$LOG_FILE" 2>&1

PHASE2_EXIT=$?
echo "--- Phase 2 Exit: $PHASE2_EXIT ---" >> "$LOG_FILE"

# Phase 3: index + log
echo "--- Phase 3: Index + Log ---" >> "$LOG_FILE"
/Users/sskim/.local/bin/claude -p \
  "/vault-linter --index" \
  --permission-mode bypassPermissions \
  --allowedTools "Read,Grep,Glob,Write,Edit,Bash,Skill" \
  >> "$LOG_FILE" 2>&1

PHASE3_EXIT=$?
echo "--- Phase 3 Exit: $PHASE3_EXIT ---" >> "$LOG_FILE"

echo "=== Vault Maintenance End: $(date) ===" >> "$LOG_FILE"

# 실패 시 알림 (macOS notification)
if [[ $PHASE1_EXIT -ne 0 || $PHASE2_EXIT -ne 0 || $PHASE3_EXIT -ne 0 ]]; then
  osascript -e "display notification \"Vault maintenance failed (lint:$PHASE1_EXIT, semantic:$PHASE2_EXIT, index:$PHASE3_EXIT). Check $LOG_FILE\" with title \"Vault Maintenance\""
fi
