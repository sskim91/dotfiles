#!/bin/bash
# Gate script: git commit 시 보안 검사 실행
# settings.json의 "if": "Bash(git commit*)"로 필터링됨

INPUT=$(cat)

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
