#!/bin/bash

# TIL (Today I Learned) markdown review hook
# Only reviews .md files in ~/dev/TIL directory
#
# TIL_REVIEW_MODE:
#   chain  (default) — Codex primary + Gemini verification, parallel
#   codex           — Codex only
#   gemini          — Gemini only (legacy)

ENABLE_TIL_REVIEW=${ENABLE_TIL_REVIEW:-1}
TIL_REVIEW_MODE=${TIL_REVIEW_MODE:-chain}

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

# Only review markdown files
if [[ ! "$FILE_PATH" =~ \.md$ ]] || [[ ! -f "$FILE_PATH" ]]; then
	exit 0
fi

# Skip agent context files (not TIL documents)
case "$(basename "$FILE_PATH")" in
	GEMINI.md|AGENTS.md|CLAUDE.md) exit 0 ;;
esac

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
CODEX_MODEL="${TIL_CODEX_MODEL:-gpt-5.5}"
GEMINI_MODEL="${TIL_GEMINI_MODEL:-gemini-3-flash-preview}"

# Per-tool timeout (seconds). With 1 auto-retry, worst case = 2 × timeout per tool.
# Hook timeout in settings.json must be > 2 × max(CODEX_TIMEOUT, GEMINI_TIMEOUT).
CODEX_TIMEOUT=${TIL_CODEX_TIMEOUT:-120}
GEMINI_TIMEOUT=${TIL_GEMINI_TIMEOUT:-120}

# Portable timeout (no coreutils dependency on macOS).
# Returns 124 on timeout (GNU convention), otherwise the command's exit code.
run_with_timeout() {
	local secs=$1; shift
	"$@" &
	local pid=$!
	(
		sleep "$secs"
		kill -TERM "$pid" 2>/dev/null && {
			sleep 2
			kill -KILL "$pid" 2>/dev/null
		}
	) &
	local watchdog=$!
	wait "$pid" 2>/dev/null
	local rc=$?
	kill -TERM "$watchdog" 2>/dev/null
	wait "$watchdog" 2>/dev/null
	# 143 = 128 + SIGTERM; treat as timeout
	if [[ $rc -eq 143 || $rc -eq 137 ]]; then
		return 124
	fi
	return $rc
}

# Shared review rubric. Keep model-specific execution rules in the wrappers below.
BASE_REVIEW_RUBRIC_PROMPT="**오늘 날짜: $(date +%Y-%m-%d)**

**중요: 제공된 단일 TIL 문서만 리뷰하세요.**
**날짜 확인이 필요하면 위에 제공된 오늘 날짜를 사용하세요.**
**모델별 전용 지침과 공통 루브릭이 충돌하면 모델별 전용 지침을 우선하세요.**

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

### 검증/환각 방지
- 문서에 **실제로 존재하는 내용만** 지적하세요.
- **공백/띄어쓰기 문제는 절대 지적하지 마세요.** 특히 코드나 경로에 \"공백이 포함되어 있다\"는 식의 지적은 흔한 환각입니다.
- 100% 확신이 없으면 지적하지 말고 '없음'으로 처리하세요.
- 지적할 때는 **왜 문제인지**와 **어떻게 고치면 되는지**를 구체적으로 쓰세요.
- 균형을 유지하세요. Blocker는 엄격하게, Refinement/Insight는 눈에 띄는 경우만 작성하세요.

### Blocker 판정 전 체크
Blocker를 제기하기 전 반드시 다음 3가지를 확인하세요:
1. 문서의 정확한 문장 또는 코드 조각이 실제로 존재하는가?
2. 왜 독자에게 잘못된 학습을 유발하는가?
3. 수정 방향이 명확한가?

이 셋 중 하나라도 부족하면 Blocker가 아니라 Refinement로 낮추거나 '없음'으로 처리하세요.

### 선택 우선순위
- Refinement 후보가 여러 개라면 독자의 오해를 가장 크게 줄이는 1개만 선택하세요.
- Insight 후보가 여러 개라면 문서 주제와 가장 직접적으로 연결되는 1개만 선택하세요.

## 리뷰 항목

### 1. 🚫 Blocker (즉시 수정 필요)
- **이 항목이 하나라도 있으면 문서는 통과되지 않습니다.**
- 문서 내부에서 확인 가능한 기술적 사실 오류 (틀린 정보, 잘못된 개념 설명)
- 독자에게 잘못된 학습을 유발하는 명백한 개념 오류

**Blocker가 아닌 것:**
- 예시 코드의 단순화된 예외 처리
- 스타일 선호도 차이
- 더 나은 방법이 있을 수 있는 경우
- 개념 설명을 위한 의사 코드(Pseudo-code)의 문법

### 2. 💡 Refinement (개선 제안 - 수정 선택)
- **있다면 최대 1개만.** 억지로 찾지 마세요. 없으면 '없음'.
- 독자의 이해도를 높이거나, 설명을 더 명확하게 만드는 제안
- 누락된 중요 정보, 모호한 설명, 논리적 비약

**Refinement가 아닌 것 (절대 제안하지 마세요):**
- 예시 코드의 스타일 개선
- \`throws Exception\` → 구체적 예외 변경
- shutdown() 메서드 추가, 리소스 정리 코드 추가
- 개인적 선호도에 기반한 제안
- TIL은 개인 학습 노트입니다. 가벼운 hedging 문장(\"중요하다\", \"유용하다\" 등)은 사고 흔적이니 지적하지 마세요.

### 3. 🎓 Insight (심화 학습 - 수정 불필요)
- **있다면 최대 1개만.** 독자가 더 깊이 학습할 수 있는 방향을 제시하세요. 없으면 '없음'.
- 관련된 심화 주제, 실무에서 마주칠 수 있는 상황, 면접 질문
- 문서 내용과 연결되는 구체적인 인사이트"

OUTPUT_FORMAT_PROMPT="
## 응답 형식
1. 반드시 아래 섹션명을 그대로 사용하세요: \`## Blocker\`, \`## Refinement\`, \`## Insight\`
2. 해당 사항이 없으면 섹션 본문에 '없음'만 작성하세요.
3. **응답의 가장 마지막 줄에 반드시 다음 중 하나를 출력하세요. 이 라인은 절대 생략 금지:**
   - Blocker가 '없음'이면: \`STATUS: PASS\`
   - Blocker가 하나 이상 있으면: \`STATUS: FAIL\`
   - 위 두 형식 외 다른 변형(예: STATUS:PASS, Status: pass, ✅ PASS)은 금지. 정확히 \`STATUS: PASS\` 또는 \`STATUS: FAIL\`만 사용.
4. 한글로 답변하세요.
5. **깔끔하게 끝내세요. 불필요한 칭찬이나 요약은 생략하세요. STATUS 라인 뒤에는 어떤 텍스트도 추가하지 마세요.**

출력 예시 (Blocker 없음):
## Blocker
없음

## Refinement
없음

## Insight
없음

STATUS: PASS

출력 예시 (Blocker 있음):
## Blocker
3번 섹션의 \"X는 항상 Y를 보장한다\"는 설명은 문서의 뒤쪽 예시와 모순됩니다. 조건부로만 성립한다고 수정해야 합니다.

## Refinement
없음

## Insight
없음

STATUS: FAIL"

CODEX_REVIEW_PROMPT="당신은 Codex CLI로 실행되는 Claude Code PostToolUse 훅의 Primary TIL 리뷰어입니다.

파일 수정, apply_patch, diff 생성, 셸 명령 실행을 하지 마세요.
파일 시스템 탐색이나 저장소 구조 분석을 하지 마세요.

$BASE_REVIEW_RUBRIC_PROMPT

## Codex 전용: 사실 검증과 공식 출처 확인
당신은 \`web_search=\"live\"\`로 실행됩니다. 다음처럼 **공식 출처로 검증 가능한 기술 사실**을 담당하세요:

1. 문서가 다음 중 하나라도 다룬다면 **반드시 1회 이상 web_search를 호출**하세요:
   - 라이브러리/프레임워크/언어의 특정 API, 함수, 메서드, 옵션
   - 버전 번호, 릴리즈일, 지원 종료일(EOL)
   - Deprecated 여부, 권장 대체 API
   - 외부 URL 링크
2. 코드 문법 오류로 인해 **컴파일/실행이 불가능**한 경우는 Blocker로 다루세요.
3. 문서 내용이 당신의 기존 지식과 충돌하면 web_search로 확인하세요.
4. 일반 개념 설명, 예시 코드 스타일, 문서 내부에서 충분히 확인 가능한 내용은 검색하지 마세요.
5. Blocker로 사실 오류를 지적할 때는 **확인한 공식 문서 URL을 1줄로 인용**하세요. (예: \`근거: https://docs.python.org/3/...\`)
6. 공식 출처로 Deprecated API 사용이 확인되면 Blocker로 다루고 대안을 명시하세요.
7. 외부 URL 출처 링크가 깨졌거나 명백히 잘못된 경우에는 Refinement로 다루세요. 로컬 파일 링크는 검증하지 마세요.
8. 검색 결과가 문서 내용과 일치하면 침묵하세요 (\"확인 결과 정확합니다\" 같은 사족 금지). 불일치할 때만 Blocker/Refinement에 반영하세요.
9. 검색했지만 명확한 출처를 못 찾았다면 Blocker로 단정하지 말고 Refinement에서 \"확인 필요\"로만 다루세요.
10. 공식 문서나 신뢰 가능한 출처가 없으면 Deprecated/API/version 관련 내용을 Blocker로 단정하지 마세요.

$OUTPUT_FORMAT_PROMPT"

GEMINI_REVIEW_PROMPT="당신은 Gemini CLI로 실행되는 비대화형 TIL Verification 리뷰어입니다.
당신은 Codex Primary 리뷰어와 **병렬로** 실행되며, 그의 결과를 보지 못합니다.
따라서 Codex와 같은 사실 검증을 반복하려 하지 말고, **Primary가 놓치기 쉬운 영역에 가중치**를 두세요.

파일 탐색, 셸 명령 실행, 웹 검색을 하지 마세요.

$BASE_REVIEW_RUBRIC_PROMPT

## Gemini 전용: 차별화된 검토 관점
Codex Primary는 코드 문법 오류와, 공식 출처로 검증 가능한 사실 오류/API/Deprecated 문제를 담당합니다.
당신은 **문서 내부의 의미와 독자 이해**를 우선적으로 살피세요:

1. **개념적/논리적 오류**: 비유의 부정확성, 인과관계 오류, 일반화 오류 (\"항상\", \"절대\"의 오용)
2. **누락된 전제/맥락**: 코드는 맞지만 그 코드가 의미 있게 동작하기 위한 전제 조건이 빠진 경우
3. **독자 오해 유발 표현**: 다른 언어/프레임워크 배경의 독자가 잘못 추론할 수 있는 표현
4. **Insight의 깊이**: 사실 검증보다 문서 주제와 직접 연결되는 심화 학습 포인트 1개에 집중하세요

## Gemini 전용: 사실 검증 제한
- 외부 지식이 필요한 최신 버전, Deprecated 여부, 링크 유효성은 Codex가 검증합니다. 당신은 이런 내용을 Blocker로 단정하지 마세요.
- 문서 안의 설명만으로 명백한 모순이나 오해가 확인될 때만 Blocker/Refinement로 제시하세요.
- 외부 확인이 필요해 보이면 Refinement에서 \"공식 출처 확인 필요\" 정도로만 언급하세요.
- 차별화에 집착해 억지로 다른 지적을 만들지 마세요. 문서 내부 기준으로 명백한 Blocker는 Codex와 겹쳐도 그대로 보고하세요.

$OUTPUT_FORMAT_PROMPT"

# Temp files for parallel runs (so both reviewers can write concurrently)
TMPDIR_REVIEW=$(mktemp -d)
trap 'rm -rf "$TMPDIR_REVIEW"' EXIT

_codex_invoke() {
	cd "$TIL_DIR" && cat "$FILE_PATH" | \
		codex exec -m "$CODEX_MODEL" \
			--ephemeral \
			--sandbox read-only \
			--skip-git-repo-check \
			--output-last-message "$TMPDIR_REVIEW/codex.txt" \
			-c 'approval_policy="never"' \
			-c 'web_search="live"' \
			"$CODEX_REVIEW_PROMPT" \
			>"$TMPDIR_REVIEW/codex.stdout" 2>"$TMPDIR_REVIEW/codex.err"
}

run_codex() {
	run_with_timeout "$CODEX_TIMEOUT" _codex_invoke
	local rc=$?
	if [[ $rc -eq 124 ]]; then
		echo "⚠️  Codex 1차 timeout(${CODEX_TIMEOUT}s) — 자동 재시도 중..." >&2
		run_with_timeout "$CODEX_TIMEOUT" _codex_invoke
		rc=$?
	fi
	if [[ $rc -eq 124 ]]; then
		printf '## Blocker\n없음\n\n## Refinement\n없음\n\n## Insight\n없음\n\nSTATUS: ERROR\n[SYSTEM] Codex 리뷰가 %ss × 2회 모두 timeout되었습니다. 리뷰 인프라 장애이므로 문서 수정으로 해결되지 않습니다. 다음 파일로 넘어가지 말고 사용자에게 보고하세요.\n' \
			"$CODEX_TIMEOUT" > "$TMPDIR_REVIEW/codex.txt"
	fi
	return $rc
}

_gemini_invoke() {
	cd "$TIL_DIR" && cat "$FILE_PATH" | \
		gemini -y --sandbox false -m "$GEMINI_MODEL" \
			"$GEMINI_REVIEW_PROMPT" \
			>"$TMPDIR_REVIEW/gemini.txt" 2>"$TMPDIR_REVIEW/gemini.err"
}

run_gemini() {
	run_with_timeout "$GEMINI_TIMEOUT" _gemini_invoke
	local rc=$?
	if [[ $rc -eq 124 ]]; then
		echo "⚠️  Gemini 1차 timeout(${GEMINI_TIMEOUT}s) — 자동 재시도 중..." >&2
		run_with_timeout "$GEMINI_TIMEOUT" _gemini_invoke
		rc=$?
	fi
	if [[ $rc -eq 124 ]]; then
		printf '## Blocker\n없음\n\n## Refinement\n없음\n\n## Insight\n없음\n\nSTATUS: ERROR\n[SYSTEM] Gemini 리뷰가 %ss × 2회 모두 timeout되었습니다. 리뷰 인프라 장애이므로 문서 수정으로 해결되지 않습니다. 다음 파일로 넘어가지 말고 사용자에게 보고하세요.\n' \
			"$GEMINI_TIMEOUT" > "$TMPDIR_REVIEW/gemini.txt"
	fi
	return $rc
}

case "$TIL_REVIEW_MODE" in
	codex)
		echo "📝 Codex($CODEX_MODEL)가 TIL 문서를 리뷰 중..." >&2
		run_codex
		CODEX_STATUS=$?
		;;
	gemini)
		echo "📝 Gemini($GEMINI_MODEL)가 TIL 문서를 리뷰 중..." >&2
		run_gemini
		GEMINI_STATUS=$?
		;;
	chain|*)
		echo "📝 Codex($CODEX_MODEL) + Gemini($GEMINI_MODEL) 병렬 리뷰 중..." >&2
		run_codex &
		CODEX_PID=$!
		run_gemini &
		GEMINI_PID=$!
		wait "$CODEX_PID"
		CODEX_STATUS=$?
		wait "$GEMINI_PID"
		GEMINI_STATUS=$?
		;;
esac

# Pass review outputs to Claude via stderr
{
	echo ""
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	echo "🤖 TIL Review (mode: $TIL_REVIEW_MODE)"
	echo "📄 File: $FILE_PATH"
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

	if [[ -s "$TMPDIR_REVIEW/codex.txt" ]]; then
		echo ""
		echo "─── 1️⃣ Codex ($CODEX_MODEL) Primary Review ───"
		cat "$TMPDIR_REVIEW/codex.txt"
	elif [[ "$TIL_REVIEW_MODE" != "gemini" ]]; then
		echo ""
		echo "─── 1️⃣ Codex ($CODEX_MODEL) Primary Review ───"
		echo "Codex review failed or produced no output. exit_status=${CODEX_STATUS:-unknown}"
		if [[ -s "$TMPDIR_REVIEW/codex.err" ]]; then
			echo "--- codex stderr (last 20 lines) ---"
			tail -n 20 "$TMPDIR_REVIEW/codex.err"
		fi
		echo "STATUS: ERROR"
		echo "[SYSTEM] 리뷰 도구 자체가 실패했습니다. 문서 수정으로 해결되지 않으니 사용자에게 보고하세요."
	fi

	if [[ -s "$TMPDIR_REVIEW/gemini.txt" ]]; then
		echo ""
		echo "─── 2️⃣ Gemini ($GEMINI_MODEL) Verification ───"
		cat "$TMPDIR_REVIEW/gemini.txt"
	elif [[ "$TIL_REVIEW_MODE" != "codex" ]]; then
		echo ""
		echo "─── 2️⃣ Gemini ($GEMINI_MODEL) Verification ───"
		echo "Gemini review failed or produced no output. exit_status=${GEMINI_STATUS:-unknown}"
		if [[ -s "$TMPDIR_REVIEW/gemini.err" ]]; then
			echo "--- gemini stderr (last 20 lines) ---"
			tail -n 20 "$TMPDIR_REVIEW/gemini.err"
		fi
		echo "STATUS: ERROR"
		echo "[SYSTEM] 리뷰 도구 자체가 실패했습니다. 문서 수정으로 해결되지 않으니 사용자에게 보고하세요."
	fi

	echo ""
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	echo "위 리뷰를 참고하여 문서를 개선해주세요."
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
} >&2

# Exit with code 2 so Claude processes the stderr output
exit 2
