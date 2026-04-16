#!/bin/bash
# Check for .env files and similar configuration files
# .env 파일 생성 방지

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // .tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    echo '{}'
    exit 0
fi

# 환경 변수 파일 패턴
ENV_PATTERNS="(^|/)\.env($|\.local$|\.development$|\.production$|\.staging$|\.test$)"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)\.env\.[^.]+$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)config\.local\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)secrets?\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)credentials\.(json|yaml|yml|toml)$"

if echo "$FILE_PATH" | grep -qE "$ENV_PATTERNS"; then
    echo "🚨 Environment file detected: $FILE_PATH" >&2
    echo "Use .env.example with placeholder values instead." >&2

    echo '{"decision": "deny", "reason": "Environment/config files (.env, secrets.json, etc.) should not be created with real values. Create .env.example with placeholders instead."}'
    exit 0
fi

echo '{}'
exit 0
