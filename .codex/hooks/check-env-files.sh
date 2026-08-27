#!/bin/bash
# Check for .env files and similar configuration files
# .env 파일이 커밋되는 것을 방지
# ENABLE_ENV_FILE_CHECK (zsh/path.zsh) 가 1이 아니면 검사 없이 통과.
# 기본값 0 — 사용자가 이 게이트를 비활성으로 결정 (2026-08). 재활성화는 export =1.
# (fallback을 0으로 두는 이유: export 이전에 시작된 세션에도 즉시 적용되게)

[ "${ENABLE_ENV_FILE_CHECK:-0}" != "1" ] && exit 0

# 환경 변수 파일 패턴
ENV_PATTERNS="(^|/)\.env($|\.local$|\.development$|\.production$|\.staging$|\.test$)"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)\.env\.[^.]+$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)config\.local\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)secrets?\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)credentials\.(json|yaml|yml|toml)$"

# 안전한 파일 패턴 (플레이스홀더만 포함, 커밋 허용)
SAFE_PATTERNS="\.(example|sample|template)$"

# 시크릿 실값 판별용 — 키 이름이 아래에 걸리고 값이 placeholder 가 아니면 실값으로 본다.
# KEY=value 셸 문법만 인식한다.
SECRET_KEY_PATTERN="(PASSWORD|PASSWD|SECRET|TOKEN|CREDENTIAL|PRIVATE_KEY|ACCESS_KEY|API_KEY)"
PLACEHOLDER_PATTERN="=(dummy|changeme|placeholder|example|test|xxx|your[-_]|\\\$\{|<)"

# 구조화 설정 파일(JSON/YAML/TOML)은 `key: value` 문법이라 위 탐지기가 원리적으로
# 발화하지 못한다. 추적 파일 우회에서 제외하고 종전처럼 무조건 차단한다.
STRICT_PATTERNS="(^|/)(config\.local|secrets?|credentials)\.(json|yaml|yml|toml)$"

# git diff에서 추가된 파일 중 환경 변수 파일 체크 (안전한 파일 제외).
# --diff-filter=d 로 삭제를 제외한다: 없으면 STRICT_PATTERNS 경로가 파일명만 보고 차단하므로,
# 실수로 커밋된 secrets.json 등을 "제거하는" 커밋까지 막힌다.
ENV_FILES=$(git diff --cached --name-only --diff-filter=d 2>/dev/null | grep -E "$ENV_PATTERNS" | grep -Ev "$SAFE_PATTERNS" || true)

# 이미 추적 중인 KEY=value 형식 env 파일의 "수정"은 통과시킨다 — 레포가 의도적으로 관리하는
# 설정(placeholder·더미값)이고, 최초 커밋 시점에 이미 사람이 판단한 파일이다.
# 차단 대상은 세 가지다: ① 새로 추가되는 env 파일 ② 구조화 설정 파일(STRICT_PATTERNS)
# ③ 추적 파일이라도 추가된 줄에 시크릿 실값이 보이는 경우
# (check-hardcoded-secrets.sh 는 코드 확장자만 스캔해 env 내용을 못 본다).
NEW_ENV_FILES=""
STRICT_ENV_FILES=""
RISKY_ENV_FILES=""
if [ -n "$ENV_FILES" ]; then
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        if ! git cat-file -e "HEAD:$file" 2>/dev/null; then
            NEW_ENV_FILES="${NEW_ENV_FILES}${file}"$'\n'
            continue
        fi
        if echo "$file" | grep -Eq "$STRICT_PATTERNS"; then
            STRICT_ENV_FILES="${STRICT_ENV_FILES}${file}"$'\n'
            continue
        fi
        ADDED=$(git diff --cached -- "$file" 2>/dev/null | grep "^+" | grep -v "^+++" || true)
        # 시크릿 키가 걸린 줄만 추린 뒤 그 줄들에 placeholder 가 없으면 실값으로 본다.
        # (diff 블록 전체를 한 번에 검사하면 무해한 placeholder 한 줄이 실값을 가려준다)
        if printf '%s\n' "$ADDED" \
            | grep -Ei "^\+[A-Za-z0-9_]*${SECRET_KEY_PATTERN}[A-Za-z0-9_]*=[^[:space:]]" \
            | grep -Eivq "$PLACEHOLDER_PATTERN"; then
            RISKY_ENV_FILES="${RISKY_ENV_FILES}${file}"$'\n'
        fi
    done <<< "$ENV_FILES"
fi

if [ -n "$NEW_ENV_FILES" ]; then
    echo "🚨 Error: New environment/config file(s) detected!"
    echo ""
    echo "The following files are NOT tracked yet and should not be committed:"
    printf '%s' "$NEW_ENV_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    echo "These files typically contain:"
    echo "  - API keys and tokens"
    echo "  - Database credentials"
    echo "  - Service URLs and secrets"
    echo ""
    echo "Recommendations:"
    echo "  1. Add to .gitignore"
    echo "  2. Use .env.example with placeholder values"
    echo "  3. Remove from staging: git reset HEAD <file>"
    echo ""
    exit 1
fi

if [ -n "$STRICT_ENV_FILES" ]; then
    echo "🚨 Error: Structured secret/config file(s) staged!"
    echo ""
    printf '%s' "$STRICT_ENV_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    echo "These files use key: value syntax, so their contents cannot be"
    echo "checked for real secrets. They are always blocked."
    echo ""
    echo "Recommendations:"
    echo "  1. Add to .gitignore"
    echo "  2. Commit a .example variant with placeholder values"
    echo "  3. Remove from staging: git reset HEAD <file>"
    echo ""
    exit 1
fi

if [ -n "$RISKY_ENV_FILES" ]; then
    echo "🚨 Error: Secret-looking value added to tracked env file(s)!"
    echo ""
    printf '%s' "$RISKY_ENV_FILES" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    echo "Added lines assign a real-looking value to a secret key"
    echo "(PASSWORD/SECRET/TOKEN/CREDENTIAL/API_KEY ...)."
    echo "Use a placeholder (dummy, \${VAR}, <value>) or move it to a secret store."
    echo ""
    exit 1
fi

exit 0
