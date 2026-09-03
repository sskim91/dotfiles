#!/bin/bash
# UserPromptSubmit hook shared by Codex and Claude Code.
#
# Prompt rewriting is opt-in: prefix a request with `rewrite:` or `재작성:`.
# Git/deploy context remains automatic, but only for exact intent keywords.

set -euo pipefail

prompt=$(jq -r '.prompt // empty' 2>/dev/null || true)

[[ -z "$prompt" ]] && exit 0
[[ "$prompt" == /* ]] && exit 0
[[ "$prompt" == \** ]] && exit 0
[[ "$prompt" == \#* ]] && exit 0

context=""

append_context() {
  if [[ -n "$context" ]]; then
    context+=$'\n\n'
  fi
  context+="$1"
}

case "$prompt" in
  [Rr][Ee][Ww][Rr][Ii][Tt][Ee]:* | 재작성:*)
    rewrite_context=""
    read -r -d '' rewrite_context <<'EOF' || true
## Prompt Rewrite
The user explicitly requested a rewrite-then-execute pass.

Before executing, show a [Rewrite] block with:
- **Goal**: The intended outcome in one sentence
- **Context**: Relevant conversation context and resolved references
- **Constraints**: Requirements, limits, and approval boundaries
- **Output**: The expected result or format

Preserve every requirement, use the user's language, and treat the leading
`rewrite:` or `재작성:` as a control prefix. If a matching skill applies, invoke
it before rewriting. Then execute the rewritten request.
EOF
    append_context "$rewrite_context"
    ;;
esac

git_pattern='(^|[^A-Za-z0-9_])(commit|push|pull request|merge|branch|rebase|cherry-pick|stash|pr)([^A-Za-z0-9_]|$)|커밋|푸시|머지|브랜치|리베이스'
if printf '%s\n' "$prompt" | grep -qiE "$git_pattern"; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null || true)
    [[ -z "$branch" ]] && branch="N/A"
    dirty=$(git status --short | wc -l | tr -d ' ')
  else
    branch="N/A"
    dirty="N/A"
  fi
  append_context "## Git Context"$'\n'"Branch: $branch, Changed files: $dirty"
fi

deploy_pattern='(^|[^A-Za-z0-9_])(deploy|deployment|release|prod|production)([^A-Za-z0-9_]|$)|배포|릴리즈|운영'
if printf '%s\n' "$prompt" | grep -qiE "$deploy_pattern"; then
  last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tags")
  append_context "## Deploy Context"$'\n'"Last tag: $last_tag"
fi

[[ -z "$context" ]] && exit 0

jq -n --arg ctx "$context" '{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": $ctx
  }
}'
