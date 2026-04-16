#!/bin/bash
# Check for sensitive file extensions before file write
# 민감한 파일(키, 인증서 등) 생성 방지

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // .tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    echo '{}'
    exit 0
fi

# 민감한 파일 확장자 패턴
SENSITIVE_PATTERNS="\.(pem|key|p12|pfx|jks|crt|cer|keystore|truststore)$"

if echo "$FILE_PATH" | grep -qE "$SENSITIVE_PATTERNS"; then
    echo "🚨 Sensitive file detected: $FILE_PATH" >&2
    echo "Private keys and certificates should not be created by AI." >&2

    echo '{"decision": "deny", "reason": "Sensitive file type (.pem, .key, .crt, etc.) should not be created. Use proper key management tools instead."}'
    exit 0
fi

echo '{}'
exit 0
