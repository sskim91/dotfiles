#!/bin/bash
# Gate script: git commit 명령일 때만 보안 검사 실행
# matcher "Bash"로 모든 Bash 호출에 트리거되므로, 여기서 한 번만 필터링

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if ! echo "$COMMAND" | grep -q 'git commit'; then
    exit 0
fi

# git commit인 경우 보안 검사 순차 실행
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
FAILED=0

for check in check-sensitive-files.sh check-env-files.sh check-hardcoded-secrets.sh; do
    OUTPUT=$("$HOOK_DIR/$check" 2>&1)
    STATUS=$?
    if [ $STATUS -ne 0 ]; then
        echo "$OUTPUT"
        FAILED=1
    fi
done

exit $FAILED
