#!/bin/bash

# SessionStart hook to inject current date/time context
# Gemini CLI version — uses hookSpecificOutput.additionalContext per spec

CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "📅 Current time: $CURRENT_TIME" >&2

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "Current date and time: $CURRENT_TIME"
  }
}
EOF
