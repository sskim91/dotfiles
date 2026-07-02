---
name: git-commit-and-push
description: Use when user says "commit and push", "커밋하고 푸시", "올려줘", "저장하고 올려". Do NOT use for commit-only (use git-commit) or push-only (use git-push).
---

# Git Commit and Push

커밋과 푸시를 순차적으로 수행합니다.

> ⚠️ **GenOS 레포** (`~/work/GenOS`, 또는 `.claude/skills/genos-commit/` 존재) 에서는
> Commit Phase가 **`genos-commit` 스킬**로 위임된다 — `git-commit` 스킬이 이 위임을 처리한다.

## Workflow

1. **Commit Phase** — `git-commit` 스킬의 규칙을 **그대로** 따른다 (프로젝트 위임, 경로 분기, 메시지 포맷, Gotchas 포함). 커밋 절차를 이 스킬에서 재정의하지 않는다.
2. **Push Phase** — `git-push` 스킬 참조

## Quick Flow

```bash
# 1. Commit Phase — git-commit 스킬 규칙대로 수행

# 2. 동기화 & 푸시
git pull --rebase origin $(git branch --show-current)
git push origin $(git branch --show-current)
```

## Checklist

- [ ] 민감한 정보 없음
- [ ] 테스트 통과
- [ ] 커밋 메시지 규칙 준수 (/git-commit 참조)
- [ ] Protected branch 직접 push 주의
