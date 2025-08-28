#!/bin/bash

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review JavaScript files
if [[ ! "$FILE_PATH" =~ \.(js|jsx|mjs|cjs)$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔍 Running AI code review for modern JavaScript in $FILE_PATH..." >&2

# JavaScript-specific modern review prompt
REVIEW_OUTPUT=$(gemini -p "@$FILE_PATH Review this modern JavaScript code for:
1. ES2024+ feature usage (optional chaining, nullish coalescing, private fields)
2. Modern async patterns (async/await, Promise.allSettled, AbortController)
3. React/Vue/Svelte best practices (if applicable)
4. Performance optimizations (Web Workers, lazy loading, code splitting)
5. Security issues (prototype pollution, XSS, injection attacks)
6. Modern module patterns (ESM, dynamic imports, tree-shaking)
7. Proper error handling and defensive programming
8. Web API usage best practices (fetch, IntersectionObserver, etc.)
9. Memory leak prevention and cleanup
10. Accessibility and semantic HTML (for frontend code)
11. Modern bundler compatibility (Vite, ESBuild, SWC)
Be concise, focus on modern JavaScript patterns and critical issues only." 2>&1)

# Output review to stderr so Claude can see it
echo "$REVIEW_OUTPUT" >&2
echo "$REVIEW_OUTPUT" >>~/.gemini.log

# Exit with code 2 so Claude processes the stderr output
exit 2