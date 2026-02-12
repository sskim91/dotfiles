#!/bin/bash

# NOTE:
# Ruff는 기본 활성화, 나머지는 필요시 활성화
ENABLE_RUFF=${ENABLE_RUFF:-1}
ENABLE_TY=${ENABLE_TY:-0}
ENABLE_PYREFLY=${ENABLE_PYREFLY:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔧 Running check for Python files..."

# Run check
CHECK_SUCCESS=1

if [[ "$ENABLE_RUFF" -eq 1 ]]; then
	echo "🔧 Running ruff check on $FILE_PATH..."
	if ! uvx ruff check "$FILE_PATH" --fix; then
		echo "❌ ruff check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_TY" -eq 1 ]]; then
	echo "🔧 Running ty check..."
	if ! uvx ty check .; then
		echo "❌ ty check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_PYREFLY" -eq 1 ]]; then
	echo "🔧 Running pyrefly check..."
	if ! uvx pyrefly check; then
		echo "❌ pyrefly check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$CHECK_SUCCESS" -eq 1 ]]; then
	echo "✅ All checks passed"
else
	echo "❌ Check failed. Please fix the issues above." >&2
	exit 2
fi

exit 0
