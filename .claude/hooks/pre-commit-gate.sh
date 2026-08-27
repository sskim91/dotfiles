#!/bin/bash
# Gate script: git commit 시 보안 검사 실행
# settings.json의 "if": "Bash(*git commit*)"로 필터링됨

INPUT=$(cat)

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
FAILED=0

# -x 가드가 필요하다: 스크립트가 없거나 실행권한이 빠지면 127이 돌아오고, 그게 FAILED=1로
# 이어져 "command not found"만 남긴 채 모든 커밋이 막힌다. .codex 미러는 이미 이 가드를 쓴다.
for check in check-sensitive-files.sh check-env-files.sh check-hardcoded-secrets.sh; do
    if [ -x "$HOOK_DIR/$check" ]; then
        OUTPUT=$("$HOOK_DIR/$check" 2>&1)
        STATUS=$?
        if [ $STATUS -ne 0 ]; then
            echo "$OUTPUT" >&2
            FAILED=1
        fi
    fi
done

if [ $FAILED -ne 0 ]; then
    exit 2
fi
exit 0
