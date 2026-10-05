# Commit Message Rules & Checklist

## Commit Message Rules

1. Subject와 body를 빈 줄로 분리
2. Subject line 50자 이내 (`type(scope): ` 포함)
3. Subject line 마침표 없음
4. 한국어 subject는 명사로 끝냄 (추가, 수정, 변경), English subject는 명령형 (add, fix, update - not added, fixed)
5. Body는 72자에서 줄바꿈
6. Body에서 **what**과 **why** 설명 (how 아님)

**Imperative Test** (English subject): "If applied, this commit will [your subject]"
- ✅ "add user authentication"
- ❌ "added user authentication"

## Pre-Commit Checklist

```bash
git status                    # 상태 확인
git diff                      # 변경사항 검토
git add <files>               # 선택적 스테이징
git diff --staged             # 스테이징 검토
git commit -F - <<'EOF'       # 메시지는 heredoc으로 전달 (에디터를 열지 않음)
type(scope): 제목

본문
EOF
```

## Never Commit
- Credentials (API keys, passwords, tokens)
- `.env` files
- Private keys (`*.pem`, `*.key`)
- Large binaries (>100MB)

## Warning Triggers
- Files containing "test" or "temp" in production
