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

echo "Running Gemini code review for $FILE_PATH..." >&2

# 3. 개선된 프롬프트
# - Role 부여: 시니어 파이썬 엔지니어
# - 노이즈 제거: 단순 포맷팅(PEP 8 등)은 무시하라고 지시
# - 구조화: 중요도에 따라 분류
PROMPT="
You are a Senior Python Backend Engineer.
Target File: $FILE_PATH

Review the code based on the following Strict Rules:

**1. PROOF REQUIRED (Anti-Hallucination):**
   - When pointing out an issue, you **MUST quote the exact line(s) of code** from the file.
   - If you cannot find the actual line causing the issue, **DO NOT report it**.
   - Do not invent missing features if the existing logic is sufficient.

**2. IGNORE Style & Formatting:**
   - Ignore PEP 8, indentation, whitespace, missing docstrings, or variable naming styles.
   - Assume 'Black' or 'Ruff' handles formatting.

**3. FOCUS on Logic & Safety:**
   - **Runtime Errors**: Potential IndexError, KeyError, NoneType Access.
   - **Python Pitfalls**: Mutable default arguments (e.g., \`def f(x=[])\`), variable shadowing.
   - **Performance**: N+1 queries (if DB code), accidental quadratic complexity.
   - **Type Safety**: Serious type mismatches that will crash at runtime.
   - **Security**: SQL Injection, hardcoded secrets, unsafe input handling.

**4. OUTPUT:**
   - Language: Korean (한글)
   - Format: Markdown
   - If the code is safe and logical, output ONLY: 'LGTM'

**Output Template:**
### 🚨 Critical
* [Line Number]: Description
  > \`Code Snippet\`

### 💡 Suggestion
* [Line Number]: Improvement
  > \`Code Snippet\`
"

# 4. Gemini 실행
# 모델은 최신 모델 사용 권장 (gemini-2.0-flash-thinking 등도 있다면 좋음)
# 파일 내용을 직접 파이프로 넘기는 것이 @ 문법보다 호환성이 좋을 수 있습니다.
FILE_CONTENT=$(cat "$FILE_PATH")

REVIEW_OUTPUT=$(echo "$FILE_CONTENT" | gemini -y --sandbox false -m gemini-2.5-pro -p "$PROMPT" 2>&1)

# 5. 결과 처리
# LGTM이 포함되어 있거나 출력이 너무 짧으면 굳이 에러로 띄우지 않고 넘어갈 수도 있음 (선택 사항)
if [[ "$REVIEW_OUTPUT" == *"LGTM"* ]]; then
    exit 0
fi

# Claude에게 보여줄 출력
echo "---------------------------------------------------" >&2
echo "🤖 **Gemini Code Review**" >&2
echo "" >&2
echo "$REVIEW_OUTPUT" >&2
echo "---------------------------------------------------" >&2

# Exit code 2를 반환하여 Claude가 stderr를 경고처럼 표시하게 함
exit 2