#!/bin/bash

# vault-linker.sh — PostToolUse hook
# Obsidian vault에 .md 파일 생성/수정 시 관련 노트를 검색하여 피드백 제공
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

# 새 파일에서 키워드 추출 (tags에서)
KEYWORDS=$(sed -n '/^tags:/,/^[^ ]/p' "$FILE_PATH" 2>/dev/null | grep "  - " | sed 's/  - //' | sed 's|/| |g' | tr '\n' '|' | sed 's/|$//')

# 키워드가 없으면 핵심 아이디어 섹션에서 추출
if [[ -z "$KEYWORDS" ]]; then
    KEYWORDS=$(sed -n '/## 핵심/,/^---$/p' "$FILE_PATH" 2>/dev/null | head -5 | tr -d '>#*_[]()' | tr ' ' '\n' | sort -u | awk 'length > 3' | head -5 | tr '\n' '|' | sed 's/|$//')
fi

if [[ -z "$KEYWORDS" ]]; then
    exit 0
fi

# vault에서 관련 노트 검색 (자기 자신 제외)
RELATED=$(grep -rli -E "$KEYWORDS" "$VAULT" --include="*.md" 2>/dev/null | \
    grep -v "$FILE_PATH" | \
    grep -v "/99.Template/" | \
    grep -v "/10.Flashcards/" | \
    grep -v "/.obsidian/" | \
    head -5)

# 결과가 없으면 스킵
if [[ -z "$RELATED" ]]; then
    exit 0
fi

COUNT=$(echo "$RELATED" | wc -l | tr -d ' ')

cat >&2 <<EOF

📎 Vault Linker: 관련 노트 ${COUNT}건 발견
─────────────────────────────
EOF

echo "$RELATED" | while read -r NOTE; do
    NOTE_NAME=$(basename "$NOTE" .md)
    echo "  → [[${NOTE_NAME}]]" >&2
done

cat >&2 <<EOF
─────────────────────────────
💡 이 노트들과 양방향 [[wikilink]] 연결을 고려하세요.
   related_notes에 추가하려면 사용자에게 확인하세요.

EOF

exit 2
