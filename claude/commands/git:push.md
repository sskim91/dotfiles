# Git Push Custom Command Guide

## Purpose
안전하고 체계적인 Git Push를 위한 커스텀 커맨드 가이드

## Core Philosophy
> "Push는 팀과 코드를 공유하는 마지막 관문입니다. 한 번 push된 히스토리는 되돌리기 어렵습니다."

안전한 Push는:
- 팀의 작업을 방해하지 않습니다
- 프로젝트 히스토리를 깨끗하게 유지합니다
- CI/CD 파이프라인을 안정적으로 유지합니다
- 충돌과 병합 문제를 최소화합니다

## Command Flow

### Phase 1: Pre-Push Verification

#### 1. Local Repository Status Check
```bash
# 현재 상태 확인
git status

# 커밋되지 않은 변경사항 확인
git diff
git diff --staged

# stash가 필요한지 확인
git stash list
```

#### 2. Branch Verification
```bash
# 현재 브랜치 확인
git branch --show-current

# 원격 브랜치와의 관계 확인
git branch -vv

# 보호된 브랜치 체크
PROTECTED_BRANCHES="main|master|develop|release|production"
```

#### 3. Remote Repository Sync
```bash
# 원격 저장소 최신 정보 가져오기
git fetch --all --prune

# 로컬과 원격의 차이 확인
git log HEAD..origin/$(git branch --show-current) --oneline
git log origin/$(git branch --show-current)..HEAD --oneline
```

### Phase 2: Conflict Prevention

#### 1. Check for Upstream Changes
```bash
# 원격에 새로운 커밋이 있는지 확인
git fetch origin
git status -uno

# 충돌 가능성 미리 확인
git diff HEAD...origin/$(git branch --show-current)
```

#### 2. Merge or Rebase Strategy
```bash
# Option 1: Merge (히스토리 보존)
git pull origin $(git branch --show-current)

# Option 2: Rebase (깨끗한 히스토리)
git pull --rebase origin $(git branch --show-current)

# Rebase 충돌 시
git rebase --abort  # 취소
git rebase --continue  # 계속
```

### Phase 3: Pre-Push Validation

#### 1. Commit History Review
```bash
# 푸시할 커밋들 확인
git log origin/$(git branch --show-current)..HEAD --oneline

# 커밋 메시지 품질 확인
git log origin/$(git branch --show-current)..HEAD --format="%h %s" | while read line; do
    # 50자 제한 체크
    # 명령형 문법 체크
    # 타입 프리픽스 체크
done
```

#### 2. Large Files Check
```bash
# 푸시할 커밋의 파일 크기 확인
git diff --stat origin/$(git branch --show-current)..HEAD

# 100MB 이상 파일 검색
git rev-list --objects origin/$(git branch --show-current)..HEAD | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {if ($3 > 104857600) print $4 " " $3}'
```

#### 3. Sensitive Data Final Check
```bash
# 민감한 정보 최종 스캔
git diff origin/$(git branch --show-current)..HEAD | \
  grep -E "(api[_-]?key|password|token|secret|private[_-]?key)"
```

### Phase 4: Push Strategies

#### 1. Standard Push
```bash
# 현재 브랜치를 원격에 푸시
git push origin $(git branch --show-current)

# 업스트림 설정과 함께 푸시
git push -u origin $(git branch --show-current)
```

#### 2. Force Push (위험!)
```bash
# ⚠️ 절대 공유 브랜치에서 사용 금지
# 개인 feature 브랜치에서만 사용

# Force with lease (더 안전함)
git push --force-with-lease origin $(git branch --show-current)

# 일반 force push (매우 위험)
# git push --force origin $(git branch --show-current)
```

#### 3. Push with Tags
```bash
# 태그와 함께 푸시
git push origin $(git branch --show-current) --tags

# 특정 태그만 푸시
git push origin v1.0.0
```

### Phase 5: Post-Push Actions

#### 1. Verify Push Success
```bash
# 푸시 확인
git log origin/$(git branch --show-current) -1

# 원격 브랜치 상태 확인
git ls-remote origin
```

#### 2. CI/CD Pipeline Check
- GitHub Actions, GitLab CI, Jenkins 등 확인
- 빌드 상태 모니터링
- 테스트 결과 확인

#### 3. Pull Request / Merge Request
```bash
# GitHub CLI 사용 시
gh pr create --title "Feature: ..." --body "..."

# GitLab CLI 사용 시
glab mr create --title "Feature: ..." --description "..."
```

## Critical Constraints (절대 금지사항)

### 🚫 NEVER Push:

1. **To Protected Branches Without Review**
   - main/master 직접 push
   - release 브랜치 직접 push
   - PR/MR 없는 production push

2. **Broken Code**
   - 컴파일 실패 코드
   - 테스트 실패 코드
   - Linter 에러가 있는 코드

3. **Large Binary Files**
   - 100MB 이상 파일
   - Generated files (node_modules, .pyc, etc.)
   - Build artifacts

4. **Sensitive Information**
   - Credentials, API keys
   - .env files
   - Private keys, certificates

### ⚠️ Warning Situations:

1. **Force Push Warnings**
   - 공유 브랜치에 force push
   - 다른 사람의 커밋 덮어쓰기
   - CI/CD 진행 중 push

2. **Merge Conflicts**
   - 해결되지 않은 충돌
   - 자동 병합된 충돌 검토 필요

## Push Safety Checklist

### Before Push:
- [ ] 모든 변경사항이 커밋되었는가?
- [ ] 원격 저장소와 동기화되었는가?
- [ ] 충돌이 모두 해결되었는가?
- [ ] 테스트가 통과하는가?
- [ ] 커밋 메시지가 규칙을 따르는가?
- [ ] 민감한 정보가 없는가?
- [ ] 대용량 파일이 없는가?

### Push Command Priority:
1. `git push` (일반 push)
2. `git push -u origin branch` (업스트림 설정)
3. `git push --force-with-lease` (안전한 force)
4. ~~`git push --force`~~ (사용 금지)

## Automation Script

```bash
#!/bin/bash
# Safe push helper

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 Git Push Safety Check"
echo "========================"

# 1. Check uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️  Uncommitted changes detected${NC}"
    git status -s
    read -p "Stash changes and continue? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "Auto-stash before push $(date +%Y%m%d_%H%M%S)"
        echo "Changes stashed"
    else
        exit 1
    fi
fi

# 2. Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}Current branch: $CURRENT_BRANCH${NC}"

# 3. Check if it's a protected branch
PROTECTED_BRANCHES="main|master|develop|release|production"
if [[ "$CURRENT_BRANCH" =~ ^($PROTECTED_BRANCHES)$ ]]; then
    echo -e "${RED}⚠️  WARNING: You're pushing to a protected branch: $CURRENT_BRANCH${NC}"
    read -p "Are you ABSOLUTELY sure? (type 'yes' to confirm): " -r
    if [[ "$REPLY" != "yes" ]]; then
        echo "Push cancelled"
        exit 1
    fi
fi

# 4. Fetch latest changes
echo "📥 Fetching latest changes..."
git fetch origin

# 5. Check if behind remote
BEHIND=$(git rev-list --count HEAD..origin/$CURRENT_BRANCH)
if [[ "$BEHIND" -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Your branch is $BEHIND commits behind origin/$CURRENT_BRANCH${NC}"
    echo "You need to pull/merge/rebase first:"
    echo "  git pull origin $CURRENT_BRANCH"
    echo "  OR"
    echo "  git pull --rebase origin $CURRENT_BRANCH"
    exit 1
fi

# 6. Show commits to be pushed
AHEAD=$(git rev-list --count origin/$CURRENT_BRANCH..HEAD)
if [[ "$AHEAD" -eq 0 ]]; then
    echo -e "${GREEN}✓ Already up to date with origin${NC}"
    exit 0
fi

echo -e "${BLUE}📤 Commits to push ($AHEAD):${NC}"
git log origin/$CURRENT_BRANCH..HEAD --oneline

# 7. Check for large files
echo "📦 Checking for large files..."
LARGE_FILES=$(git diff --stat origin/$CURRENT_BRANCH..HEAD | awk '$4 ~ /[0-9]+/ && $4 > 1000000 {print $1 " (" $4 " bytes)"}')
if [[ -n "$LARGE_FILES" ]]; then
    echo -e "${YELLOW}⚠️  Large files detected:${NC}"
    echo "$LARGE_FILES"
    read -p "Continue with large files? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 8. Check for sensitive patterns
echo "🔍 Scanning for sensitive data..."
if git diff origin/$CURRENT_BRANCH..HEAD | grep -qiE "(api[_-]?key|password|token|secret)"; then
    echo -e "${RED}⚠️  Potential sensitive data detected!${NC}"
    echo "Please review your changes carefully"
    git diff origin/$CURRENT_BRANCH..HEAD | grep -iE "(api[_-]?key|password|token|secret)" | head -5
    read -p "I've reviewed and it's safe to push (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 9. Final confirmation
echo ""
echo "📋 Push Summary:"
echo "  Branch: $CURRENT_BRANCH"
echo "  Remote: origin"
echo "  Commits: $AHEAD"
echo ""

echo "Choose push type:"
echo "  [1] Normal push"
echo "  [2] Push with upstream (-u)"
echo "  [3] Force with lease (⚠️ careful)"
echo "  [4] Cancel"
read -p "Your choice: " -n 1 -r
echo

case $REPLY in
    1)
        echo "Executing: git push origin $CURRENT_BRANCH"
        git push origin $CURRENT_BRANCH
        ;;
    2)
        echo "Executing: git push -u origin $CURRENT_BRANCH"
        git push -u origin $CURRENT_BRANCH
        ;;
    3)
        echo -e "${YELLOW}⚠️  Force pushing with lease...${NC}"
        echo "Executing: git push --force-with-lease origin $CURRENT_BRANCH"
        git push --force-with-lease origin $CURRENT_BRANCH
        ;;
    *)
        echo "Push cancelled"
        exit 0
        ;;
esac

echo -e "${GREEN}✅ Push completed successfully!${NC}"

# 10. Post-push actions
echo ""
echo "📌 Next steps:"
echo "  - Check CI/CD pipeline status"
echo "  - Create/update Pull Request if needed"
echo "  - Notify team members if necessary"

# Check if hub/gh is installed for PR creation
if command -v gh &> /dev/null; then
    read -p "Create a Pull Request? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh pr create
    fi
fi
```

## Recovery Commands

### Undo Push (위험!)
```bash
# 로컬에서 커밋 취소
git reset --hard HEAD~1

# Force push로 원격 업데이트 (팀과 상의 필수!)
git push --force-with-lease origin branch

# 또는 revert 사용 (더 안전)
git revert HEAD
git push origin branch
```

### Recover from Failed Push
```bash
# Push 실패 시
git pull --rebase origin branch
# 충돌 해결
git rebase --continue
git push origin branch
```

### Branch Recovery
```bash
# 잘못된 브랜치에 push한 경우
git push origin :wrong-branch  # 원격 브랜치 삭제
git checkout correct-branch
git cherry-pick <commit-hash>
git push origin correct-branch
```