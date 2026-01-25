#!/bin/bash

# SessionStart hook to inject current date/time context
# This runs automatically when a user starts a new session with Claude Code

# Output JSON with time/date context
cat <<EOF
{
  "suppressOutput": true,
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Current time and date: $(date '+%H:%M:%S %Y-%m-%d')"
  }
}
EOF