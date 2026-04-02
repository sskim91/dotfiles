#!/bin/bash
# prompt-rewriter.sh — UserPromptSubmit hook
# Injects "rewrite then execute" instruction as additionalContext

prompt=$(cat | jq -r '.prompt // empty' 2>/dev/null)

# Bypass conditions
[[ -z "$prompt" ]] && exit 0
[[ "$prompt" == /* ]] && exit 0          # slash commands
[[ "$prompt" == \** ]] && exit 0         # explicit bypass with *
[[ "$prompt" == \#* ]] && exit 0         # memory/comment
[[ ${#prompt} -lt 15 ]] && exit 0        # short replies (응, ㅇㅇ, ok, 해줘, etc.)

# Skip if prompt looks structured (contains code blocks, URLs, file paths)
[[ "$prompt" == *'```'* ]] && exit 0     # code blocks
[[ "$prompt" == *'http'* ]] && exit 0    # URLs
[[ "$prompt" =~ \.(py|ts|js|java|sh|md|json|yaml)$ ]] && exit 0  # ends with file extension

REWRITER_INSTRUCTION="## Prompt Rewriter\nThe user writes informal Korean with repeated phrases, omitted context, and broken word order.\n\nBefore executing, show a [Rewrite] block using this structure:\n- **Goal**: What the user wants (single clear sentence)\n- **Context**: Infer from conversation history — fill in \"그거\", \"아까 그\", \"그 파일\" etc.\n- **Constraints**: Any limitations or preferences mentioned or implied\n- **Output**: What form the result should take\n\nRules:\n- Preserve ALL information from original — never drop details\n- Length can exceed original — clarity over brevity\n- Same language as original\n- If the prompt is already clear and structured, skip [Rewrite] entirely\n- IMPORTANT: If a matching Skill exists for the user request, invoke the Skill tool FIRST. Rewriting does NOT replace skill invocation.\n\nAfter [Rewrite], execute that version."

EXTRA_CONTEXT=""

# git 관련 키워드가 있으면 현재 상태 주입
if printf '%s\n' "$prompt" | grep -qiE "commit|push|pr|merge|branch|rebase|cherry-pick|stash|커밋|푸시|머지|브랜치|리베이스"; then
  BRANCH=$(git branch --show-current 2>/dev/null || echo "N/A")
  DIRTY=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
  EXTRA_CONTEXT=$'\n\n## Git Context\nBranch: '"$BRANCH"', Changed files: '"$DIRTY"
fi

# 배포/운영 관련 키워드
if printf '%s\n' "$prompt" | grep -qiE "deploy|배포|release|릴리즈|prod|운영"; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tags")
  EXTRA_CONTEXT+=$'\n\n## Deploy Context\nLast tag: '"$LAST_TAG"
fi

# printf %b로 \n을 실제 개행으로 변환 후 jq에 전달
FULL_CONTEXT=$(printf '%b' "${REWRITER_INSTRUCTION}${EXTRA_CONTEXT}")

jq -n --arg ctx "$FULL_CONTEXT" '{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": $ctx
  }
}'
