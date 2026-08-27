#!/bin/bash
# Check for sensitive file extensions before commit
# 민감한 파일(키, 인증서 등)이 커밋되는 것을 방지

# 민감한 파일 확장자 패턴
SENSITIVE_PATTERNS="\.(pem|key|p12|pfx|jks|crt|cer|keystore|truststore)$"

# git diff에서 추가된 파일 중 민감한 파일 체크.
# --diff-filter=d 로 삭제를 제외한다: 없으면 파일명만 보고 차단하므로, 실수로 커밋된 키를
# "제거하는" 커밋까지 막혀 --no-verify 없이는 수습이 불가능해진다.
SENSITIVE_FILES=$(git diff --cached --name-only --diff-filter=d 2>/dev/null | grep -E "$SENSITIVE_PATTERNS" || true)

if [ -n "$SENSITIVE_FILES" ]; then
    echo "🚨 Error: Sensitive file(s) detected!"
    echo ""
    echo "The following files should NOT be committed:"
    echo "$SENSITIVE_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    echo "These files typically contain:"
    echo "  - Private keys (.pem, .key)"
    echo "  - Certificates (.crt, .cer)"
    echo "  - Keystores (.p12, .pfx, .jks)"
    echo ""
    echo "Please add them to .gitignore or remove from staging:"
    echo "  git reset HEAD <file>"
    echo ""
    exit 1
fi

exit 0
