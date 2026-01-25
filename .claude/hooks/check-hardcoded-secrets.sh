#!/bin/bash
# Check for hardcoded secrets in staged files
# 코드에 하드코딩된 비밀 정보 감지

# 검사할 파일 확장자
CODE_EXTENSIONS="\.py$|\.java$|\.js$|\.ts$|\.go$|\.rb$|\.php$|\.sh$|\.yaml$|\.yml$|\.json$|\.xml$|\.properties$|\.gradle$|\.kt$"

# 비밀 패턴 (정규식)
SECRET_PATTERNS=(
    # API Keys
    "api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"
    "apikey['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"

    # AWS
    "AKIA[0-9A-Z]{16}"
    "aws[_-]?secret[_-]?access[_-]?key"

    # Private Keys
    "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"

    # JWT/Tokens
    "eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"

    # Generic secrets
    "password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "secret['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"

    # Database URLs with credentials
    "(mysql|postgresql|mongodb|redis)://[^:]+:[^@]+@"
)

# 스테이징된 파일 중 코드 파일만 필터링
STAGED_CODE_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E "$CODE_EXTENSIONS" || true)

if [ -z "$STAGED_CODE_FILES" ]; then
    exit 0
fi

FOUND_SECRETS=""

for file in $STAGED_CODE_FILES; do
    if [ -f "$file" ]; then
        # 각 파일의 스테이징된 변경사항만 검사
        STAGED_CONTENT=$(git diff --cached "$file" 2>/dev/null | grep "^+" | grep -v "^+++" || true)

        for pattern in "${SECRET_PATTERNS[@]}"; do
            MATCHES=$(echo "$STAGED_CONTENT" | grep -iE "$pattern" || true)
            if [ -n "$MATCHES" ]; then
                FOUND_SECRETS="$FOUND_SECRETS\n📁 $file:\n$MATCHES\n"
            fi
        done
    fi
done

if [ -n "$FOUND_SECRETS" ]; then
    echo "🚨 Warning: Potential hardcoded secrets detected!"
    echo ""
    echo -e "$FOUND_SECRETS"
    echo ""
    echo "Recommendations:"
    echo "  1. Use environment variables instead"
    echo "  2. Use a secrets manager (AWS Secrets Manager, Vault, etc.)"
    echo "  3. If this is a false positive, you can bypass with:"
    echo "     git commit --no-verify"
    echo ""
    echo "⚠️  This is a WARNING, not blocking the commit."
    echo "    Please review the detected patterns carefully."
    echo ""
    # Warning only, don't block (exit 0)
    # To make it blocking, change to: exit 1
fi

exit 0
