#!/bin/bash
# Block 'rm' command and suggest 'trash' instead
# macOS 15+ has built-in 'trash' command at /usr/bin/trash

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Normalize: collapse whitespace, trim
COMMAND=$(echo "$COMMAND" | xargs)

# Allow: \rm, command rm (intentional permanent delete)
if echo "$COMMAND" | grep -qE '(\\rm|command rm)'; then
    exit 0
fi

# Block: rm as standalone command (rm file, rm -rf dir, etc.)
if echo "$COMMAND" | grep -qE '(^|[;&|] *)rm '; then
    echo "BLOCKED: 'rm' is not allowed. Use 'trash' instead." >&2
    echo "  trash <file>       # move to macOS Trash" >&2
    echo "  trash -v <file>    # verbose mode" >&2
    echo "If you truly need permanent delete, use '\\rm' or 'command rm'." >&2
    exit 2
fi

exit 0
