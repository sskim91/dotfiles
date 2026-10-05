---
name: git-commit-and-push
description: Use when user says "commit and push", "커밋하고 푸시", "올려줘", "저장하고 올려". Do NOT use for commit-only (use git-commit) or push-only (use git-push).
---

# Git Commit and Push

커밋과 푸시를 순차적으로 수행합니다.

> ⚠️ 레포에 `<project>-commit` 스킬이 **실제로 존재하면** Commit Phase가 그쪽으로 위임된다 —
> `git-commit` 스킬이 존재 확인과 위임을 함께 처리한다.

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
- [ ] 회사·OSS 레포의 protected branch 직접 push는 사용자 확인 (개인 레포는 main이어도 바로 push — `git-push` 참조)
