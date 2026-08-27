#!/bin/bash
# Block 'rm' command and suggest 'trash' instead
# macOS 15+ has built-in 'trash' command at /usr/bin/trash

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Normalize: collapse whitespace, trim.
# Do NOT use xargs here: it applies shell quote parsing and exits non-zero on an
# unmatched quote, leaving COMMAND empty. `rm can't.log` then matched neither grep
# below and the delete went through -- a silent hole in an always-on guard.
COMMAND=$(printf '%s' "$COMMAND" | tr '\n\t' '  ' | sed -e 's/  */ /g' -e 's/^ //' -e 's/ *$//')

# Allow: \rm, command rm (intentional permanent delete)
if echo "$COMMAND" | grep -qE '(\\rm|command rm)'; then
    exit 0
fi

# Block: rm as standalone command (rm file, rm -rf dir, etc.)
if echo "$COMMAND" | grep -qE '(^|[;&|] *)rm '; then
    cat <<'HOOK_JSON'
{
  "decision": "block",
  "reason": "rm은 허용되지 않습니다. trash를 사용하세요.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "rm 명령이 차단되었습니다. macOS에서는 'trash <file>'로 휴지통으로 이동하세요. 영구 삭제가 필요하면 '\\rm' 또는 'command rm'을 사용하세요."
  }
}
HOOK_JSON
    exit 2
fi

exit 0
