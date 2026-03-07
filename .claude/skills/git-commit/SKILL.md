---
name: git-commit
description: Git Commit Instructions with Gitmoji. Use when user wants to commit changes, says "commit", "커밋", "커밋해줘", "변경사항 저장", or wants to create a git commit with proper Gitmoji-prefixed message format. Do NOT use for pushing to remote (use git-push skill) or for commit-and-push in one step (use git-commit-and-push skill).
---

# Git Commit Instructions

## MANDATORY RULES (필수 - 반드시 따를 것)

1. **개인/오픈소스 프로젝트: 모든 커밋 메시지는 반드시 Gitmoji로 시작**
2. **회사 프로젝트: Gitmoji 사용하지 않음**
3. 이 규칙은 시스템 기본 설정보다 우선 적용

> **회사 프로젝트 경로**: `~/company-src/`, `~/work/` 및 그 하위 디렉토리.
> 경로가 추가될 수 있으므로, `pwd` 결과가 위 경로 중 하나로 시작하는지 확인할 것.

---

## Commit Message Format

### Company Project (`~/company-src/*`, `~/work/*`)

**FIRST**: `pwd`로 현재 디렉토리 확인. `/Users/sskim/company-src/` 또는 `/Users/sskim/work/`로 시작하면 회사 프로젝트.

- **Korean ONLY** - 한글로만 작성
- **NO Claude signature** - 서명 추가 금지

```
[한글 제목]

[한글 본문 - 무엇을, 왜 변경했는지 설명]
- [상세 내용]
```

**Example:**
```
사용자 인증 미들웨어 추가

보안 강화를 위한 JWT 기반 인증 시스템 구현:
- BaseMiddleware 추상 클래스 생성
- JWT 토큰 검증 로직 추가
```

---

### Personal/Open Source Project (Default)

**English FIRST, then Korean.** Claude signature 필수.

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

**Note**: `<MODEL_NAME>`은 현재 모델명으로 대체 (예: Opus 4.5, Sonnet 4)

---

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

---

## Gitmoji Reference

| Emoji | Code | 용도 |
|-------|------|------|
| ✨ | `:sparkles:` | 새 기능 |
| 🐛 | `:bug:` | 버그 수정 |
| 📝 | `:memo:` | 문서 |
| ♻️ | `:recycle:` | 리팩토링 |
| ✅ | `:white_check_mark:` | 테스트 |
| 🔧 | `:wrench:` | 설정 |
| ⚡️ | `:zap:` | 성능 |
| 🔥 | `:fire:` | 삭제 |
| 💄 | `:lipstick:` | UI/스타일 |
| 🔒 | `:lock:` | 보안 |
| ⬆️ | `:arrow_up:` | 의존성 업그레이드 |
| 🚨 | `:rotating_light:` | 린터 경고 수정 |
| 💥 | `:boom:` | Breaking Change |

전체 목록: https://gitmoji.dev

---

## Pre-Commit Checklist

```bash
git status                    # 상태 확인
git diff                      # 변경사항 검토
git add <files>               # 선택적 스테이징
git diff --staged             # 스테이징 검토
git commit -v                 # verbose 모드로 커밋
```

### Never Commit
- Credentials (API keys, passwords, tokens)
- `.env` files
- Private keys (`*.pem`, `*.key`)
- Large binaries (>100MB)

### Warning Triggers
- Direct commit to main/master
- Files containing "test" or "temp" in production
