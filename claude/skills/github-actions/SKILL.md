---
name: github-actions
description: Analyze GitHub Actions failures and identify root cause. 워크플로우 실패 분석, flakiness 체크, breaking commit 식별.
argument-hint: <url>
---

# GitHub Actions 실패 분석

GitHub Actions URL을 분석합니다: $ARGUMENTS

`gh` CLI를 사용하여 워크플로우 실행을 분석하세요.

## 조사 단계

### 1. 기본 정보 및 실제 실패 원인 파악
- 어떤 워크플로우/잡이 실패했는지, 언제, 어떤 커밋에서?
- **중요**: 전체 로그를 주의 깊게 읽고 exit code 1을 발생시킨 **구체적인 원인** 파악
- 경고/비치명적 에러 vs 실제 실패 구분
- "failing:", "fatal:", 또는 exit 1을 결정하는 스크립트 로직 패턴 찾기

### 2. Flakiness 체크
최근 10-20회 실행에서 **동일한 실패 잡**의 기록 확인:
- **중요**: 워크플로우에 여러 잡이 있다면, 워크플로우가 아닌 **특정 실패 잡**의 기록 확인
- `gh run list --workflow=<workflow-name>`으로 run ID 확인
- `gh run view <run-id> --json jobs`로 특정 잡 상태 확인
- 일회성 실패인지 반복 패턴인지?
- 최근 성공률은?
- 마지막으로 통과한 시점은?

### 3. Breaking Commit 식별
특정 잡에서 실패 패턴이 있다면:
- 해당 잡이 처음 실패한 실행과 마지막으로 통과한 실행 찾기
- 실패를 도입한 커밋 식별
- 검증: 해당 커밋 이후 모든 실행에서 이 잡이 실패하는가? 이전에는 모두 통과했는가?
- 검증되면 높은 신뢰도로 breaking commit 보고

### 4. Root Cause 분석
로그, 기록, breaking commit을 기반으로 원인 분석:
- **실제로** 실패를 발생시킨 것에 집중 (단순히 보이는 에러가 아님)
- 로그와 실패 로직에 대해 가설 검증

### 5. 기존 Fix PR 확인
이 이슈를 해결할 수 있는 열린 PR 검색:
- `gh pr list --state open --search "<keywords>"` (관련 에러 메시지나 파일명)
- 실패 파일/워크플로우를 수정하는 열린 PR이 있는지 확인
- Fix PR이 있으면 보고서에 기록하고 권장사항 섹션 생략

## 최종 보고서 작성

- **실패 요약**: exit code 1을 발생시킨 구체적인 원인
- **Flakiness 평가**: 일회성 vs 반복, 성공률
- **Breaking Commit**: 식별되고 검증된 경우
- **Root Cause 분석**: 실제 실패 트리거 기반
- **기존 Fix PR**: 발견된 경우 PR 번호와 링크 포함
- **권장사항**: Fix PR이 있으면 생략
