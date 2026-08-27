#!/bin/bash
# PreToolUse gate for Antigravity file writes: block writing real secret values into
# .env-style and structured config files.
#
# This used to be a copy of the commit-time checker, which reads `git diff --cached`.
# Wired to a write event it inspected the git index instead of the tool payload, so it
# could never fire (verified 2026-08-27) while the chain still claimed .env coverage.
# Its siblings check-secrets.sh / check-sensitive-files.sh do not close that gap either:
# a .env holding `DB_PASSWORD=hunter2000` passed both, because one matches only
# high-entropy prefixed tokens and the other only key/cert file extensions.
#
# The pattern constants below are unchanged from the commit-time policy; only the input
# source is different (toolCall.args instead of the git index).

set -euo pipefail

input=$(cat)

file_path=$(
  jq -r '
    .toolCall.args.TargetFile
    // .toolCall.args.AbsolutePath
    // empty
  ' <<<"$input"
)

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

if [[ -z "$file_path" ]]; then
  echo '{"decision":"allow"}'
  exit 0
fi

# 환경 변수 파일 패턴
ENV_PATTERNS="(^|/)\.env($|\.local$|\.development$|\.production$|\.staging$|\.test$)"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)\.env\.[^.]+$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)config\.local\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)secrets?\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)credentials\.(json|yaml|yml|toml)$"

# 안전한 파일 패턴 (플레이스홀더만 담는 템플릿 — 쓰기 허용)
SAFE_PATTERNS="\.(example|sample|template)$"

# 시크릿 실값 판별용 — 키 이름이 아래에 걸리고 값이 placeholder 가 아니면 실값으로 본다.
# KEY=value 셸 문법만 인식한다.
SECRET_KEY_PATTERN="(PASSWORD|PASSWD|SECRET|TOKEN|CREDENTIAL|PRIVATE_KEY|ACCESS_KEY|API_KEY)"
PLACEHOLDER_PATTERN="=(dummy|changeme|placeholder|example|test|xxx|your[-_]|\\\$\{|<)"

# 구조화 설정 파일(JSON/YAML/TOML)은 `key: value` 문법이라 위 탐지기가 원리적으로
# 발화하지 못한다. 값 검사를 건너뛰고 무조건 차단한다.
STRICT_PATTERNS="(^|/)(config\.local|secrets?|credentials)\.(json|yaml|yml|toml)$"

if ! grep -qE "$ENV_PATTERNS" <<<"$file_path"; then
  echo '{"decision":"allow"}'
  exit 0
fi

if grep -qE "$SAFE_PATTERNS" <<<"$file_path"; then
  echo '{"decision":"allow"}'
  exit 0
fi

if grep -qE "$STRICT_PATTERNS" <<<"$file_path"; then
  echo "Structured secret config write blocked: $file_path" >&2
  echo '{"decision":"deny","reason":"Writing secrets/credentials/config.local files is not allowed. Their key: value syntax cannot be value-checked, so they are blocked outright. Use a .example template or an untracked path."}'
  exit 0
fi

# .env 계열: 값이 실제 시크릿으로 보일 때만 차단한다. placeholder 만 담은 쓰기는 통과.
if [[ -n "$content" ]]; then
  risky=$(grep -iE "$SECRET_KEY_PATTERN" <<<"$content" | grep -ivE "$PLACEHOLDER_PATTERN" || true)
  if [[ -n "$risky" ]]; then
    echo "Real secret value detected in env file write: $file_path" >&2
    echo "$risky" >&2
    echo '{"decision":"deny","reason":"This env file write assigns a real value to a secret key. Use a placeholder, or write to a path that is not committed."}'
    exit 0
  fi
fi

echo '{"decision":"allow"}'
