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

env_patterns="(^|/)\\.env($|\\.local$|\\.development$|\\.production$|\\.staging$|\\.test$)"
env_patterns="$env_patterns|(^|/)\\.env\\.[^.]+$"
env_patterns="$env_patterns|(^|/)config\\.local\\.(json|yaml|yml|toml)$"
env_patterns="$env_patterns|(^|/)secrets?\\.(json|yaml|yml|toml)$"
env_patterns="$env_patterns|(^|/)credentials\\.(json|yaml|yml|toml)$"

if grep -qE "$env_patterns" <<<"$file_path"; then
  echo "Environment file detected: $file_path" >&2
  echo '{"decision":"deny","reason":"Environment/config files (.env, secrets.json, etc.) should not be created with real values. Create .env.example with placeholders instead."}'
  exit 0
fi

echo '{"decision":"allow"}'
