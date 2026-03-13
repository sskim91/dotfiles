#!/bin/bash

# TIL (Today I Learned) markdown review hook
# Only reviews .md files in ~/dev/TIL directory
# Gemini reviews the document and passes feedback to Claude

ENABLE_TIL_REVIEW=${ENABLE_TIL_REVIEW:-0}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review markdown files
if [[ ! "$FILE_PATH" =~ \.md$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Skip GEMINI.md (context file, not a TIL document)
if [[ "$(basename "$FILE_PATH")" == "GEMINI.md" ]]; then
	exit 0
fi

# Check if file is under ~/dev/TIL
TIL_DIR="$HOME/dev/TIL"
if [[ ! "$FILE_PATH" =~ ^$TIL_DIR ]]; then
	exit 0
fi

# Exit if review is disabled
if [[ "$ENABLE_TIL_REVIEW" -ne 1 ]]; then
	exit 0
fi

# Skip translated articles (translate-article skill output)
SKIP_TRANSLATED_REVIEW=${SKIP_TRANSLATED_REVIEW:-0}
if [[ "$SKIP_TRANSLATED_REVIEW" -eq 1 ]] && grep -q "한국어로 번역한 글입니다" "$FILE_PATH" 2>/dev/null; then
	echo "⏭️ 번역 문서 리뷰 스킵: $(basename "$FILE_PATH")" >&2
	exit 0
fi

# Model configuration
GEMINI_MODEL="gemini-3-flash-preview"

echo "📝 Gemini($GEMINI_MODEL)가 TIL 문서를 리뷰 중..." >&2

# TIL-specific review prompt
# --sandbox false: disable sandbox to avoid workspace restrictions
# TIL 디렉토리에서 실행: GEMINI.md를 자동으로 컨텍스트로 읽음
# grep -v로 CLI 시작 로그 및 에이전트 thinking 출력 필터링
REVIEW_OUTPUT=$(cd "$TIL_DIR" && cat "$FILE_PATH" | gemini -y --sandbox false -m "$GEMINI_MODEL" "당신은 꼼꼼하고 건설적인 기술 문서 검토 전문가입니다.

**오늘 날짜: $(date +%Y-%m-%d)** (Deprecated API 판단 기준)

**중요: stdin으로 제공된 단일 문서만 리뷰하세요. 파일 시스템의 다른 파일을 탐색하지 마세요. 단, 사실 검증을 위한 웹 검색은 허용됩니다.**

아래 TIL(Today I Learned) 문서를 리뷰해주세요.

## TIL 문서의 특성 (반드시 이해하세요)
- **학습 노트**입니다. 프로덕션 코드가 아닙니다.
- 예시 코드의 목적은 **개념 전달**입니다. 완벽한 예외 처리나 스타일은 요구되지 않습니다.
- \`throws Exception\`, 간략화된 에러 처리 등은 **의도된 단순화**입니다. 지적하지 마세요.

## 리뷰 철학: 균형 잡힌 피드백
- **문제가 있을 때만 지적하세요.** 억지로 개선점을 찾지 마세요.
- 사소한 스타일 선호도가 아닌, **독자에게 실질적 가치를 주는** 피드백만 제공하세요.
- 좋은 문서라면 '없음'으로 끝내는 것이 올바른 리뷰입니다.

## 리뷰 원칙

### ⚠️ 환각 방지 (CRITICAL - 반드시 읽으세요)
- **공백/띄어쓰기 문제는 절대 지적하지 마세요.** 이것은 흔한 환각입니다.
- 코드나 경로에 \"공백이 포함되어 있다\"고 절대 말하지 마세요 (예: \"' @vitejs/...'에 공백\" - 이건 환각).
- 100% 확신이 없으면 **지적하지 마세요**.
- 의심스러우면 '없음'으로 끝내세요. 환각보다 나은 선택입니다.

### 검증 규칙
1. **지적 전 검증 필수**: 지적하기 전에 문서에서 해당 내용이 **실제로 존재하는지** 다시 확인하세요.
   - **허위 지적은 신뢰를 떨어뜨립니다.**
2. **구체적으로**: '더 좋을 것 같다'가 아니라, **왜** 더 좋은지, **어떻게** 고치면 되는지 명시하세요.
3. **균형 유지**: Blocker는 엄격하게, Refinement/Insight는 눈에 띄는 경우만.

## 리뷰 항목

### 1. 🚫 Blocker (즉시 수정 필요)
- **이 항목이 하나라도 있으면 문서는 통과되지 않습니다.**
- 기술적 사실 오류 (틀린 정보, 잘못된 개념 설명)
- 코드 문법 오류로 인해 **컴파일/실행이 불가능**한 경우
- Deprecated API 사용 (대안 명시 필요)

**Blocker가 아닌 것:**
- 예시 코드의 단순화된 예외 처리
- 스타일 선호도 차이
- 더 나은 방법이 있을 수 있는 경우
- 개념 설명을 위한 의사 코드(Pseudo-code)의 문법

### 2. 💡 Refinement (개선 제안 - 수정 선택)
- **있다면 최대 1개만.** 억지로 찾지 마세요. 없으면 '없음'.
- 독자의 이해도를 높이거나, 설명을 더 명확하게 만드는 제안
- 누락된 중요 정보, 모호한 설명, 논리적 비약
- 외부 URL 출처 링크가 깨졌거나 명백히 잘못된 경우 (로컬 파일 링크는 검증하지 마세요)

**좋은 Refinement 예시:**
- \"2.3절에서 X 개념을 언급했지만 정의가 없습니다. 간단한 설명을 추가하면 좋겠습니다.\"
- \"Before/After 비교에서 After가 왜 더 나은지 이유가 명시되지 않았습니다.\"
- \"다이어그램과 본문 설명이 약간 다릅니다. A는 B라고 했는데 다이어그램에서는 C로 표시됨.\"

**Refinement가 아닌 것 (절대 제안하지 마세요):**
- 예시 코드의 스타일 개선
- \`throws Exception\` → 구체적 예외 변경
- shutdown() 메서드 추가, 리소스 정리 코드 추가
- 개인적 선호도에 기반한 제안

### 3. 🎓 Insight (심화 학습 - 수정 불필요)
- **있다면 최대 1개만.** 독자가 더 깊이 학습할 수 있는 방향을 제시하세요. 없으면 '없음'.
- 관련된 심화 주제, 실무에서 마주칠 수 있는 상황, 면접 질문
- 문서 내용과 연결되는 구체적인 인사이트

**좋은 Insight 예시:**
- \"이 패턴은 실무에서 X 상황에 자주 사용됩니다. Y 프레임워크의 Z 기능과 비교해보면 좋습니다.\"
- \"면접에서 'A와 B의 차이점'이 자주 출제됩니다. 이 문서의 내용을 바탕으로 정리해두면 좋겠습니다.\"

## 응답 형식
1. 각 항목별로 피드백을 작성하세요. 해당 사항이 없으면 '없음'으로 깔끔하게 마무리.
2. **Blocker가 '없음'이면, 마지막 줄에 반드시:** STATUS: PASS
3. 한글로 답변하세요.
4. **깔끔하게 끝내세요. 불필요한 칭찬이나 요약은 생략하세요.**" 2>/dev/null)

# Pass Gemini's review to Claude via stderr
cat >&2 <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Gemini ($GEMINI_MODEL) TIL Review
📄 File: $FILE_PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$REVIEW_OUTPUT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위 Gemini 리뷰를 참고하여 문서를 개선해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# Exit with code 2 so Claude processes the stderr output
exit 2
