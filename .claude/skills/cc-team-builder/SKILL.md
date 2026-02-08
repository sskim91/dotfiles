---
name: cc-team-builder
description: Interactive wizard to design and spawn Claude Code Agent Teams. Use when user wants to create agent team, design team composition, plan multi-agent collaboration, or mentions "agent team", "team spawn", "create team".
---

# Create Agent Team

Agent Team 구성을 대화형으로 설계하고 생성하는 스킬. 사용 목적, 팀 구조, 역할 분배를 단계별 질문으로 파악한 뒤 최적의 팀 프롬프트를 생성합니다.

## Usage

```
/create-agent-team                    # 대화형 위저드 시작
/create-agent-team <description>      # 작업 설명으로 바로 시작
```

## Prerequisites

Agent Teams가 활성화되어 있어야 합니다. 비활성 상태라면 안내:

```json
// ~/.claude/settings.json 또는 프로젝트 .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Instructions

### Step 1: 작업 목적 파악

인자가 제공된 경우 해당 설명을 사용. 아닌 경우 AskUserQuestion:

```
header: "Task type"
question: "어떤 작업을 위한 팀을 구성할까요?"
options:
  - label: "Code Review"
    description: "PR이나 코드베이스를 여러 관점(보안, 성능, 테스트 등)에서 병렬 검토"
  - label: "Feature Development"
    description: "새 기능을 프론트엔드/백엔드/테스트 등으로 분리하여 병렬 개발"
  - label: "Investigation"
    description: "버그 원인이나 기술 문제를 여러 가설로 병렬 조사"
  - label: "Research & Analysis"
    description: "기술 조사, 라이브러리 비교, 아키텍처 검토 등 병렬 탐색"
```

### Step 2: 팀 규모 결정

```
header: "Team size"
question: "팀원을 몇 명으로 구성할까요?"
options:
  - label: "2명"
    description: "소규모 작업. 두 관점 비교나 프론트/백 분리"
  - label: "3명 (Recommended)"
    description: "균형 잡힌 구성. 대부분의 작업에 적합"
  - label: "4-5명"
    description: "대규모 조사나 다면적 검토. 토큰 비용 높음"
```

### Step 3: 역할 설계

Step 1에서 선택한 작업 유형에 따라 역할 템플릿을 제안합니다.

#### Code Review 템플릿

```
header: "Reviewers"
question: "어떤 관점의 리뷰어를 배치할까요? (복수 선택)"
multiSelect: true
options:
  - label: "Security"
    description: "보안 취약점, 인증/인가, 입력 검증 검토"
  - label: "Performance"
    description: "성능 영향, N+1 쿼리, 메모리 사용 검토"
  - label: "Test Coverage"
    description: "테스트 누락, 엣지 케이스, 커버리지 검증"
  - label: "Architecture"
    description: "설계 패턴, SOLID 원칙, 유지보수성 검토"
```

#### Feature Development 템플릿

```
header: "Roles"
question: "어떤 역할의 팀원을 배치할까요? (복수 선택)"
multiSelect: true
options:
  - label: "Frontend"
    description: "UI 컴포넌트, 상태 관리, 사용자 경험 구현"
  - label: "Backend"
    description: "API, 비즈니스 로직, 데이터베이스 구현"
  - label: "Tester"
    description: "단위/통합 테스트 작성, 엣지 케이스 검증"
  - label: "DevOps"
    description: "배포, CI/CD, 인프라 설정"
```

#### Investigation 템플릿

```
header: "Approach"
question: "조사 방식을 어떻게 구성할까요?"
options:
  - label: "Hypothesis-based"
    description: "각 팀원이 다른 가설을 조사하고 서로 반박/검증"
  - label: "Layer-based"
    description: "프론트엔드/백엔드/DB 등 계층별로 나눠 조사"
  - label: "Timeline-based"
    description: "최근 변경/배포/설정 등 시간축별로 나눠 조사"
```

#### Research & Analysis 템플릿

```
header: "Research"
question: "연구 방식을 어떻게 구성할까요?"
options:
  - label: "Competitive"
    description: "각 팀원이 다른 대안을 옹호하며 장단점 토론"
  - label: "Aspect-based"
    description: "성능/비용/DX/확장성 등 관점별로 나눠 분석"
  - label: "Depth-based"
    description: "한 팀원은 넓게, 나머지는 유망한 옵션을 깊게 조사"
```

### Step 4: 모델 선택

```
header: "Model"
question: "팀원에게 어떤 모델을 사용할까요?"
options:
  - label: "Sonnet (Recommended)"
    description: "빠르고 비용 효율적. 대부분의 작업에 적합"
  - label: "Opus"
    description: "최고 품질. 복잡한 아키텍처나 심층 분석에 적합"
  - label: "Haiku"
    description: "가장 빠르고 저렴. 단순 검색/분류 작업에 적합"
```

### Step 5: 추가 옵션

```
header: "Options"
question: "추가 옵션을 선택하세요 (복수 선택 가능)"
multiSelect: true
options:
  - label: "Plan approval"
    description: "팀원이 구현 전 계획을 리더에게 승인 요청"
  - label: "Delegation mode"
    description: "리더는 조율만 하고 직접 코드를 작성하지 않음"
  - label: "Split pane (tmux)"
    description: "각 팀원을 별도 tmux 창에 표시"
```

### Step 6: 프롬프트 생성 및 확인

수집한 정보를 바탕으로 팀 생성 프롬프트를 조합합니다.

**프롬프트 구조:**

```
Create an agent team to [작업 목적].

Spawn [N] teammates:
- [역할1]: [상세 지시사항]. Use [model].
- [역할2]: [상세 지시사항]. Use [model].
- [역할3]: [상세 지시사항]. Use [model].

[추가 지시사항 - plan approval, delegation 등]

Coordination rules:
- Each teammate should [협업 방식]
- When all teammates finish, synthesize findings and present a summary.
- Wait for all teammates to complete before concluding.
```

생성된 프롬프트를 사용자에게 보여주고 AskUserQuestion으로 확인:

```
header: "Confirm"
question: "이 팀 구성으로 진행할까요?"
options:
  - label: "Yes, proceed"
    description: "이대로 팀을 생성합니다"
  - label: "Edit prompt"
    description: "프롬프트를 수정한 뒤 진행합니다"
```

### Step 7: 팀 실행

사용자가 확인하면:

1. **TeamCreate**로 팀 생성
2. **TaskCreate**로 각 팀원의 작업 생성
3. **Task tool**로 팀원 에이전트 생성 (team_name 지정)
4. **TaskUpdate**로 작업 할당

## Role Templates Reference

### Code Review Roles

| Role | Focus | Key Checks |
|------|-------|------------|
| Security Reviewer | 보안 취약점 | XSS, SQL injection, auth bypass, secrets exposure |
| Performance Reviewer | 성능 영향 | N+1 queries, memory leaks, blocking I/O |
| Test Reviewer | 테스트 품질 | Coverage gaps, edge cases, flaky tests |
| Architecture Reviewer | 설계 품질 | SOLID, coupling, abstraction, patterns |

### Feature Development Roles

| Role | Scope | Deliverable |
|------|-------|-------------|
| Frontend Dev | UI/UX 구현 | Components, state, styles |
| Backend Dev | API/로직 구현 | Endpoints, services, models |
| Test Engineer | 테스트 작성 | Unit, integration, E2E tests |
| DevOps Engineer | 인프라/배포 | CI/CD, Docker, configs |

### Investigation Roles

| Role | Strategy | Output |
|------|----------|--------|
| Hypothesis Investigator | 특정 가설 검증 | Evidence for/against |
| Layer Inspector | 특정 계층 집중 조사 | Layer-specific findings |
| Timeline Analyst | 시간순 변경 추적 | Change correlation |

## Best Practices

이 스킬이 생성하는 프롬프트에 항상 포함할 원칙:

1. **파일 충돌 방지**: 각 팀원이 서로 다른 파일을 담당하도록 분리
2. **명확한 결과물**: 각 팀원의 기대 산출물을 명시
3. **완료 대기**: 리더가 팀원 완료 전에 먼저 결론짓지 않도록 지시
4. **팀원당 5-6개 작업**: 적절한 작업 단위로 분할
5. **충분한 컨텍스트**: 팀원에게 관련 파일 경로, 기술 스택 등 명시

## Examples

### PR 코드 리뷰 팀

```
/create-agent-team PR #42 코드 리뷰
```

결과 프롬프트 예시:
```
Create an agent team to review PR #42.

Spawn 3 teammates:
- Security reviewer: Review for security vulnerabilities including auth bypass,
  injection attacks, and secrets exposure. Use Sonnet.
- Performance reviewer: Check for N+1 queries, memory leaks, and blocking I/O.
  Use Sonnet.
- Test reviewer: Validate test coverage, identify missing edge cases.
  Use Sonnet.

Have them each review independently and share findings.
When all reviews are complete, synthesize into a unified review summary.
Wait for all teammates to complete before concluding.
```

### 버그 조사 팀

```
/create-agent-team 로그인 후 세션이 1분 만에 만료되는 버그 조사
```

결과 프롬프트 예시:
```
Create an agent team to investigate why user sessions expire after 1 minute.

Spawn 4 teammates to investigate different hypotheses:
- Auth config investigator: Check session/token configuration, TTL settings,
  cookie attributes. Use Sonnet.
- Backend logic investigator: Trace session creation and validation flow in
  auth middleware. Use Sonnet.
- Frontend investigator: Check token refresh logic, storage mechanism, and
  API interceptors. Use Sonnet.
- Infrastructure investigator: Check load balancer sticky sessions, Redis
  session store TTL, deployment config. Use Sonnet.

Have them talk to each other to disprove each other's theories.
Update findings as consensus emerges.
Wait for all teammates to complete before concluding.
```
