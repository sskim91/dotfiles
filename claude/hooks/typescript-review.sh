#!/bin/bash

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review TypeScript files
if [[ ! "$FILE_PATH" =~ \.(ts|tsx)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔍 Running AI code review for modern TypeScript in $FILE_PATH..." >&2

# TypeScript-specific modern review prompt
REVIEW_OUTPUT=$(gemini -p "@$FILE_PATH Review this TypeScript code for:
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
Be concise, focus on modern best practices and important issues only." 2>&1)

# Output review to stderr so Claude can see it
echo "$REVIEW_OUTPUT" >&2
echo "$REVIEW_OUTPUT" >>~/.gemini.log

# Exit with code 2 so Claude processes the stderr output
exit 2