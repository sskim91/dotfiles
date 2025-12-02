#!/bin/bash

ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review Java files
if [[ ! "$FILE_PATH" =~ \.java$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Exit if review is disabled
if [[ "$ENABLE_GEMINI_REVIEW" -ne 1 ]]; then
	exit 0
fi

echo "🔍 Running Gemini code review for $FILE_PATH..." >&2

# Java-specific review prompt
# NOTE: If you get ModelNotFoundError or workspace errors, try:
#   cat "$FILE_PATH" | gemini -y --sandbox false -m gemini-2.5-pro -p "..."
REVIEW_OUTPUT=$(gemini -y --sandbox false -m gemini-2.5-pro -p "@$FILE_PATH Review this Java code for:
1. Design patterns and best practices
2. Exception handling and error management
3. Thread safety and concurrency issues
4. Security vulnerabilities (input validation, SQL injection, etc.)
5. Performance optimizations (memory leaks, inefficient algorithms)
6. Proper use of Java idioms and modern Java features
7. Code style and readability
Be concise, only mention important issues.
**Please respond in Korean (한글로 답변해주세요).**" 2>&1)

# Output review to stderr so Claude can see it
echo "$REVIEW_OUTPUT" >&2

# Exit with code 2 so Claude processes the stderr output
exit 2