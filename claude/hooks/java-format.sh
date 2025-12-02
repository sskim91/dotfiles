#!/bin/bash

DISABLE_FORMAT=${DISABLE_FORMAT:-0}
ENABLE_GOOGLE_JAVA_FORMAT=${ENABLE_GOOGLE_JAVA_FORMAT:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only process Java files
if [[ ! "$FILE_PATH" =~ \.java$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Exit if format is disabled
if [[ "$DISABLE_FORMAT" -eq 1 ]]; then
	exit 0
fi

echo "🔧 Running format for Java files..."

# Run format
FORMAT_SUCCESS=1

if [[ "$ENABLE_GOOGLE_JAVA_FORMAT" -eq 1 ]]; then
	echo "🔧 Running google-java-format..."
	
	# Check if google-java-format is installed
	if command -v google-java-format &> /dev/null; then
		if ! google-java-format --replace "$FILE_PATH"; then
			echo "❌ google-java-format failed" >&2
			FORMAT_SUCCESS=0
		fi
	else
		# Try to download and use it if not installed
		GJF_VERSION="1.28.0"
		GJF_JAR="$HOME/.local/bin/google-java-format-${GJF_VERSION}.jar"
		
		if [[ ! -f "$GJF_JAR" ]]; then
			echo "📦 Downloading google-java-format..."
			mkdir -p "$HOME/.local/bin"
			curl -sL "https://github.com/google/google-java-format/releases/download/v${GJF_VERSION}/google-java-format-${GJF_VERSION}-all-deps.jar" -o "$GJF_JAR"
		fi
		
		if [[ -f "$GJF_JAR" ]]; then
			if ! java -jar "$GJF_JAR" --replace "$FILE_PATH"; then
				echo "❌ google-java-format failed" >&2
				FORMAT_SUCCESS=0
			fi
		else
			echo "⚠️ google-java-format not available, skipping..." >&2
		fi
	fi
fi

if [[ "$FORMAT_SUCCESS" -eq 1 ]]; then
	echo "✅ Format completed"
else
	echo "❌ Format failed" >&2
	exit 2
fi

exit 0