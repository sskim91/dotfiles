#!/bin/bash
# Per-language check invoked by file-dispatcher.sh (Codex) or directly.
# Contract: reads {tool_input:{file_path}} on stdin, lints that one file,
# prints feedback, exits 2 on failure. Mirrors .claude/hooks/javascript-check.sh.
#
# All JavaScript checks are OPT-IN (disabled by default). Enable via ENABLE_*.

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

CHECK_SUCCESS=1

if [[ "$ENABLE_BIOME" -eq 1 ]]; then
	if ! npx @biomejs/biome check --apply "$FILE_PATH"; then
		echo "❌ Biome check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_OXC" -eq 1 ]]; then
	if ! npx oxlint --fix "$FILE_PATH"; then
		echo "❌ OXC lint failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_ESLINT" -eq 1 ]]; then
	if ! npx eslint "$FILE_PATH" --fix; then
		echo "❌ ESLint check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_STANDARD" -eq 1 ]]; then
	if ! npx standard --fix "$FILE_PATH"; then
		echo "❌ StandardJS check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

[[ "$CHECK_SUCCESS" -eq 1 ]] && exit 0
echo "❌ JavaScript checks failed. Please fix the issues above." >&2
exit 2
