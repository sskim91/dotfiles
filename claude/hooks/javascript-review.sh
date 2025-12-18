#!/bin/bash

# 기본 활성화 여부 확인
ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

# jq 존재 여부 확인
if ! command -v jq &> /dev/null; then
    exit 0
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# 1. 파일 경로 체크 및 확장자 확인 (.js, .jsx, .mjs, .cjs)
if [[ -z "$FILE_PATH" ]] || [[ ! "$FILE_PATH" =~ \.(js|jsx|mjs|cjs)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# 2. 리뷰 기능 활성화 체크
if [[ "$ENABLE_GEMINI_REVIEW" -ne 1 ]]; then
	exit 0
fi

# gemini CLI 도구 확인
if ! command -v gemini &> /dev/null; then
    echo "⚠️ 'gemini' CLI tool not found. Skipping review." >&2
    exit 0
fi

echo "🔍 Running Gemini code review for Modern JavaScript in $FILE_PATH..." >&2

# 3. 개선된 프롬프트 (Modern JavaScript 전문)
# - 스타일/포맷팅 무시 (Prettier/ESLint 영역)
# - 레거시 패턴(var) 지양, 비동기 실수(forEach 내 await 등) 체크
# - React(.jsx)일 경우 DOM 직접 접근이나 State 변형 체크
PROMPT="
You are a Senior JavaScript Engineer.
Target File: $FILE_PATH

Review the code provided via input based on the following criteria:

**Review Rules (Strict):**
1. **Ignore formatting/style** (semicolons, indentation, quotes, trailing commas) - Assume Prettier/ESLint handles them.
2. **Focus on Logic & Modern Standards**:
   - **Legacy Issues**: Usage of \`var\` instead of \`const/let\`.
   - **Async Pitfalls**: Using \`await\` inside \`forEach\` (should use \`for...of\` or \`Promise.all\`), missing \`try/catch\` in async functions.
   - **Equality**: Loose equality \`==\` (unless explicitly needed for null checks).
   - **Modern Syntax**: Suggest Optional Chaining (\`?.\`) or Nullish Coalescing (\`??\`) to simplify verbose checks.
3. **Frontend Specifics (if React/JSX used)**:
   - Direct DOM manipulation (using \`document.querySelector\` instead of refs).
   - Mutating state directly.
4. **Security**: usage of \`eval()\`, \`innerHTML\` (XSS risk), or Prototype Pollution risks.
5. **Be Constructive**: If the code is solid, just say 'LGTM (Looks Good To Me)' and end.

**Output Format (Markdown, Korean):**
If there are issues, use this format:

### 🚨 Critical (반드시 수정 필요)
* [라인 번호]: 버그, 심각한 비동기 로직 오류, 보안 취약점

### 💡 Suggestion (권장 사항)
* [라인 번호]: 더 간결한 ES6+ 문법 제안, 성능 개선

---
**Language:** Korean (한글)
"

# 4. Gemini 실행
FILE_CONTENT=$(cat "$FILE_PATH")
REVIEW_OUTPUT=$(echo "$FILE_CONTENT" | gemini -y --sandbox false -m gemini-3-flash-preview "$PROMPT" 2>&1 | grep -v -E "^\[STARTUP\]|^YOLO mode|^Loaded cached")

# 5. 결과 처리
# LGTM이면 조용히 종료
if [[ "$REVIEW_OUTPUT" == *"LGTM"* ]]; then
    exit 0
fi

# Claude에게 보여줄 출력 포맷팅
echo "---------------------------------------------------" >&2
echo "🤖 **Gemini JavaScript Review**" >&2
echo "" >&2
echo "$REVIEW_OUTPUT" >&2
echo "---------------------------------------------------" >&2

# Exit code 2로 Claude가 stderr를 읽게 함
exit 2