#!/bin/bash

# vault-maintenance.sh — Cron으로 실행되는 Obsidian vault 자동 유지보수
# 매주 일요일 새벽 2시 실행 권장: 0 2 * * 0 ~/.dotfiles/scripts/vault-maintenance.sh
#
# 동작:
# 1. vault-linter 실행 (고아 노트, 깨진 링크, 태그 비일관성 점검)
# 2. 결과를 00.Inbox/Vault-Lint-Report-{date}.md에 저장
#
# Max 구독 모델 — 추가 비용 없음

LOG_DIR="$HOME/.local/log/vault-maintenance"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/vault-maintenance-${DATE}.log"

echo "=== Vault Maintenance Start: $(date) ===" >> "$LOG_FILE"

# Claude Code 비대화형 실행 (Max 구독)
# --permission-mode bypassPermissions: plan mode 승인 대기 방지
/Users/sskim/.local/bin/claude -p \
  "/vault-linter" \
  --permission-mode bypassPermissions \
  --allowedTools "Read,Grep,Glob,Write,Bash,Skill" \
  >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
echo "=== Vault Maintenance End: $(date), Exit: $EXIT_CODE ===" >> "$LOG_FILE"

# 실패 시 알림 (macOS notification)
if [[ $EXIT_CODE -ne 0 ]]; then
  osascript -e "display notification \"Vault maintenance failed (exit $EXIT_CODE). Check $LOG_FILE\" with title \"Vault Maintenance\""
fi
