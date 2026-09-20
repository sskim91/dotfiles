#!/usr/bin/env bash
# 특정 페이지 구간의 머리말/꼬리말을 덤프한다. 쪽번호 오독을 눈으로 가려낼 때 쓴다.
# 사용: page-context.sh FILE.pdf 첫페이지 끝페이지
set -euo pipefail

f="${1:?PDF 경로}"; a="${2:?시작 페이지}"; b="${3:?끝 페이지}"

for ((p = a; p <= b; p++)); do
  t=$(pdftotext -f "$p" -l "$p" -layout "$f" - 2>/dev/null | grep -v '^[[:space:]]*$' || true)
  echo "--- p$p"
  echo "$t" | head -2 | cut -c1-100
  echo "$t" | tail -2 | cut -c1-100
done
