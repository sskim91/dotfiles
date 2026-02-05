#!/bin/bash

# Modern TypeScript development tools
# 기본적으로 모두 비활성화 상태 (사용자가 필요시 활성화)
ENABLE_TSC=${ENABLE_TSC:-0}
ENABLE_BIOME=${ENABLE_BIOME:-0}
ENABLE_OXC=${ENABLE_OXC:-0}
ENABLE_ESLINT=${ENABLE_ESLINT:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process TypeScript files
if [[ ! "$FILE_PATH" =~ \.(ts|tsx)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔧 Running checks for TypeScript files..."

# Run checks
CHECK_SUCCESS=1

# TypeScript Compiler - strict type checking with modern settings
if [[ "$ENABLE_TSC" -eq 1 ]]; then
	echo "🔧 Running TypeScript compiler (strict mode)..."
	if ! npx tsc --noEmit --strict --skipLibCheck; then
		echo "❌ TypeScript type check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

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

# ESLint - Traditional but comprehensive linting
if [[ "$ENABLE_ESLINT" -eq 1 ]]; then
	echo "🔧 Running ESLint on $FILE_PATH..."
	if ! npx eslint "$FILE_PATH" --fix; then
		echo "❌ ESLint check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$CHECK_SUCCESS" -eq 1 ]]; then
	echo "✅ All TypeScript checks passed"
else
	echo "❌ TypeScript checks failed. Please fix the issues above." >&2
	exit 2
fi

exit 0