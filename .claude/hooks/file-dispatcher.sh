#!/bin/bash

# File dispatcher that routes to appropriate language-specific hooks based on file extension.
# On lint failure, surfaces the child script's output to Claude inline via
# PostToolUse hookSpecificOutput.updatedToolOutput (Claude Code 2.1.121+).

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
HOOK_TYPE="${1:-check}"

case "$FILE_PATH" in
	*.py) LANGUAGE="python" ;;
	*.java) LANGUAGE="java" ;;
	*.ts|*.tsx) LANGUAGE="typescript" ;;
	*.js|*.jsx|*.mjs|*.cjs) LANGUAGE="javascript" ;;
	*.go) LANGUAGE="go" ;;
	*.rs) LANGUAGE="rust" ;;
	*.cpp|*.cc|*.cxx|*.h|*.hpp) LANGUAGE="cpp" ;;
	*) exit 0 ;;
esac

HOOK_SCRIPT="$(dirname "$0")/${LANGUAGE}-${HOOK_TYPE}.sh"
[[ -f "$HOOK_SCRIPT" ]] || exit 0

TMP_OUT=$(mktemp)
trap 'rm -f "$TMP_OUT"' EXIT

echo "$INPUT" | "$HOOK_SCRIPT" >"$TMP_OUT" 2>&1
CHILD_EXIT=$?

if [[ "$CHILD_EXIT" -eq 0 ]]; then
	exit 0
fi

LINT_OUTPUT=$(cat "$TMP_OUT")
[[ -z "$LINT_OUTPUT" ]] && exit 0

ORIGINAL=$(echo "$INPUT" | jq -r '.tool_response // "" | if type == "object" then tojson else tostring end')

UPDATED=$(printf '%s\n\n[%s-%s lint feedback]\n%s' "$ORIGINAL" "$LANGUAGE" "$HOOK_TYPE" "$LINT_OUTPUT")

jq -n --arg out "$UPDATED" \
	'{hookSpecificOutput: {hookEventName: "PostToolUse", updatedToolOutput: $out}}'

exit 0
