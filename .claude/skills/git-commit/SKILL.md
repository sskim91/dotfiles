---
name: git-commit
description: Use when user wants to commit changes, says "commit", "커밋", "커밋해줘", "변경사항 저장". Do NOT use for pushing (use git-push) or commit-and-push (use git-commit-and-push).
---

# Git Commit Instructions

## 경로 분기 (CRITICAL)

**FIRST**: `pwd`로 현재 디렉토리 확인.

| 경로 | 프로젝트 타입 | 언어 |
|------|-------------|------|
| `~/company-src/*`, `~/work/*` | 회사 | Korean |
| `~/dev/oss/*` | OSS 기여 | English |
| 그 외 모든 경로 | 개인 | Korean |

**Attribution**: settings.json의 `attribution`으로 관리. 스킬에서 직접 추가하지 않음.

## 커밋 메시지 포맷

```
[제목 (한글 or English — 경로 분기 따름)]

[본문 - 무엇을, 왜 변경했는지]
- [상세 내용]
```

## 참고 자료

| 파일 | 내용 |
|------|------|
| [commit-rules.md](references/commit-rules.md) | 7 Rules, Pre-Commit Checklist, Never Commit 목록 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ Gitmoji 사용 → 사용하지 않음
- ❌ Co-Authored-By나 "Generated with Claude" 직접 추가 → settings.json attribution이 관리함
- ❌ Subject에 마침표 붙임 → 마침표 없음
- ❌ Past tense 사용 ("Added") → 명령형 ("Add")
- ❌ `git add .` 또는 `git add -A` → 파일 지정해서 스테이징
- ❌ 개인 프로젝트에서 영어 커밋 → Korean이 기본, `~/dev/oss/*`만 English
