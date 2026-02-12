#!/bin/bash

# NOTE:
# 기본적으로 모두 비활성화 상태
ENABLE_CHECKSTYLE=${ENABLE_CHECKSTYLE:-0}
ENABLE_SPOTBUGS=${ENABLE_SPOTBUGS:-0}
ENABLE_PMD=${ENABLE_PMD:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Java files
if [[ ! "$FILE_PATH" =~ \.java$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

echo "🔧 Running check for Java files..."

# Run check
CHECK_SUCCESS=1

if [[ "$ENABLE_CHECKSTYLE" -eq 1 ]]; then
	echo "🔧 Running checkstyle..."

	# Check for checkstyle configuration
	if [[ -f "checkstyle.xml" ]] || [[ -f ".checkstyle.xml" ]]; then
		CONFIG_FILE=$(ls checkstyle.xml .checkstyle.xml 2>/dev/null | head -1)
	else
		# Use Google Java Style if no config exists
		CONFIG_FILE="/google_checks.xml"
	fi

	if command -v checkstyle &> /dev/null; then
		if ! checkstyle -c "$CONFIG_FILE" "$FILE_PATH"; then
			echo "❌ checkstyle check failed" >&2
			CHECK_SUCCESS=0
		fi
	else
		echo "⚠️ checkstyle not installed, skipping..." >&2
	fi
fi

if [[ "$ENABLE_SPOTBUGS" -eq 1 ]]; then
	echo "🔧 Running SpotBugs..."

	# SpotBugs requires compiled .class files
	if command -v spotbugs &> /dev/null; then
		# Try to compile the file first if needed
		CLASS_FILE="${FILE_PATH%.java}.class"
		if [[ ! -f "$CLASS_FILE" ]] || [[ "$FILE_PATH" -nt "$CLASS_FILE" ]]; then
			javac "$FILE_PATH" 2>/dev/null
		fi

		if [[ -f "$CLASS_FILE" ]]; then
			if ! spotbugs -textui "$CLASS_FILE"; then
				echo "❌ SpotBugs check failed" >&2
				CHECK_SUCCESS=0
			fi
		else
			echo "⚠️ Could not compile Java file for SpotBugs analysis" >&2
		fi
	else
		echo "⚠️ SpotBugs not installed, skipping..." >&2
	fi
fi

if [[ "$ENABLE_PMD" -eq 1 ]]; then
	echo "🔧 Running PMD..."

	if command -v pmd &> /dev/null; then
		# Use default Java ruleset
		if ! pmd check -d "$FILE_PATH" -R rulesets/java/quickstart.xml -f text; then
			echo "❌ PMD check failed" >&2
			CHECK_SUCCESS=0
		fi
	else
		echo "⚠️ PMD not installed, skipping..." >&2
	fi
fi

if [[ "$CHECK_SUCCESS" -eq 1 ]]; then
	echo "✅ All checks passed"
else
	echo "❌ Check failed. Please fix the issues above." >&2
	exit 2
fi

exit 0
