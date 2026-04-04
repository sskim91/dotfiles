#!/bin/bash

# vault-linker.sh — PostToolUse hook
# Obsidian vault에 .md 파일 생성/수정 시 vault 노트 목록과 새 노트 요약을
# Claude에게 전달하여 의미적 링킹을 유도한다.
# ENABLE_VAULT_LINKER=1 로 활성화

ENABLE_VAULT_LINKER=${ENABLE_VAULT_LINKER:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# .md 파일이 아니면 스킵
if [[ ! "$FILE_PATH" =~ \.md$ ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Obsidian vault 경로
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note"

# vault 내 파일이 아니면 스킵
if [[ ! "$FILE_PATH" =~ "$VAULT" ]]; then
    exit 0
fi

# 비활성화 시 스킵
if [[ "$ENABLE_VAULT_LINKER" -ne 1 ]]; then
    exit 0
fi

# 제외 경로
if [[ "$FILE_PATH" =~ /99\.Template/ ]] || \
   [[ "$FILE_PATH" =~ /10\.Flashcards/ ]] || \
   [[ "$FILE_PATH" =~ /\.obsidian/ ]] || \
   [[ "$FILE_PATH" =~ Vault-Lint-Report ]]; then
    exit 0
fi

NEW_FILENAME=$(basename "$FILE_PATH" .md)

# 새 노트의 frontmatter + 핵심 아이디어 추출 (첫 30줄)
NOTE_SUMMARY=$(head -30 "$FILE_PATH" 2>/dev/null)

# vault의 모든 노트 목록 수집 (파일명 = 노트 제목)
# 제외: Template, Flashcards, .obsidian, 자기 자신
NOTE_LIST=$(find "$VAULT" -name "*.md" \
    -not -path "*/99.Template/*" \
    -not -path "*/.obsidian/*" \
    -not -name "FC-*" \
    -not -name "Vault-Lint-Report*" \
    2>/dev/null | while read -r f; do
        basename "$f" .md
    done | grep -v "^${NEW_FILENAME}$" | sort)

# 노트가 없으면 스킵
if [[ -z "$NOTE_LIST" ]]; then
    exit 0
fi

NOTE_COUNT=$(echo "$NOTE_LIST" | wc -l | tr -d ' ')

cat >&2 <<EOF

📎 Vault Linker — 의미적 링킹 컨텍스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

새 노트: [[${NEW_FILENAME}]]
요약:
${NOTE_SUMMARY}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vault 노트 목록 (${NOTE_COUNT}개):
${NOTE_LIST}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 vault 노트 목록에서 [[${NEW_FILENAME}]]과 의미적으로 관련된 노트를 찾아주세요.
단순 키워드 매칭이 아니라, 주제/개념의 연관성을 기반으로 판단하세요.
관련 노트가 있으면 사용자에게 related_notes 양방향 연결을 제안하세요.
관련 노트가 없으면 이 메시지를 무시하세요.

EOF

exit 2
