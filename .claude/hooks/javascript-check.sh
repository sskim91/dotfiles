#!/bin/bash

# Modern JavaScript development tools
# 기본적으로 모두 비활성화 상태 (사용자가 필요시 활성화)
ENABLE_BIOME=${ENABLE_BIOME:-0}
ENABLE_OXC=${ENABLE_OXC:-0}
ENABLE_ESLINT=${ENABLE_ESLINT:-0}
ENABLE_STANDARD=${ENABLE_STANDARD:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process JavaScript files
if [[ ! "$FILE_PATH" =~ \.(js|jsx|mjs|cjs)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔧 Running checks for modern JavaScript files..."

# Run checks
CHECK_SUCCESS=1

# Biome - Fast, modern all-in-one toolchain
if [[ "$ENABLE_BIOME" -eq 1 ]]; then
	echo "🔧 Running Biome check on $FILE_PATH..."
	if ! npx @biomejs/biome check --apply "$FILE_PATH"; then
		echo "❌ Biome check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

# OXC - Rust-based extremely fast linter
if [[ "$ENABLE_OXC" -eq 1 ]]; then
	echo "🔧 Running OXC linter on $FILE_PATH..."
	if ! npx oxlint --fix "$FILE_PATH"; then
		echo "❌ OXC lint failed" >&2
		CHECK_SUCCESS=0
	fi
fi

# ESLint - Traditional but comprehensive linting with modern configs
if [[ "$ENABLE_ESLINT" -eq 1 ]]; then
	echo "🔧 Running ESLint on $FILE_PATH..."
	if ! npx eslint "$FILE_PATH" --fix; then
		echo "❌ ESLint check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

# Standard JS - Zero-config modern JavaScript style
if [[ "$ENABLE_STANDARD" -eq 1 ]]; then
	echo "🔧 Running StandardJS on $FILE_PATH..."
	if ! npx standard --fix "$FILE_PATH"; then
		echo "❌ StandardJS check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$CHECK_SUCCESS" -eq 1 ]]; then
	echo "✅ All modern JavaScript checks passed"
else
	echo "❌ JavaScript checks failed. Please fix the issues above." >&2
	exit 2
fi

exit 0