# Git Commit and Push Combined Command Guide

## Purpose
커밋과 푸시를 안전하고 효율적으로 한 번에 수행하기 위한 통합 커맨드 가이드

---

## ⚠️ IMPORTANT: Commit Message Format for Claude

### 🏢 Company Project Detection (HIGHEST PRIORITY)

**BEFORE writing any commit message, FIRST check if the current working directory is under `~/company-src/`:**

```bash
# Check current directory
pwd
# If path starts with /Users/sskim/company-src/, this is a COMPANY PROJECT
```

### Company Project Rules (`~/company-src/*`)

When working in a **company project** (`~/company-src/` directory):

1. **Korean ONLY** - Write commit message in Korean only (no English section)
2. **NO Claude signature** - Do NOT add the following lines:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   Co-Authored-By: Claude <MODEL_NAME> <noreply@anthropic.com>
   ```

**Company Project Commit Structure:**
```
[한글 제목]

[한글 본문 - 무엇을, 왜 변경했는지 설명]
- [상세 내용]
- [변경사항 설명]
```

**Company Project Example:**
```
사용자 인증 미들웨어 추가

보안 강화를 위한 JWT 기반 인증 시스템 구현:
- BaseMiddleware 추상 클래스 생성
- JWT 토큰 검증 로직 추가
- 권한 체크 미들웨어 구현
- 테스트 코드 작성 완료
```

---

### Personal/Open Source Project Rules (Default)

When working in **personal or open source projects** (NOT under `~/company-src/`):

You **MUST** write the ENTIRE commit message in BOTH English and Korean, with English coming FIRST.

**Required Structure:**

```
[English Subject Line]

[English Body - explaining what and why]
- [Details in English]
- [Changes described in English]

[한글 제목 - Same as English subject]

[한글 본문 - Same content as English body]
- [상세 내용 - Details in Korean]
- [변경사항 설명 - Changes described in Korean]

```

**Note**: Claude Code가 커밋 시 signature(🤖 Generated with... / Co-Authored-By)를 자동 추가함

**Critical Requirements:**
1. **English section comes FIRST** (subject + body)
2. **Korean section comes SECOND** (제목 + 본문)
3. **Blank line** between English and Korean sections
4. **Same content** in both languages (translation, not different information)
5. Follow all the Seven Rules for commit messages in BOTH languages
6. Keep subject lines under 50 characters in both languages
7. This format is **MANDATORY** for all commits in personal/open source projects

### Example:
```
Add middleware system with PII detection and audit logging

Implement production-ready middleware pattern for security and compliance:
- Create BaseMiddleware abstract class with before_request/after_response/on_error hooks
- Add PIIDetectionMiddleware for masking phone, email, SSN, card, account numbers
- Add AuditLoggingMiddleware for JSON Lines format compliance logging
- Integrate middleware support into ScheduleManagerAgent
- Add comprehensive test suite (8 tests, all passing)

Configure development tools:
- Add Ruff linter and formatter (>=0.14.0)
- Apply PEP 604 type hints (Optional[T] → T | None)
- Fix pytest import issues by removing conflicting __init__.py files
- Add build system configuration for editable install

미들웨어 시스템 추가 및 PII 탐지, 감사 로깅 구현

보안 및 규정 준수를 위한 프로덕션 수준의 미들웨어 패턴 구현:
- BaseMiddleware 추상 클래스 생성 (before_request/after_response/on_error 훅 포함)
- 전화번호, 이메일, SSN, 카드번호, 계좌번호 마스킹을 위한 PIIDetectionMiddleware 추가
- JSON Lines 형식 준수 로깅을 위한 AuditLoggingMiddleware 추가
- ScheduleManagerAgent에 미들웨어 지원 통합
- 포괄적인 테스트 스위트 추가 (8개 테스트, 모두 통과)

개발 도구 구성:
- Ruff 린터 및 포매터 추가 (>=0.14.0)
- PEP 604 타입 힌트 적용 (Optional[T] → T | None)
- 충돌하는 __init__.py 파일 제거로 pytest 임포트 문제 수정
- 편집 가능한 설치를 위한 빌드 시스템 구성 추가
```

---

## Core Philosophy
> "Commit locally, push globally. 로컬에서 완벽하게 준비한 후, 세상과 공유하세요."

통합 워크플로우의 장점:
- 작업 흐름이 끊기지 않습니다
- 실수를 줄이고 생산성을 높입니다
- 일관된 품질의 코드를 유지합니다
- 팀 협업이 더욱 원활해집니다

## Prerequisites

이 가이드는 다음 두 가이드의 내용을 통합합니다:
- 📝 [git:commit.md](git:commit.md) - 안전한 커밋 가이드
- 🚀 [git:push.md](git:push.md) - 안전한 푸시 가이드

각 단계별 상세 내용은 위 가이드를 참조하세요.

## Integrated Workflow

### 🎯 Quick Checklist
```
┌─────────────────────────────────────┐
│  COMMIT PHASE                       │
├─────────────────────────────────────┤
│ □ git status 확인                   │
│ □ .gitignore 검증                   │
│ □ 민감한 정보 스캔                   │
│ □ 파일 크기 체크                     │
│ □ 선택적 스테이징                    │
│ □ 커밋 메시지 작성 (7 Rules)         │
├─────────────────────────────────────┤
│  PUSH PHASE                         │
├─────────────────────────────────────┤
│ □ 원격 저장소 동기화                 │
│ □ 충돌 확인 및 해결                  │
│ □ 브랜치 보호 규칙 확인              │
│ □ CI/CD 파이프라인 상태              │
│ □ 최종 푸시 실행                     │
└─────────────────────────────────────┘
```

## Combined Command Flow

### Phase 1: Pre-Operation Check
```bash
# 1. 작업 디렉토리 상태 확인
git status

# 2. 원격 저장소 최신 상태 가져오기
git fetch --all

# 3. 로컬과 원격의 차이 확인
git log --oneline --graph --decorate --all -10
```

### Phase 2: Commit Preparation
Reference: [git:commit.md#phase-1-pre-commit-verification](git:commit.md)

```bash
# 1. 변경사항 검토
git diff

# 2. 민감한 정보 검사
git diff | grep -iE "(api[_-]?key|password|token|secret)"

# 3. 선택적 스테이징
git add -p  # Interactive staging
```

### Phase 3: Create Commit
Reference: [git:commit.md#the-seven-rules-of-a-great-git-commit-message](git:commit.md)

```bash
# 명령형 문법으로 작성
git commit -v  # Verbose mode로 diff 보며 작성
```

### Phase 4: Pre-Push Validation
Reference: [git:push.md#phase-1-pre-push-verification](git:push.md)

```bash
# 1. 푸시할 커밋 확인
git log origin/$(git branch --show-current)..HEAD --oneline

# 2. 충돌 가능성 체크
git diff HEAD...origin/$(git branch --show-current)
```

### Phase 5: Sync and Push
Reference: [git:push.md#phase-2-conflict-prevention](git:push.md)

```bash
# 1. 원격 변경사항 통합
git pull --rebase origin $(git branch --show-current)

# 2. 푸시 실행
git push origin $(git branch --show-current)
```

## Automated Script

```bash
#!/bin/bash
# Safe commit and push helper
# This script combines git:commit and git:push workflows

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
echo -e "${MAGENTA}    Git Commit & Push Safety Tool     ${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════${NC}"
echo ""

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📍 Current branch: $CURRENT_BRANCH${NC}"

#############################################
# PART 1: COMMIT PHASE
#############################################
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}    📝 COMMIT PHASE                    ${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. Check git status
echo "📊 Checking git status..."
git status --short

if [[ -z $(git status --short) ]]; then
    echo -e "${GREEN}✓ Working directory clean${NC}"
    echo "Nothing to commit. Checking for unpushed commits..."
else
    # 2. Check .gitignore
    if [ ! -f .gitignore ]; then
        echo -e "${YELLOW}⚠️  No .gitignore file found${NC}"
        read -p "Continue without .gitignore? (y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    fi

    # 3. Sensitive data check
    echo "🔍 Scanning for sensitive patterns..."
    if git diff | grep -qiE "(api[_-]?key|password|token|secret|private[_-]?key)"; then
        echo -e "${RED}⚠️  Potential sensitive data detected!${NC}"
        git diff | grep -iE "(api[_-]?key|password|token|secret)" | head -5
        read -p "Review complete and safe to continue? (y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    fi

    # 4. Stage changes
    echo ""
    echo "📦 Files with changes:"
    git status --short
    echo ""
    echo "How would you like to stage changes?"
    echo "  [a] Stage all changes"
    echo "  [i] Interactive staging"
    echo "  [s] Select specific files"
    echo "  [q] Quit"
    read -p "Your choice: " -n 1 -r
    echo

    case $REPLY in
        a|A)
            git add -A
            echo "✓ All changes staged"
            ;;
        i|I)
            git add -p
            ;;
        s|S)
            echo "Enter files to stage (space-separated):"
            read -r files
            git add $files
            ;;
        *)
            echo "Cancelled"
            exit 0
            ;;
    esac

    # 5. Show staged changes
    echo ""
    echo "📝 Staged changes:"
    git diff --staged --stat

    # 6. Commit with message
    echo ""
    echo -e "${BLUE}💬 Commit Message Guidelines:${NC}"
    echo "  • Use imperative mood ('Add' not 'Added')"
    echo "  • Limit subject to 50 characters"
    echo "  • Capitalize the subject line"
    echo "  • No period at the end"
    echo "  • Explain what and why, not how"
    echo ""
    echo "Ready to write commit message..."
    sleep 1
    
    # Commit
    git commit -v
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Commit failed or cancelled${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Commit created successfully${NC}"
fi

#############################################
# PART 2: PUSH PHASE
#############################################
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}    🚀 PUSH PHASE                      ${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. Check if on protected branch
PROTECTED_BRANCHES="main|master|develop|release|production"
if [[ "$CURRENT_BRANCH" =~ ^($PROTECTED_BRANCHES)$ ]]; then
    echo -e "${RED}⚠️  WARNING: Protected branch '$CURRENT_BRANCH'${NC}"
    read -p "Are you sure you want to push to $CURRENT_BRANCH? (type 'yes'): " -r
    [[ "$REPLY" != "yes" ]] && exit 1
fi

# 2. Fetch latest changes
echo "📥 Fetching latest from remote..."
git fetch origin

# 3. Check if behind remote
BEHIND=$(git rev-list --count HEAD..origin/$CURRENT_BRANCH 2>/dev/null || echo "0")
if [[ "$BEHIND" -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Branch is $BEHIND commits behind origin/$CURRENT_BRANCH${NC}"
    echo "Remote has new commits. Choose merge strategy:"
    echo "  [m] Merge"
    echo "  [r] Rebase (recommended)"
    echo "  [c] Cancel"
    read -p "Your choice: " -n 1 -r
    echo
    
    case $REPLY in
        m|M)
            git pull origin $CURRENT_BRANCH
            ;;
        r|R)
            git pull --rebase origin $CURRENT_BRANCH
            ;;
        *)
            echo "Push cancelled"
            exit 0
            ;;
    esac
fi

# 4. Show commits to push
AHEAD=$(git rev-list --count origin/$CURRENT_BRANCH..HEAD 2>/dev/null || echo "999")
if [[ "$AHEAD" -eq 0 ]]; then
    echo -e "${GREEN}✓ Already up to date with origin${NC}"
    exit 0
fi

echo -e "${BLUE}📤 Commits to push ($AHEAD):${NC}"
git log origin/$CURRENT_BRANCH..HEAD --oneline 2>/dev/null || git log --oneline -5

# 5. Large files check
echo "📦 Checking for large files..."
LARGE_FILES=$(git diff --stat origin/$CURRENT_BRANCH..HEAD 2>/dev/null | awk '$4 ~ /[0-9]+/ && $4 > 1000000 {print $1}' || echo "")
if [[ -n "$LARGE_FILES" ]]; then
    echo -e "${YELLOW}⚠️  Large files detected:${NC}"
    echo "$LARGE_FILES"
    read -p "Continue with large files? (y/n): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# 6. Final push confirmation
echo ""
echo -e "${MAGENTA}📋 Final Summary:${NC}"
echo "  Branch: $CURRENT_BRANCH → origin/$CURRENT_BRANCH"
echo "  Commits to push: $AHEAD"
echo ""

echo "Ready to push. Choose option:"
echo "  [p] Push"
echo "  [u] Push with upstream"
echo "  [f] Force with lease (⚠️)"
echo "  [c] Cancel"
read -p "Your choice: " -n 1 -r
echo

case $REPLY in
    p|P)
        git push origin $CURRENT_BRANCH
        ;;
    u|U)
        git push -u origin $CURRENT_BRANCH
        ;;
    f|F)
        echo -e "${YELLOW}⚠️  Force pushing...${NC}"
        git push --force-with-lease origin $CURRENT_BRANCH
        ;;
    *)
        echo "Push cancelled"
        exit 0
        ;;
esac

#############################################
# PART 3: POST-OPERATION
#############################################
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}    ✅ SUCCESS!                        ${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

# Show final status
echo ""
git log --oneline --graph -5
echo ""

# Post-push suggestions
echo "📌 Next steps:"
echo "  • Check CI/CD pipeline status"
echo "  • Create Pull Request if needed"
echo "  • Update issue/ticket status"

# Auto PR creation
if command -v gh &> /dev/null; then
    echo ""
    read -p "Create a Pull Request? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh pr create
    fi
elif command -v glab &> /dev/null; then
    echo ""
    read -p "Create a Merge Request? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        glab mr create
    fi
fi

echo ""
echo -e "${GREEN}All done! Happy coding! 🎉${NC}"
```

## Usage Examples

### Basic Usage
```bash
# 커밋과 푸시를 한 번에
./git-commit-and-push.sh
```

### Common Scenarios

#### 1. Feature Branch Workflow
```bash
# Feature 브랜치에서 작업 완료 후
git checkout -b feature/new-feature
# ... 코드 작업 ...
./git-commit-and-push.sh
# PR/MR 생성
```

#### 2. Hotfix Workflow
```bash
# Hotfix 브랜치에서 긴급 수정
git checkout -b hotfix/critical-bug
# ... 버그 수정 ...
./git-commit-and-push.sh
# 즉시 main에 머지
```

#### 3. Daily Work
```bash
# 일상적인 작업
# ... 코드 수정 ...
./git-commit-and-push.sh
# 자동으로 모든 검사 수행
```

## Error Handling

### Common Issues and Solutions

#### 1. Merge Conflicts
```bash
# Rebase 중 충돌 발생 시
git status  # 충돌 파일 확인
# 파일 수정
git add <resolved-files>
git rebase --continue
```

#### 2. Push Rejected
```bash
# Push 거부됨
git pull --rebase origin branch
# 충돌 해결 후
git push origin branch
```

#### 3. Large File Error
```bash
# 대용량 파일 에러
git reset HEAD~1  # 커밋 취소
git rm --cached large-file
echo "large-file" >> .gitignore
git add .gitignore
git commit -m "Remove large file and update gitignore"
```

## Best Practices

### 1. Atomic Operations
- 한 번에 하나의 기능/버그 수정
- 관련된 변경사항만 함께 커밋

### 2. Frequency
- 자주, 작은 단위로 커밋 & 푸시
- 하루 작업은 하루 안에 푸시

### 3. Communication
- 커밋 메시지로 의도 명확히 전달
- PR/MR 설명 충실히 작성

### 4. Safety First
- Protected 브랜치 직접 푸시 지양
- Force push는 최후의 수단
- 민감한 정보 항상 체크

## Quick Commands Reference

```bash
# 상태 확인
git status
git log --oneline --graph -10

# 커밋 생성
git add -p                    # Interactive staging
git commit -v                 # Verbose commit

# 동기화
git fetch --all              # 모든 원격 정보 가져오기
git pull --rebase           # Rebase로 통합

# 푸시
git push                     # 일반 푸시
git push -u origin branch    # 업스트림 설정
git push --force-with-lease  # 안전한 force push

# 되돌리기
git reset HEAD~1            # 마지막 커밋 취소
git revert HEAD             # 커밋 되돌리기
git stash                   # 임시 저장
```

## Related Guides
- 📝 [Commit Guide](git:commit.md) - 상세한 커밋 가이드
- 🚀 [Push Guide](git:push.md) - 상세한 푸시 가이드
- 📚 [Git Best Practices](https://cbea.ms/git-commit/) - 외부 참고 자료