#!/bin/bash

ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review TypeScript files
if [[ ! "$FILE_PATH" =~ \.(ts|tsx)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Exit if review is disabled
if [[ "$ENABLE_GEMINI_REVIEW" -ne 1 ]]; then
	exit 0
fi

echo "🔍 Running AI code review for modern TypeScript in $FILE_PATH..." >&2

# TypeScript-specific modern review prompt
# NOTE: If you get ModelNotFoundError or workspace errors, try:
#   cat "$FILE_PATH" | gemini -y --sandbox false -m gemini-2.5-pro -p "..."
REVIEW_OUTPUT=$(gemini -y --sandbox false -m gemini-2.5-pro -p "@$FILE_PATH Review this TypeScript code for:
1. Modern TypeScript features usage (strict types, const assertions, template literal types)
2. Type safety and proper use of generics
3. React hooks best practices (if applicable)
4. Modern async patterns (async/await, Promise handling)
5. Performance optimizations (useMemo, useCallback, lazy loading)
6. Security issues (XSS prevention, input validation)
7. Modern module patterns and tree-shaking compatibility
8. Proper error boundaries and error handling
9. Accessibility considerations for UI components
10. Use of modern ECMAScript features appropriately
Be concise, focus on modern best practices and important issues only.
**Please respond in Korean (한글로 답변해주세요).**" 2>&1)

# Output review to stderr so Claude can see it
echo "$REVIEW_OUTPUT" >&2

# Exit with code 2 so Claude processes the stderr output
exit 2