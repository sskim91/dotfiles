# Git Commit Custom Command Guide

## Purpose
안전하고 체계적인 Git 커밋을 위한 커스텀 커맨드 가이드

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
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

**Company Project Commit Structure:**
```
<gitmoji> [한글 제목]

[한글 본문 - 무엇을, 왜 변경했는지 설명]
- [상세 내용]
- [변경사항 설명]
```

**Company Project Example:**
```
✨ 사용자 인증 미들웨어 추가

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
<gitmoji> [English Subject Line]

[English Body - explaining what and why]
- [Details in English]
- [Changes described in English]

<gitmoji> [한글 제목 - Same as English subject]

[한글 본문 - Same content as English body]
- [상세 내용 - Details in Korean]
- [변경사항 설명 - Changes described in Korean]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <MODEL_NAME> <noreply@anthropic.com>
```

**Note**: `<MODEL_NAME>`은 현재 사용 중인 모델명으로 대체 (예: Opus 4.5, Sonnet 4)

**Critical Requirements:**
1. **English section comes FIRST** (subject + body)
2. **Korean section comes SECOND** (제목 + 본문)
3. **Blank line** between English and Korean sections
4. **Same content** in both languages (translation, not different information)
5. Follow all the Seven Rules for commit messages in BOTH languages
6. Keep subject lines under 50 characters in both languages
7. **MUST include Claude Code signature** at the end
8. This format is **MANDATORY** for all commits in personal/open source projects

### Example:
```
✨ Add middleware system with PII detection and audit logging

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

✨ 미들웨어 시스템 추가 및 PII 탐지, 감사 로깅 구현

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

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Core Philosophy
> "A well-crafted Git commit message is the best way to communicate context about a change to fellow developers (and indeed to their future selves)."

좋은 커밋 메시지는:
- 코드 리뷰를 더 효율적으로 만듭니다
- 프로젝트 히스토리를 이해하기 쉽게 만듭니다
- 버그의 원인을 추적하기 쉽게 만듭니다
- 팀 협업의 품질을 높입니다

## Command Flow

### Phase 1: Pre-Commit Verification
1. **Check git status first**
   - `git status` 실행하여 현재 상태 파악
   - Untracked files 확인
   - Modified files 확인
   - Branch 이름 확인 (main/master가 아닌 경우 경고)

2. **Review .gitignore**
   - `.gitignore` 파일 확인
   - 민감한 파일들이 제외되었는지 검증
   - 필수 ignore 항목 체크:
     - `.env`, `.env.*` (환경 변수)
     - `*.key`, `*.pem`, `*.cert` (인증서/키 파일)
     - `node_modules/`, `venv/`, `.venv/` (의존성)
     - `.DS_Store`, `Thumbs.db` (시스템 파일)
     - `*.log`, `*.pid` (로그/프로세스 파일)
     - `.idea/`, `.vscode/` (IDE 설정 - 선택적)

3. **Sensitive Information Check**
   - 스테이징할 파일들 검사
   - 절대 커밋하면 안 되는 패턴:
     ```
     - API keys: /api[_-]?key/i
     - Passwords: /password\s*=\s*["'].+["']/i
     - Tokens: /token\s*=\s*["'].+["']/i
     - AWS credentials: /aws_access_key_id|aws_secret_access_key/i
     - Private keys: /BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY/
     ```

### Phase 2: Staging Strategy
1. **Selective Staging**
   - 전체 추가 (`git add .`) 전에 개별 파일 검토
   - 큰 바이너리 파일 체크 (>10MB)
   - Generated files 제외 확인 (build/, dist/, *.min.js)

2. **Staging Commands Priority**
   ```bash
   # 1. 먼저 수정된 파일만 확인
   git diff
   
   # 2. 개별 파일 추가 권장
   git add <specific-file>
   
   # 3. Interactive staging for complex changes
   git add -p  # 부분적으로 추가
   
   # 4. 전체 추가는 마지막 수단
   git add .  # 주의: .gitignore 확인 필수
   ```

### Phase 3: Pre-Commit Validation
1. **Diff Review**
   - `git diff --staged` 실행
   - 각 변경사항 검토
   - 의도하지 않은 변경 확인

2. **File Size Check**
   - 100MB 이상 파일 경고
   - LFS 사용 권장 대상 식별

3. **Lint/Format Check** (언어별)
   - Python: `ruff check`, `black --check`
   - JavaScript: `eslint`, `prettier --check`
   - Java: `checkstyle`, `google-java-format`

### Phase 4: Commit Message

#### The Seven Rules of a Great Git Commit Message
1. **Separate subject from body with a blank line**
2. **Limit the subject line to 50 characters**
3. **Capitalize the subject line**
4. **Do not end the subject line with a period**
5. **Use the imperative mood in the subject line**
6. **Wrap the body at 72 characters**
7. **Use the body to explain what and why vs. how**

#### Message Structure
```
<gitmoji> <subject>
                             ← Blank line
<body>
                             ← Blank line
<footer>
```

**Examples:**
```
✨ Add user authentication
🐛 Fix login page redirect issue
📝 Update API documentation
```

#### Subject Line Rules
1. **Imperative Mood Test**
   - Your subject should complete: "If applied, this commit will..."
   - ✅ Good: "Add user authentication"
   - ❌ Bad: "Added user authentication"
   - ❌ Bad: "Adding user authentication"

2. **Gitmoji Prefixes** (Required - https://gitmoji.dev/)
   - ✨ `:sparkles:` 새로운 기능 추가
   - 🐛 `:bug:` 버그 수정
   - 📝 `:memo:` 문서 추가/수정
   - 🎨 `:art:` 코드 구조/포맷 개선
   - ♻️ `:recycle:` 코드 리팩토링
   - ✅ `:white_check_mark:` 테스트 추가/수정
   - 🔧 `:wrench:` 설정 파일 변경
   - ⚡️ `:zap:` 성능 개선
   - 🔥 `:fire:` 코드/파일 삭제
   - 🚀 `:rocket:` 배포
   - 💄 `:lipstick:` UI/스타일 업데이트
   - 🔒 `:lock:` 보안 이슈 수정
   - ⬆️ `:arrow_up:` 의존성 업그레이드
   - ⬇️ `:arrow_down:` 의존성 다운그레이드
   - 🚨 `:rotating_light:` 컴파일러/린터 경고 수정
   - 🚧 `:construction:` 작업 진행 중
   - 💚 `:green_heart:` CI 빌드 수정
   - 📦 `:package:` 패키지 추가/업데이트
   - 🔀 `:twisted_rightwards_arrows:` 브랜치 병합
   - 🗑️ `:wastebasket:` 사용하지 않는 코드 정리
   - 💥 `:boom:` 주요 변경사항 (Breaking Change)

3. **Subject Examples**
   ```
   ✅ Good Examples (with Gitmoji):
   - 🐛 Fix memory leak in user session handler
   - ✨ Add OAuth2 authentication for API endpoints
   - ♻️ Refactor database connection pooling
   - 📝 Update README with installation instructions
   - ⚡️ Improve query performance by adding index
   - 🔧 Update ESLint configuration

   ❌ Bad Examples:
   - fixed bug                    # No gitmoji, too vague
   - Added new feature.           # No gitmoji, period at end, past tense
   - 🐛 changing api endpoints    # Not imperative, not capitalized
   - ✨ Fix bug in the system that was causing issues when users tried to... # Too long
   ```

#### Body Writing Guidelines
1. **Explain the Context**
   - What was the problem?
   - Why is this change necessary?
   - What are the consequences of this change?

2. **Body Template**
   ```
   [Current behavior/Problem]
   
   [Solution/Change made]
   
   [Impact/Benefits]
   ```

3. **Good Body Example**
   ```
   🐛 Fix race condition in payment processing

   The payment processor was occasionally processing the same
   payment twice when users double-clicked the submit button.

   This commit adds a mutex lock around the payment processing
   logic and implements idempotency keys to ensure each payment
   is processed exactly once.

   Fixes #842
   ```

#### Footer Guidelines
- **Issue References**: `Fixes #123`, `Closes #456`
- **Breaking Changes**: Start with `BREAKING CHANGE:`
- **Co-authors**: `Co-authored-by: name <email>`
- **Reviewed-by**: `Reviewed-by: name <email>`

#### Commit Message Quality Checklist
- [ ] Subject line completes "If applied, this commit will..."
- [ ] Subject line ≤ 50 characters
- [ ] Subject line starts with capital letter
- [ ] No period at end of subject
- [ ] Blank line between subject and body
- [ ] Body lines wrapped at 72 characters
- [ ] Body explains WHY, not HOW
- [ ] Referenced related issues/tickets

### Phase 5: Final Checks
1. **Commit Simulation**
   ```bash
   # Dry run to check what will be committed
   git commit --dry-run -v
   ```

2. **Hook Verification**
   - Pre-commit hooks 실행 확인
   - 실패 시 수정 후 재시도

### Critical Constraints (절대 금지사항)

#### 🚫 NEVER Commit:
1. **Credentials & Secrets**
   - API keys, tokens, passwords
   - Database connection strings with passwords
   - SSH private keys
   - AWS/GCP/Azure credentials
   - Encryption keys

2. **Personal Information**
   - 실제 이메일 주소 (테스트 외)
   - 전화번호, 주민번호
   - 신용카드 정보
   - 개인 식별 가능 정보 (PII)

3. **System Files**
   - `.env` files (use `.env.example` instead)
   - Local configuration files
   - IDE-specific settings (optional)
   - OS-generated files

4. **Large Files**
   - Binary files > 100MB
   - Database dumps
   - Log files
   - Cache directories

#### ⚠️ Warning Triggers:
1. **Branch Protection**
   - Direct commit to main/master
   - Force push without coordination
   - Rewriting public history

2. **File Patterns**
   - Files containing "test" or "temp" in production commits
   - TODO comments in critical code
   - Commented-out code blocks

### Emergency Rollback

If you accidentally committed sensitive data:

```bash
# 1. DO NOT PUSH YET

# 2. Remove from last commit (if not pushed)
git reset HEAD~1

# 3. If already pushed (coordinate with team)
git revert <commit-hash>

# 4. For sensitive data removal
# Use BFG Repo-Cleaner or git filter-branch
# Then force push and notify all team members
```

### Automation Script Template

```bash
#!/bin/bash
# Safe commit helper with enhanced checks

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Status check
echo "📊 Checking git status..."
git status

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    echo -e "${YELLOW}⚠️  Warning: You're on $CURRENT_BRANCH branch${NC}"
    read -p "Are you sure you want to commit directly to $CURRENT_BRANCH? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Consider creating a feature branch:"
        echo "  git checkout -b feature/your-feature-name"
        exit 1
    fi
fi

# 2. Gitignore verification
if [ ! -f .gitignore ]; then
    echo -e "${YELLOW}⚠️  Warning: No .gitignore file found!${NC}"
    read -p "Continue without .gitignore? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Sensitive pattern check (enhanced)
echo "🔍 Scanning for sensitive patterns..."
SENSITIVE_PATTERNS="(api[_-]?key|password|token|secret|private[_-]?key|credentials|aws_access_key|aws_secret)"
if git diff --staged | grep -iE "$SENSITIVE_PATTERNS"; then
    echo -e "${RED}❌ Potential sensitive data detected!${NC}"
    echo "Please review the staged changes and remove sensitive information."
    exit 1
fi

# Check for common sensitive files
SENSITIVE_FILES=".env|.env.local|.env.production|credentials|secrets"
if git diff --staged --name-only | grep -E "$SENSITIVE_FILES"; then
    echo -e "${RED}❌ Sensitive file detected in staging!${NC}"
    echo "Consider using .env.example instead"
    exit 1
fi

# 4. Large file check with better formatting
echo "📦 Checking file sizes..."
LARGE_FILES_FOUND=0
while IFS= read -r file; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$size" -gt 104857600 ]; then  # 100MB
            echo -e "${RED}❌ Large file: $file ($(numfmt --to=iec-i --suffix=B $size))${NC}"
            LARGE_FILES_FOUND=1
        elif [ "$size" -gt 10485760 ]; then  # 10MB warning
            echo -e "${YELLOW}⚠️  Large file warning: $file ($(numfmt --to=iec-i --suffix=B $size))${NC}"
        fi
    fi
done < <(git diff --staged --name-only)

if [ "$LARGE_FILES_FOUND" -eq 1 ]; then
    echo "Consider using Git LFS for large files:"
    echo "  git lfs track '*.zip' && git add .gitattributes"
    exit 1
fi

# 5. Show staged changes with context
echo "📝 Staged changes:"
git diff --staged --stat
echo ""
echo "Files to be committed:"
git diff --staged --name-status

# 6. Commit message preview
echo ""
echo "💬 Preparing commit message..."
echo "Remember the imperative mood test:"
echo "  'If applied, this commit will...'"
echo ""

# 7. Final confirmation with options
echo "Choose an action:"
echo "  [c] Commit with message"
echo "  [v] Commit with verbose mode (see diff in editor)"
echo "  [p] Review changes again (git diff --staged)"
echo "  [a] Abort"
read -p "Your choice: " -n 1 -r
echo

case $REPLY in
    c|C)
        git commit
        ;;
    v|V)
        git commit -v
        ;;
    p|P)
        git diff --staged
        echo ""
        read -p "Ready to commit? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git commit -v
        else
            echo "❌ Commit cancelled"
        fi
        ;;
    *)
        echo "❌ Commit cancelled"
        exit 0
        ;;
esac

echo -e "${GREEN}✅ Commit completed successfully!${NC}"
```

## Quick Reference

### Safe Commit Checklist
- [ ] `git status` 실행 및 확인
- [ ] `.gitignore` 파일 존재 및 내용 확인
- [ ] Sensitive data scan 완료
- [ ] Large files check 완료
- [ ] `git diff --staged` 검토
- [ ] Commit message 규칙 준수
- [ ] Branch 확인 (main/master 직접 커밋 주의)

### Command Sequence
```bash
git status                    # 1. 상태 확인
git diff                      # 2. 변경사항 검토
git add <files>              # 3. 선택적 스테이징
git diff --staged            # 4. 스테이징 검토
git commit -v                # 5. 상세 커밋 (에디터에서 diff 보며 작성)
```

### Writing Better Commits - Pro Tips

#### 1. Use `git commit -v` (verbose)
- Shows diff in your editor while writing the message
- Helps you write more accurate commit messages
- Prevents committing unintended changes

#### 2. Configure Your Editor
```bash
# Set your preferred editor
git config --global core.editor "vim"  # or "code --wait", "nano", etc.

# Enable commit message template
git config --global commit.template ~/.gitmessage
```

#### 3. Commit Message Template (~/.gitmessage)
```
# <type>(<scope>): <subject>

# <body>
# Explain what and why (not how)
# - What was the problem?
# - Why is this change necessary?
# - What effect does this change have?

# <footer>
# Fixes #<issue>
# BREAKING CHANGE: <description>
```

#### 4. Atomic Commits
- One commit = One logical change
- Don't mix refactoring with feature additions
- Split large changes into smaller, logical commits
```bash
# Stage parts of a file
git add -p

# Split previous commit
git reset HEAD~1
git add <first-logical-change>
git commit -m "First logical change"
git add <second-logical-change>
git commit -m "Second logical change"
```

## Recovery Commands

```bash
# Unstage files
git reset HEAD <file>

# Discard changes
git checkout -- <file>

# Amend last commit
git commit --amend

# Interactive rebase (local only)
git rebase -i HEAD~n
```