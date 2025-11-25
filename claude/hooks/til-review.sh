#!/bin/bash

# TIL (Today I Learned) markdown review hook
# Only reviews .md files in ~/dev/TIL directory
# Gemini reviews the document and passes feedback to Claude

ENABLE_GEMINI_REVIEW=${ENABLE_GEMINI_REVIEW:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review markdown files
if [[ ! "$FILE_PATH" =~ \.md$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Check if file is under ~/dev/TIL
TIL_DIR="$HOME/dev/TIL"
if [[ ! "$FILE_PATH" =~ ^$TIL_DIR ]]; then
	exit 0
fi

# Exit if review is disabled
if [[ "$ENABLE_GEMINI_REVIEW" -ne 1 ]]; then
	exit 0
fi

echo "📝 Gemini가 TIL 문서를 리뷰 중..." >&2

# TIL-specific review prompt
# -m gemini-2.5-pro: best available model for thorough review
# --sandbox false: disable sandbox to avoid workspace restrictions
REVIEW_OUTPUT=$(cat "$FILE_PATH" | gemini -y --sandbox false -m gemini-2.5-pro -p "당신은 기술 문서 검토 전문가입니다. 아래 TIL(Today I Learned) 문서를 리뷰해주세요.

## 최우선 원칙: 정확성
- **기술적 사실 검증이 가장 중요합니다**
- 잘못된 정보, 오래된 정보, 부정확한 설명이 있다면 반드시 지적해주세요
- 확실하지 않은 내용은 웹 검색을 통해서라도 검증해주세요
- 코드 예제의 문법 오류, 잘못된 API 사용, deprecated 메서드 등을 확인해주세요

## 리뷰 항목

### 1. 기술적 정확성 (Critical)
- 기술적 사실 오류
- 잘못되거나 오래된 정보
- 코드 예제의 정확성 (컴파일/실행 가능 여부)
- API/라이브러리 버전 호환성

### 2. 문서 품질
- 문법/맞춤법 오류
- 논리적 흐름과 구성
- 마크다운 형식 적절성

### 3. 개선 제안
- 보완하면 좋을 내용
- 더 좋은 예제나 설명 방법

## 응답 형식
각 항목별로 구체적인 피드백을 제공해주세요. 문제가 없으면 '문제 없음'이라고 명시해주세요.
**한글로 답변해주세요.**" 2>&1)

# Pass Gemini's review to Claude via stderr
cat >&2 <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Gemini TIL Review
📄 File: $FILE_PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$REVIEW_OUTPUT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위 Gemini 리뷰를 참고하여 문서를 개선해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# Exit with code 2 so Claude processes the stderr output
exit 2
