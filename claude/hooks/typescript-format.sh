#!/bin/bash

# Modern TypeScript formatting tools
DISABLE_FORMAT=${DISABLE_FORMAT:-0}
ENABLE_PRETTIER=${ENABLE_PRETTIER:-0}
ENABLE_BIOME=${ENABLE_BIOME:-0}
ENABLE_DPRINT=${ENABLE_DPRINT:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process TypeScript files
if [[ ! "$FILE_PATH" =~ \.(ts|tsx)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Exit if format is disabled
if [[ "$DISABLE_FORMAT" -eq 1 ]]; then
	exit 0
fi

echo "🔧 Running modern formatters for TypeScript files..."

# Run formatters
FORMAT_SUCCESS=1

# Prettier - The industry standard formatter
if [[ "$ENABLE_PRETTIER" -eq 1 ]]; then
	echo "🔧 Running Prettier (modern code formatting)..."
	# Modern Prettier config with latest features
	if ! npx prettier --write --arrow-parens always --trailing-comma all --print-width 100 --tab-width 2 --semi true --single-quote true "**/*.{ts,tsx}"; then
		echo "❌ Prettier format failed" >&2
		FORMAT_SUCCESS=0
	fi
fi

# Biome - Fast, modern all-in-one formatter
if [[ "$ENABLE_BIOME" -eq 1 ]]; then
	echo "🔧 Running Biome formatter (blazing fast)..."
	if ! npx @biomejs/biome format --write .; then
		echo "❌ Biome format failed" >&2
		FORMAT_SUCCESS=0
	fi
fi

# dprint - Extremely fast Rust-based formatter
if [[ "$ENABLE_DPRINT" -eq 1 ]]; then
	echo "🔧 Running dprint (ultra-fast formatting)..."
	if ! npx dprint fmt; then
		echo "❌ dprint format failed" >&2
		FORMAT_SUCCESS=0
	fi
fi

if [[ "$FORMAT_SUCCESS" -eq 1 ]]; then
	echo "✅ TypeScript formatting completed with modern standards"
else
	echo "❌ TypeScript formatting failed" >&2
	exit 2
fi

exit 0