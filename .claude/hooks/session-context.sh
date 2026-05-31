#!/bin/bash

# SessionStart hook to inject current date/time context
# Reads stdin JSON to distinguish startup vs resume vs clear

INPUT=$(cat)
SOURCE=$(printf '%s\n' "$INPUT" | jq -r '.source // "startup"' 2>/dev/null)

BRANCH=$(git branch --show-current 2>/dev/null || echo "not a git repo")
CONTEXT="Current time: $(date '+%H:%M %Y-%m-%d'), Branch: $BRANCH"

if [[ "$SOURCE" == "resume" ]]; then
  LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "no commits")
  CONTEXT+=", Resumed session. Last commit: $LAST_COMMIT"
elif [[ "$SOURCE" == "compact" ]]; then
  CONTEXT+=", Context was compacted"
fi

jq -n --arg ctx "$CONTEXT" '{
  "suppressOutput": true,
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ctx
  }
}'
