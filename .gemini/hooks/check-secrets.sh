#!/bin/bash
# Check for hardcoded secrets before file write
# Gemini CLI BeforeTool hook

INPUT=$(cat)

# tool_input에서 파일 내용 추출
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_content // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // .tool_input.file_path // empty')

# 내용이 없으면 통과
if [[ -z "$CONTENT" ]]; then
    echo '{}'
    exit 0
fi

# 비밀 패턴 (정규식)
SECRET_PATTERNS=(
    # AWS
    "AKIA[0-9A-Z]{16}"

    # GitHub
    "ghp_[a-zA-Z0-9]{36}"
    "gho_[a-zA-Z0-9]{36}"
    "github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}"

    # GitLab
    "glpat-[a-zA-Z0-9_-]{20,}"

    # OpenAI / Anthropic
    "sk-[a-zA-Z0-9]{48}"
    "sk-ant-[a-zA-Z0-9_-]{90,}"

    # Slack
    "xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"
    "xoxp-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"

    # Google
    "AIza[0-9A-Za-z_-]{35}"

    # Stripe
    "sk_live_[a-zA-Z0-9]{24,}"
    "rk_live_[a-zA-Z0-9]{24,}"

    # Twilio
    "SK[a-f0-9]{32}"

    # SendGrid
    "SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}"

    # npm
    "npm_[a-zA-Z0-9]{36}"

    # Discord
    "[MN][A-Za-z0-9]{23,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}"

    # Private Keys
    "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"

    # JWT
    "eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"

    # Database URLs with credentials
    "(mysql|postgresql|mongodb|redis)://[^:]+:[^@]+@"
)

FOUND_SECRETS=""

for pattern in "${SECRET_PATTERNS[@]}"; do
    MATCHES=$(echo "$CONTENT" | grep -oE "$pattern" 2>/dev/null || true)
    if [[ -n "$MATCHES" ]]; then
        FOUND_SECRETS="$FOUND_SECRETS$MATCHES\n"
    fi
done

if [[ -n "$FOUND_SECRETS" ]]; then
    echo "🚨 Potential secrets detected in: $FILE_PATH" >&2
    echo -e "$FOUND_SECRETS" >&2
    echo "Use environment variables instead of hardcoding secrets." >&2

    # Block the operation (exit 2)
    echo '{"decision": "block", "reason": "Potential hardcoded secrets detected. Use environment variables instead."}'
    exit 2
fi

# Allow the operation
echo '{}'
exit 0
