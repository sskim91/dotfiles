# Commit Message Rules & Checklist

## Seven Rules of Commit Messages

1. Subject와 body를 빈 줄로 분리
2. Subject line 50자 이내
3. Subject line 대문자로 시작
4. Subject line 마침표 없음
5. Subject line은 명령형 (Add, Fix, Update - not Added, Fixed)
6. Body는 72자에서 줄바꿈
7. Body에서 **what**과 **why** 설명 (how 아님)

**Imperative Test**: "If applied, this commit will [your subject]"
- ✅ "Add user authentication"
- ❌ "Added user authentication"

## Pre-Commit Checklist

```bash
git status                    # 상태 확인
git diff                      # 변경사항 검토
git add <files>               # 선택적 스테이징
git diff --staged             # 스테이징 검토
git commit -v                 # verbose 모드로 커밋
```

## Never Commit
- Credentials (API keys, passwords, tokens)
- `.env` files
- Private keys (`*.pem`, `*.key`)
- Large binaries (>100MB)

## Warning Triggers
- Direct commit to main/master
- Files containing "test" or "temp" in production
