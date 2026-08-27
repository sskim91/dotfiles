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
- **Context**: Infer from conversation history — fill in "그거", "아까 그", "그 파일" etc.
- **Constraints**: Any limitations or preferences mentioned or implied
- **Output**: What form the result should take

Rules:
- Preserve ALL information from original — never drop details
- Length can exceed original; clarity over brevity
- Same language as original
- If the prompt is already clear and structured, skip [Rewrite] entirely
- IMPORTANT: If a matching Skill exists for the user request, invoke the Skill tool FIRST. Rewriting does NOT replace skill invocation.

After [Rewrite], execute that version.
EOF

# Repo state injection, ported from .claude/hooks/prompt-rewriter.sh. The two copies
# had drifted: only the claude side injected git/deploy context, only this side had
# the `yml` bypass. Keep them behaviourally identical.
if printf '%s\n' "$prompt" | grep -qiE "commit|push|pr|merge|branch|rebase|cherry-pick|stash|커밋|푸시|머지|브랜치|리베이스"; then
  BRANCH=$(git branch --show-current 2>/dev/null || echo "N/A")
  DIRTY=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
  context+=$'\n\n## Git Context\nBranch: '"$BRANCH"', Changed files: '"$DIRTY"
fi

if printf '%s\n' "$prompt" | grep -qiE "deploy|배포|release|릴리즈|prod|운영"; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tags")
  context+=$'\n\n## Deploy Context\nLast tag: '"$LAST_TAG"
fi

jq -n --arg ctx "$context" '{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": $ctx
  }
}'
