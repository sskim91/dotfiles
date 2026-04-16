#!/bin/bash
# PreToolUse hook — security checks before git commit
# Codex-local pre-commit gate.
#
# Codex doesn't support "if" filters, so we filter the command here.

INPUT=$(cat)
COMMAND=$(printf '%s\n' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only run on git commit commands
if ! printf '%s\n' "$COMMAND" | grep -qE '^git commit'; then
  exit 0
fi

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FAILED=0

for check in check-sensitive-files.sh check-env-files.sh check-hardcoded-secrets.sh; do
  if [[ -x "$HOOK_DIR/$check" ]]; then
    OUTPUT=$("$HOOK_DIR/$check" 2>&1)
    STATUS=$?
    if [[ $STATUS -ne 0 ]]; then
      echo "$OUTPUT" >&2
      FAILED=1
    fi
  fi
done

if [[ $FAILED -ne 0 ]]; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": "Security check failed. Sensitive files, env files, or hardcoded secrets detected in staged changes."
    }
  }'
  exit 2
fi

exit 0
