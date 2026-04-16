#!/bin/bash
# UserPromptSubmit hook for Codex.
#
# Codex currently supports adding developer context from UserPromptSubmit hooks,
# but not replacing the user's prompt. This hook makes the rewrite instruction
# turn-scoped instead of keeping it in global developer_instructions.

set -euo pipefail

prompt=$(jq -r '.prompt // empty' 2>/dev/null || true)

[[ -z "$prompt" ]] && exit 0
[[ "$prompt" == /* ]] && exit 0
[[ "$prompt" == \** ]] && exit 0
[[ "$prompt" == \#* ]] && exit 0
[[ ${#prompt} -lt 15 ]] && exit 0

[[ "$prompt" == *'```'* ]] && exit 0
[[ "$prompt" == *'http'* ]] && exit 0
[[ "$prompt" =~ \.(py|ts|js|java|sh|md|json|yaml|yml)$ ]] && exit 0

read -r -d '' context <<'EOF' || true
## Prompt Rewriter
The user writes informal Korean with repeated phrases, omitted context, and broken word order.

Before executing, show a [Rewrite] block using this structure:
- **Goal**: What the user wants (single clear sentence)
- **Context**: Infer from conversation history
- **Constraints**: Any limitations or preferences mentioned or implied
- **Output**: What form the result should take

Rules:
- Preserve ALL information from original
- Length can exceed original; clarity over brevity
- Same language as original
- If the prompt is already clear and structured, skip [Rewrite] entirely

After [Rewrite], execute that version.
EOF

jq -n --arg ctx "$context" '{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": $ctx
  }
}'
