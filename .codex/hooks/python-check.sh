#!/bin/bash
# Per-language check invoked by file-dispatcher.sh (Codex) or directly.
# Contract: reads {tool_input:{file_path}} on stdin, lints that one file,
# prints feedback, exits 2 on failure. Mirrors .claude/hooks/python-check.sh.
#
# Ruff is enabled by default; ty/pyrefly opt-in via ENABLE_*.

ENABLE_RUFF=${ENABLE_RUFF:-1}
ENABLE_TY=${ENABLE_TY:-0}
ENABLE_PYREFLY=${ENABLE_PYREFLY:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Prefer uvx (parity with .claude), fall back to ruff on PATH.
if command -v uvx >/dev/null 2>&1; then
	RUFF=(uvx ruff)
elif command -v ruff >/dev/null 2>&1; then
	RUFF=(ruff)
else
	exit 0
fi

CHECK_SUCCESS=1

if [[ "$ENABLE_RUFF" -eq 1 ]]; then
	if ! "${RUFF[@]}" check "$FILE_PATH" --fix; then
		echo "❌ ruff check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_TY" -eq 1 ]]; then
	if ! uvx ty check .; then
		echo "❌ ty check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

if [[ "$ENABLE_PYREFLY" -eq 1 ]]; then
	if ! uvx pyrefly check; then
		echo "❌ pyrefly check failed" >&2
		CHECK_SUCCESS=0
	fi
fi

[[ "$CHECK_SUCCESS" -eq 1 ]] && exit 0
echo "❌ Check failed. Please fix the issues above." >&2
exit 2
