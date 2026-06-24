#!/bin/bash
# 관리자 API JWT 발급 래퍼 (on-demand, hybrid)
# - 설정(base URL/user_id/1Password 항목)은 ~/.dotfiles/.env.admin-api 에서 로드
# - 비밀번호는 1Password에서 실시간으로만 읽고 디스크에 남기지 않는다.
# - 발급한 access token만 ~/.cache/admin-api/token 에 캐시(600)하고, exp 임박 시 자동 재발급.
# 사용: TOKEN=$(admin-api-token.sh); curl -H "Authorization: Bearer $TOKEN" ...
set -euo pipefail

# 설정 로드 (로그인 셸이 아니어도 동작하도록 직접 source)
ENV_FILE="${DOTFILES:-$HOME/.dotfiles}/.env.admin-api"
# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && source "$ENV_FILE"

: "${ADMIN_API_BASE:?ADMIN_API_BASE 미설정 — $ENV_FILE 확인}"
: "${ADMIN_API_USER:?ADMIN_API_USER 미설정 — $ENV_FILE 확인}"
: "${ADMIN_API_OP_ITEM:?ADMIN_API_OP_ITEM 미설정 — $ENV_FILE 확인}"

LOGIN_URL="${ADMIN_API_BASE%/}/auth/login"
CACHE="${HOME}/.cache/admin-api/token"

# 캐시 토큰이 60초 이상 남아있으면 유효로 간주
token_valid() {
  [ -s "$CACHE" ] || return 1
  local payload pad exp now
  payload=$(cut -d. -f2 < "$CACHE")
  pad=$(( (4 - ${#payload} % 4) % 4 ))
  exp=$(printf '%s%s' "$payload" "$(printf '=%.0s' $(seq 1 "$pad"))" \
        | tr '_-' '/+' | base64 -d 2>/dev/null | jq -r '.exp // 0')
  now=$(date +%s)
  awk "BEGIN{exit !(${exp%.*} > $now + 60)}"
}

if ! token_valid; then
  pass=$(op item get "$ADMIN_API_OP_ITEM" --fields label=password --reveal)
  body=$(jq -n --arg u "$ADMIN_API_USER" --arg p "$pass" '{user_id:$u, password:$p}')
  res=$(curl -fsS -X POST "$LOGIN_URL" -H "Content-Type: application/json" -d "$body")
  token=$(printf '%s' "$res" | jq -r '.data.access_token // empty')
  if [ -z "$token" ]; then
    echo "로그인 실패: $res" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$CACHE")"
  ( umask 077; printf '%s' "$token" > "$CACHE" )
fi

cat "$CACHE"
