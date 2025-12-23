#!/bin/bash

# 기본적으로 활성화 여부 확인 (환경 변수가 없으면 0)
ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

# jq가 없으면 조용히 종료 (오류 방지)
if ! command -v jq &> /dev/null; then
    exit 0
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# 1. 파일 경로가 없거나, Python 파일이 아니거나, 실제 파일이 없으면 종료
if [[ -z "$FILE_PATH" ]] || [[ ! "$FILE_PATH" =~ \.py$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# 2. 리뷰 기능이 꺼져있으면 종료
if [[ "$ENABLE_GEMINI_REVIEW" -ne 1 ]]; then
	exit 0
fi

# gemini CLI 도구 존재 여부 확인
if ! command -v gemini &> /dev/null; then
    echo "⚠️ 'gemini' CLI tool not found. Skipping review." >&2
    exit 0
fi

# Model configuration
GEMINI_MODEL="gemini-3-flash-preview"

echo "🔍 Running Gemini($GEMINI_MODEL) code review for $FILE_PATH..." >&2

# 3. 개선된 프롬프트
# - Role 부여: 시니어 파이썬 엔지니어
# - 노이즈 제거: 단순 포맷팅(PEP 8 등)은 무시하라고 지시
# - 구조화: 중요도에 따라 분류
# - 환각 방지 규칙 대폭 강화
PROMPT="
You are a Senior Python Backend Engineer.
Target File: $FILE_PATH

Review the code based on the following Strict Rules:

**1. ANTI-HALLUCINATION (CRITICAL - READ CAREFULLY):**
   - **NEVER report whitespace/spacing issues** in import paths, strings, or variable names.
   - **NEVER claim there is a space** where there is none. This is a common hallucination.
   - Before reporting ANY issue, **copy-paste the exact characters** from the code.
   - If you are not 100% certain the issue exists, **DO NOT report it**.
   - **DO NOT imagine** problems that don't exist in the actual code.
   - When quoting code, quote it **EXACTLY as written** - do not add or remove characters.

**2. PROOF REQUIRED:**
   - When pointing out an issue, you **MUST quote the exact line(s) of code** from the file.
   - The quoted code must be a **verbatim copy** - no modifications.
   - If you cannot find the actual problematic code, **DO NOT report it**.

**3. ABSOLUTELY IGNORE (DO NOT MENTION):**
   - PEP 8, indentation, whitespace, formatting
   - Import path spacing (e.g., DO NOT say \"there's a space in '@vitejs/...'\" - this is hallucination)
   - Missing docstrings, variable naming styles
   - Assume 'Black' or 'Ruff' handles all formatting

**4. ONLY REPORT these Logic & Safety issues:**
   - **Runtime Errors**: Potential IndexError, KeyError, NoneType Access
   - **Python Pitfalls**: Mutable default arguments (e.g., \`def f(x=[])\`), variable shadowing
   - **Performance**: N+1 queries (if DB code), accidental quadratic complexity
   - **Type Safety**: Serious type mismatches that will crash at runtime
   - **Security**: SQL Injection, hardcoded secrets, unsafe input handling

**5. OUTPUT:**
   - Language: Korean (한글)
   - Format: Markdown
   - **If no REAL logic/safety issues exist, output ONLY: 'LGTM'**
   - When in doubt, output 'LGTM' rather than risk hallucinating

**Output Template:**
### 🚨 Critical
* [Line Number]: Description
  > \`EXACT code from file - verbatim copy\`

### 💡 Suggestion
* [Line Number]: Improvement
  > \`EXACT code from file - verbatim copy\`
"

# 4. Gemini 실행
# Gemini 3 Flash 모델 사용
FILE_CONTENT=$(cat "$FILE_PATH")

REVIEW_OUTPUT=$(echo "$FILE_CONTENT" | gemini -y --sandbox false -m "$GEMINI_MODEL" "$PROMPT" 2>&1 | grep -v -E "^\[STARTUP\]|^YOLO mode|^Loaded cached")

# 5. 결과 처리
# LGTM이 포함되어 있거나 출력이 너무 짧으면 굳이 에러로 띄우지 않고 넘어갈 수도 있음 (선택 사항)
if [[ "$REVIEW_OUTPUT" == *"LGTM"* ]]; then
    exit 0
fi

# Claude에게 보여줄 출력
echo "---------------------------------------------------" >&2
echo "🤖 **Gemini ($GEMINI_MODEL) Python Review**" >&2
echo "" >&2
echo "$REVIEW_OUTPUT" >&2
echo "---------------------------------------------------" >&2

# Exit code 2를 반환하여 Claude가 stderr를 경고처럼 표시하게 함
exit 2