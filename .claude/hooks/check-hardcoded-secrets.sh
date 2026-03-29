#!/bin/bash
# Check for hardcoded secrets in staged files
# 코드에 하드코딩된 비밀 정보 감지

# 검사할 파일 확장자
CODE_EXTENSIONS="\.py$|\.java$|\.js$|\.ts$|\.go$|\.rb$|\.php$|\.sh$|\.yaml$|\.yml$|\.json$|\.xml$|\.properties$|\.gradle$|\.kt$"

# 비밀 패턴 (정규식)
SECRET_PATTERNS=(
    # API Keys (Generic)
    "api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"
    "apikey['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]"

    # AWS
    "AKIA[0-9A-Z]{16}"
    "aws[_-]?secret[_-]?access[_-]?key"

    # GitHub
    "ghp_[a-zA-Z0-9]{36}"    # Personal Access Token
    "gho_[a-zA-Z0-9]{36}"    # OAuth Access Token
    "ghu_[a-zA-Z0-9]{36}"    # User-to-Server Token
    "ghs_[a-zA-Z0-9]{36}"    # Server-to-Server Token
    "github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}"  # Fine-grained PAT

    # GitLab
    "glpat-[a-zA-Z0-9_-]{20,}"

    # OpenAI / Anthropic
    "sk-proj-[a-zA-Z0-9_-]{80,}"  # OpenAI Project API Key
    "sk-svcacct-[a-zA-Z0-9_-]{80,}"  # OpenAI Service Account Key
    "sk-[a-zA-Z0-9]{48}"      # OpenAI (legacy)
    "sk-ant-[a-zA-Z0-9_-]{90,}"  # Anthropic

    # Slack
    "xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"  # Bot Token
    "xoxp-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"  # User Token
    "xapp-[0-9]+-[a-zA-Z0-9]+-[0-9]+-[a-zA-Z0-9]+"    # App-level Token

    # Google
    "AIza[0-9A-Za-z_-]{35}"   # Google API Key

    # Stripe
    "sk_live_[a-zA-Z0-9]{24,}"  # Secret Key
    "rk_live_[a-zA-Z0-9]{24,}"  # Restricted Key

    # Twilio
    "SK[a-f0-9]{32}"

    # SendGrid
    "SG\\.[a-zA-Z0-9_-]{22}\\.[a-zA-Z0-9_-]{43}"

    # npm
    "npm_[a-zA-Z0-9]{36}"

    # Discord
    "[MN][A-Za-z0-9]{23,}\\.[A-Za-z0-9_-]{6}\\.[A-Za-z0-9_-]{27}"

    # Hugging Face
    "hf_[a-zA-Z0-9]{30,}"    # API Token

    # PyPI
    "pypi-AgEIcHlwaS[a-zA-Z0-9_-]{50,}"  # Upload Token

    # Telegram
    "[0-9]{8,10}:[a-zA-Z0-9_-]{35}"  # Bot Token

    # Hashicorp Vault
    "hvs\\.[a-zA-Z0-9_-]{24,}"  # Service Token
    "hvb\\.[a-zA-Z0-9_-]{24,}"  # Batch Token

    # Sentry
    "sntrys_[a-zA-Z0-9]{50,}"  # Auth Token

    # Private Keys
    "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"

    # JWT/Tokens
    "eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*"

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
    exit 1
fi

exit 0
