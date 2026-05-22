#!/bin/bash
set -euo pipefail

input=$(cat)

content=$(
  jq -r '
    .toolCall.args.CodeContent
    // .toolCall.args.ReplacementContent
    // (
      .toolCall.args.ReplacementChunks
      | if type == "array" then map(.ReplacementContent // .replacementContent // "") | join("\n") else empty end
    )
    // empty
  ' <<<"$input"
)

file_path=$(
  jq -r '
    .toolCall.args.TargetFile
    // .toolCall.args.AbsolutePath
    // empty
  ' <<<"$input"
)

if [[ -z "$content" ]]; then
  echo '{"decision":"allow"}'
  exit 0
fi

secret_patterns=(
  "AKIA[0-9A-Z]{16}"
  "ghp_[a-zA-Z0-9]{36}"
  "gho_[a-zA-Z0-9]{36}"
  "github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}"
  "glpat-[a-zA-Z0-9_-]{20,}"
  "sk-[a-zA-Z0-9]{48}"
  "sk-ant-[a-zA-Z0-9_-]{90,}"
  "xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"
  "xoxp-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"
  "AIza[0-9A-Za-z_-]{35}"
  "sk_live_[a-zA-Z0-9]{24,}"
  "rk_live_[a-zA-Z0-9]{24,}"
  "SK[a-f0-9]{32}"
  "SG\\.[a-zA-Z0-9_-]{22}\\.[a-zA-Z0-9_-]{43}"
  "npm_[a-zA-Z0-9]{36}"
  "[MN][A-Za-z0-9]{23,}\\.[A-Za-z0-9_-]{6}\\.[A-Za-z0-9_-]{27}"
  "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
  "eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*"
  "(mysql|postgresql|mongodb|redis)://[^:]+:[^@]+@"
)

found_secrets=""
for pattern in "${secret_patterns[@]}"; do
  matches=$(grep -oE "$pattern" <<<"$content" 2>/dev/null || true)
  if [[ -n "$matches" ]]; then
    found_secrets="${found_secrets}${matches}"$'\n'
  fi
done

if [[ -n "$found_secrets" ]]; then
  echo "Potential secrets detected in: $file_path" >&2
  echo "$found_secrets" >&2
  echo '{"decision":"deny","reason":"Potential hardcoded secrets detected. Use environment variables instead."}'
  exit 0
fi

echo '{"decision":"allow"}'
