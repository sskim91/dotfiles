#!/bin/bash
# PostToolUse dispatcher for Codex.
#
# Codex's apply_patch delivers a patch envelope in tool_input.command and can touch
# MANY files at once. This dispatcher parses the envelope once, routes each changed
# file to {language}-{check}.sh by extension, and feeds each file to the per-language
# script as {tool_input:{file_path}} — the SAME contract the .claude/hooks scripts use,
# so per-language checks are portable between Claude and Codex.
#
# Per-language scripts print feedback and exit non-zero on lint failure. Collected
# feedback is surfaced to the model via hookSpecificOutput.additionalContext (non-blocking).
#
# Usage (from hooks.json): bash file-dispatcher.sh check

set -uo pipefail

INPUT=$(cat)
HOOK_TYPE="${1:-check}"

# apply_patch (and its Edit/Write matcher aliases) carry the patch in tool_input.command.
PATCH=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[[ -z "$PATCH" ]] && exit 0

# Resolve relative paths against the session cwd.
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
[[ -n "$CWD" && -d "$CWD" ]] && cd "$CWD" 2>/dev/null

# Extract changed paths from the apply_patch envelope:
#   *** Add File: <path>     *** Update File: <path>
#   *** Delete File: <path>   *** Move to: <path>
FILES=$(printf '%s\n' "$PATCH" \
	| sed -nE 's/^\*\*\* (Add|Update|Delete) File: (.+)$/\2/p; s/^\*\*\* Move to: (.+)$/\1/p')

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEEDBACK=""

while IFS= read -r f; do
	[[ -z "$f" ]] && continue
	[[ -f "$f" ]] || continue   # deleted/renamed-away files won't exist → skip
	case "$f" in
		*.py) LANGUAGE="python" ;;
		*.java) LANGUAGE="java" ;;
		*.ts | *.tsx) LANGUAGE="typescript" ;;
		*.js | *.jsx | *.mjs | *.cjs) LANGUAGE="javascript" ;;
		*) continue ;;
	esac
	SCRIPT="$HOOK_DIR/${LANGUAGE}-${HOOK_TYPE}.sh"
	[[ -x "$SCRIPT" ]] || continue

	CHILD_INPUT=$(jq -nc --arg p "$f" '{tool_input: {file_path: $p}}')
	OUT=$(printf '%s' "$CHILD_INPUT" | "$SCRIPT" 2>&1)
	RC=$?
	if [[ "$RC" -ne 0 && -n "$OUT" ]]; then
		FEEDBACK+="[${LANGUAGE}] ${f}"$'\n'"${OUT}"$'\n\n'
	fi
done <<< "$FILES"

[[ -z "$FEEDBACK" ]] && exit 0

FEEDBACK=$(printf '[lint feedback]\n%s' "$FEEDBACK")
jq -n --arg ctx "$FEEDBACK" '{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": $ctx
  }
}'
exit 0
