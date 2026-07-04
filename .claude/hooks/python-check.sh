#!/bin/bash

# NOTE:
# Ruff는 기본 활성화 (ENABLE_RUFF=0으로 끌 수 있음)
ENABLE_RUFF=${ENABLE_RUFF:-1}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

[[ "$ENABLE_RUFF" -eq 1 ]] || exit 0

# Prefer uvx, fall back to ruff on PATH (parity with .codex/hooks/python-check.sh)
if command -v uvx >/dev/null 2>&1; then
	RUFF=(uvx ruff)
elif command -v ruff >/dev/null 2>&1; then
	RUFF=(ruff)
else
	exit 0
fi

echo "🔧 Running ruff check on $FILE_PATH..."
if "${RUFF[@]}" check "$FILE_PATH" --fix; then
	echo "✅ All checks passed"
	exit 0
fi

echo "❌ ruff check failed. Please fix the issues above." >&2
exit 2
