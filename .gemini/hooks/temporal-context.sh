#!/bin/bash

# SessionStart hook to inject current date/time context
# Gemini CLI version

CURRENT_TIME=$(date '+%H:%M:%S %Y-%m-%d')

echo "📅 Current time: $CURRENT_TIME" >&2

# Gemini CLI format
cat <<EOF
{
  "context": "Current time and date: $CURRENT_TIME"
}
EOF
