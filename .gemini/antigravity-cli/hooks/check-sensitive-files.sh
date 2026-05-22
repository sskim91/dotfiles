#!/bin/bash
set -euo pipefail

input=$(cat)
file_path=$(
  jq -r '
    .toolCall.args.TargetFile
    // .toolCall.args.AbsolutePath
    // empty
  ' <<<"$input"
)

if [[ -z "$file_path" ]]; then
  echo '{"decision":"allow"}'
  exit 0
fi

sensitive_patterns="\\.(pem|key|p12|pfx|jks|crt|cer|keystore|truststore)$"

if grep -qE "$sensitive_patterns" <<<"$file_path"; then
  echo "Sensitive file detected: $file_path" >&2
  echo '{"decision":"deny","reason":"Sensitive file type (.pem, .key, .crt, etc.) should not be created. Use proper key management tools instead."}'
  exit 0
fi

echo '{"decision":"allow"}'
