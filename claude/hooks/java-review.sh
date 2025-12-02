#!/bin/bash

# 기본 활성화 여부 확인
ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

# jq 존재 여부 확인
if ! command -v jq &> /dev/null; then
    exit 0
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# 1. 파일 경로 체크 및 확장자 확인 (.java)
if [[ -z "$FILE_PATH" ]] || [[ ! "$FILE_PATH" =~ \.java$ ]] || [[ ! -f "$FILE_PATH" ]]; then
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

echo "🔍 Running Gemini code review for Java in $FILE_PATH..." >&2

# 3. 개선된 프롬프트 (Java 전문)
# - 스타일/포맷팅 무시 (Checkstyle 영역)
# - NPE, 리소스 누수(try-with-resources), 예외 처리(swallowing) 집중
# - 모던 자바(Record, Switch Expression) 제안
PROMPT="
You are a Senior Java Backend Engineer (specializing in Spring Boot and Modern Java).
Target File: $FILE_PATH

Review the code provided via input based on the following criteria:

**Review Rules (Strict):**
1. **Ignore formatting/style**: Braces, indentation, variable naming conventions, or missing Javadocs on trivial methods (getters/setters).
2. **Focus on Robustness & Safety**:
   - **Null Safety**: Potential NullPointerExceptions (NPE). Suggest \`Optional\` usage where semantic.
   - **Resource Management**: Detect unclosed streams/connections. Enforce \`try-with-resources\`.
   - **Exception Handling**: Flag empty catch blocks (swallowed exceptions) or catching generic \`Exception\` without reason.
   - **Concurrency**: If threads/locks are used, check for race conditions or thread-safety issues.
3. **Modern Java Idioms**:
   - Suggest \`Records\`, \`Switch Expressions\`, or \`var\` only if they significantly improve readability.
   - Check for inefficient Stream API usage vs simple loops.
4. **Security**: SQL Injection (if using raw JDBC), Logging sensitive data.
5. **Be Constructive**: If the code is solid, just say 'LGTM (Looks Good To Me)' and end.

**Output Format (Markdown, Korean):**
If there are issues, use this format:

### 🚨 Critical (반드시 수정 필요)
* [라인 번호]: NPE 위험, 리소스 누수, 보안 취약점, 심각한 로직 오류

### 💡 Suggestion (권장 사항)
* [라인 번호]: 모던 자바 문법(Stream, Record 등) 제안, 가독성 개선, 성능 최적화

---
**Language:** Korean (한글)
"

# 4. Gemini 실행
FILE_CONTENT=$(cat "$FILE_PATH")
REVIEW_OUTPUT=$(echo "$FILE_CONTENT" | gemini -y --sandbox false -m gemini-2.5-pro -p "$PROMPT" 2>&1)

# 5. 결과 처리
# LGTM이면 조용히 종료
if [[ "$REVIEW_OUTPUT" == *"LGTM"* ]]; then
    exit 0
fi

# Claude에게 보여줄 출력 포맷팅
echo "---------------------------------------------------" >&2
echo "🤖 **Gemini Java Review**" >&2
echo "" >&2
echo "$REVIEW_OUTPUT" >&2
echo "---------------------------------------------------" >&2

# Exit code 2로 Claude가 stderr를 읽게 함
exit 2