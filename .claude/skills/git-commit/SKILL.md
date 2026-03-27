---
name: git-commit
description: Use when user wants to commit changes, says "commit", "커밋", "커밋해줘", "변경사항 저장". Do NOT use for pushing (use git-push) or commit-and-push (use git-commit-and-push).
---

# Git Commit Instructions

## 경로 분기 (CRITICAL)

**FIRST**: `pwd`로 현재 디렉토리 확인.

| 경로 | 프로젝트 타입 | Gitmoji | 언어 | Claude 서명 |
|------|-------------|---------|------|------------|
| `~/company-src/*`, `~/work/*` | 회사 | ❌ | Korean ONLY | ❌ |
| 그 외 모든 경로 | 개인/오픈소스 | ✅ | English + Korean | ✅ |

## 회사 프로젝트 포맷

```
[한글 제목]

[한글 본문 - 무엇을, 왜 변경했는지]
- [상세 내용]
```

## 개인/오픈소스 포맷

```
<gitmoji> [English Subject]

[English Body]
- [Details]

<gitmoji> [한글 제목]

[한글 본문]
- [상세 내용]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <MODEL_NAME> <noreply@anthropic.com>
```

`<MODEL_NAME>`은 현재 모델명으로 대체 (예: Opus 4.6, Sonnet 4.6)

## 참고 자료

| 파일 | 내용 |
|------|------|
| [gitmoji-table.md](references/gitmoji-table.md) | Gitmoji 전체 테이블 |
| [commit-rules.md](references/commit-rules.md) | 7 Rules, Pre-Commit Checklist, Never Commit 목록 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ 회사 프로젝트에서 Gitmoji 사용 → `pwd` 먼저 확인
- ❌ 회사 프로젝트에서 Claude 서명 추가 → 절대 금지
- ❌ Subject에 마침표 붙임 → 마침표 없음
- ❌ Past tense 사용 ("Added") → 명령형 ("Add")
- ❌ `git add .` 또는 `git add -A` → 파일 지정해서 스테이징
