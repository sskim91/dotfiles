#!/bin/bash
# Block 'rm' command and suggest 'trash' instead
# macOS 15+ has built-in 'trash' command at /usr/bin/trash
#
# Codex contract differs from the Claude copy: blocking is signalled by the
# `decision` field with exit 0, not by exit 2.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check each line separately. Two normalizations were tried here and both
# opened a silent hole in an always-on guard:
#
#   1. xargs -- applies shell quote parsing and exits non-zero on an unmatched
#      quote, leaving COMMAND empty. `rm can't.log` then matched nothing.
#   2. tr '\n' ' ' -- a newline IS a shell command separator, so
#      `touch x<newline>rm x` collapsed to `touch x rm x`, where rm no longer
#      follows a separator and the pattern below stopped matching. Multi-line
#      commands are the common shape, so this leaked more than (1) did.
#      (Measured 2026-08-29: newline, newline+-rf, and 3-line forms all passed.)
#
# Splitting on lines keeps the separator instead of destroying it. Tabs are
# still folded to spaces -- a tab is whitespace, not a separator.
#
# Trade-off: heredoc *content* with `rm` at line start now blocks too. That is
# a false positive with a documented escape hatch (\rm), preferred over letting
# a real multi-line delete through.
blocked=0
while IFS= read -r line; do
    line=$(printf '%s' "$line" | tr '\t' ' ')

    # Allow: \rm, command rm (intentional permanent delete)
    if printf '%s' "$line" | grep -qE '(\\rm|command rm)'; then
        continue
    fi

    # Block: rm as a standalone command (line start, or after ; & |)
    if printf '%s' "$line" | grep -qE '(^|[;&|]) *rm '; then
        blocked=1
        break
    fi
done <<< "$COMMAND"

if [[ $blocked -eq 1 ]]; then
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
fi

exit 0
