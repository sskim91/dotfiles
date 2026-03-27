---
name: cc-team-builder
description: Use when user mentions "agent team", "에이전트 팀", "team spawn", "create team", "팀 구성", "팀 만들어", "병렬로 검토/조사/개발". Do NOT use for single subagent dispatch (use superpowers:dispatching-parallel-agents).
---

# Create Agent Team

사용자의 자연어 요청을 Agent Team으로 연결한다. 목적·역할·규모는 자유롭게 판단하되, 아래 실행 순서와 함정 회피 규칙은 반드시 따른다.

## Prerequisites

Agent Teams가 활성화되어 있어야 한다. 비활성 상태라면 안내:

```json
// ~/.claude/settings.json 또는 프로젝트 .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## 실행 순서

1. 사용자 요청에서 팀 구성을 추론하여 제안. 작업 목적이 불명확하면 "어떤 작업을 위한 팀인가요?" 한 번만 질문한 뒤 구성을 제안한다.
2. 사용자 확인
3. **TeamCreate**로 팀 생성
4. **Agent tool**로 각 팀원 spawn (`team_name` 지정)
5. 모든 팀원 완료 후 결과 종합

## 함정 회피

Claude가 일반 지식으로는 놓치기 쉬운, Agent Team 특유의 실전 문제들:

| 함정 | 대응 |
|------|------|
| 팀원끼리 같은 파일을 동시 수정 → 충돌 | 각 팀원의 담당 파일/디렉토리를 명시적으로 분리 |
| 리더가 팀원 완료 전에 먼저 결론 | 프롬프트에 "Wait for all teammates to complete" 명시 |
| 팀원이 컨텍스트 부족으로 헤맴 | 관련 파일 경로, 기술 스택, 브랜치 등을 프롬프트에 포함 |
| 팀원 작업이 너무 크거나 모호 | 팀원당 구체적 산출물을 명시 (예: "~를 검토하고 발견사항을 리포트") |

## 예시

사용자: "PR #42 코드 리뷰 팀 만들어줘"

```
Create an agent team to review PR #42.

Spawn 3 teammates:
- Security reviewer: Review for auth bypass, injection, secrets exposure.
  Focus on: src/auth/, src/api/. Use Sonnet.
- Performance reviewer: Check for N+1 queries, memory leaks, blocking I/O.
  Focus on: src/services/, src/db/. Use Sonnet.
- Test reviewer: Validate test coverage, identify missing edge cases.
  Focus on: tests/. Use Sonnet.

Wait for all teammates to complete before synthesizing findings.
```
