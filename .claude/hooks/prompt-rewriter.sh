#!/bin/bash
# prompt-rewriter.sh — UserPromptSubmit hook
# Injects "rewrite then execute" instruction as additionalContext

prompt=$(cat | jq -r '.prompt // empty')

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

jq -n '{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "## Prompt Rewriter\nThe user writes informal Korean with repeated phrases, omitted context, and broken word order.\n\nBefore executing, show a [Rewrite] block using this structure:\n- **Goal**: What the user wants (single clear sentence)\n- **Context**: Infer from conversation history — fill in \"그거\", \"아까 그\", \"그 파일\" etc.\n- **Constraints**: Any limitations or preferences mentioned or implied\n- **Output**: What form the result should take\n\nRules:\n- Preserve ALL information from original — never drop details\n- Length can exceed original — clarity over brevity\n- Same language as original\n- If the prompt is already clear and structured, skip [Rewrite] entirely\n- IMPORTANT: If a matching Skill exists for the user request, invoke the Skill tool FIRST. Rewriting does NOT replace skill invocation.\n\nAfter [Rewrite], execute that version."
  }
}'
