---
name: git-commit-and-push
description: Commit and push changes in one workflow combining git-commit (Gitmoji) and git-push skills. Use when user says "commit and push", "커밋하고 푸시", "올려줘", "저장하고 올려", or wants to stage, commit, and push in one step. Do NOT use for commit only without push (use git-commit skill) or for push only without new commit (use git-push skill).
---

# Git Commit and Push

커밋과 푸시를 순차적으로 수행합니다.

## Workflow

1. **Commit Phase** - `/git-commit` 스킬 참조
2. **Push Phase** - `/git-push` 스킬 참조

## Quick Flow

```bash
# 1. 상태 확인
git status
git fetch origin

# 2. 스테이징 & 커밋
git add <files>
git commit -v

# 3. 동기화 & 푸시
git pull --rebase origin $(git branch --show-current)
git push origin $(git branch --show-current)
```

## Checklist

- [ ] 민감한 정보 없음
- [ ] 테스트 통과
- [ ] 커밋 메시지 규칙 준수 (/git-commit 참조)
- [ ] Protected branch 직접 push 주의
