#!/bin/bash

DISABLE_FORMAT=${DISABLE_FORMAT:-0}
ENABLE_RUFF=${ENABLE_RUFF:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Exit if format is disabled
if [[ "$DISABLE_FORMAT" -eq 1 ]]; then
	exit 0
fi

echo "🔧 Running format for Python files..."

# Run format
FORMAT_SUCCESS=1

if [[ "$ENABLE_RUFF" -eq 1 ]]; then
	echo "🔧 Running ruff format..."
	if ! uvx ruff format .; then
		echo "❌ ruff format failed" >&2
		FORMAT_SUCCESS=0
	fi
fi

if [[ "$FORMAT_SUCCESS" -eq 1 ]]; then
	echo "✅ Format completed"
else
	echo "❌ Format failed" >&2
	exit 2
fi

exit 0