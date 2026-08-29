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

  # Staleness fields ride along on resume/fork from Claude Code 2.1.251+.
  # Field names captured from a real resume payload on 2026-08-29 -- the
  # binary's internal names (staleness_ms, recache_tokens_if_cold) are NOT
  # what lands here, so do not re-derive these from `strings`. On older
  # builds every read falls back to empty and the clauses are skipped.
  IDLE=$(printf '%s\n' "$INPUT" | jq -r '.seconds_since_last_response // empty' 2>/dev/null)
  if [[ -n "$IDLE" ]]; then
    if [[ $IDLE -lt 60 ]]; then
      IDLE_H="${IDLE}s"
    elif [[ $IDLE -lt 3600 ]]; then
      IDLE_H="$((IDLE / 60))m"
    else
      IDLE_H="$((IDLE / 3600))h $(((IDLE % 3600) / 60))m"
    fi
    CONTEXT+=", Idle ${IDLE_H}"
  fi

  EXPIRED=$(printf '%s\n' "$INPUT" | jq -r '.prompt_cache_likely_expired // empty' 2>/dev/null)
  if [[ "$EXPIRED" == "true" ]]; then
    TOKENS=$(printf '%s\n' "$INPUT" | jq -r '.context_tokens // empty' 2>/dev/null)
    COST=$(printf '%s\n' "$INPUT" | jq -r '.estimated_cache_write_usd // empty' 2>/dev/null)
    CONTEXT+=", prompt cache expired"
    [[ -n "$TOKENS" ]] && CONTEXT+=" (first request re-caches ${TOKENS} tokens"
    [[ -n "$TOKENS" && -n "$COST" ]] && CONTEXT+=", ~\$${COST}"
    [[ -n "$TOKENS" ]] && CONTEXT+=")"
  fi
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
