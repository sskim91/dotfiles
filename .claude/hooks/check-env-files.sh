#!/bin/bash
# Check for .env files and similar configuration files
# .env 파일이 커밋되는 것을 방지

# 환경 변수 파일 패턴
ENV_PATTERNS="(^|/)\.env($|\.local$|\.development$|\.production$|\.staging$|\.test$)"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)\.env\.[^.]+$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)config\.local\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)secrets?\.(json|yaml|yml|toml)$"
ENV_PATTERNS="$ENV_PATTERNS|(^|/)credentials\.(json|yaml|yml|toml)$"

# 안전한 파일 패턴 (플레이스홀더만 포함, 커밋 허용)
SAFE_PATTERNS="\.(example|sample|template)$"

# git diff에서 추가된 파일 중 환경 변수 파일 체크 (안전한 파일 제외)
ENV_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E "$ENV_PATTERNS" | grep -Ev "$SAFE_PATTERNS" || true)

if [ -n "$ENV_FILES" ]; then
    echo "🚨 Error: Environment/Config file(s) detected!"
    echo ""
    echo "The following files should NOT be committed:"
    echo "$ENV_FILES" | while read -r file; do
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

exit 0
