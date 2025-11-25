#!/bin/bash

# File dispatcher that routes to appropriate language-specific hooks based on file extension

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
HOOK_TYPE="${1:-format}"  # format, check, or review

# Determine file extension - TypeScript and JavaScript are now separate
if [[ "$FILE_PATH" =~ \.py$ ]]; then
	LANGUAGE="python"
elif [[ "$FILE_PATH" =~ \.java$ ]]; then
	LANGUAGE="java"
elif [[ "$FILE_PATH" =~ \.(ts|tsx)$ ]]; then
	LANGUAGE="typescript"
elif [[ "$FILE_PATH" =~ \.(js|jsx|mjs|cjs)$ ]]; then
	LANGUAGE="javascript"
elif [[ "$FILE_PATH" =~ \.(go)$ ]]; then
	LANGUAGE="go"
elif [[ "$FILE_PATH" =~ \.(rs)$ ]]; then
	LANGUAGE="rust"
elif [[ "$FILE_PATH" =~ \.(cpp|cc|cxx|h|hpp)$ ]]; then
	LANGUAGE="cpp"
elif [[ "$FILE_PATH" =~ \.md$ ]] && [[ "$FILE_PATH" =~ ^$HOME/dev/TIL ]]; then
	LANGUAGE="til"
else
	# No specific handler for this file type
	exit 0
fi

# Construct hook script path
HOOK_SCRIPT="$(dirname "$0")/${LANGUAGE}-${HOOK_TYPE}.sh"

# Check if the hook script exists
if [[ -f "$HOOK_SCRIPT" ]]; then
	# Execute the appropriate hook script
	echo "$INPUT" | "$HOOK_SCRIPT"
	exit $?
else
	# No hook for this language/type combination
	exit 0
fi