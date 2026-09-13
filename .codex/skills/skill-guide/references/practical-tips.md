# 실전 스킬 작성 팁

> 출처: "Lessons from Building Claude Code: How We Use Skills" (Thariq, Anthropic, 2026-03-17)
> https://x.com/trq212/status/2033949937936085378

Anthropic 내부에서 수백 개의 스킬을 운영하면서 배운 실전 교훈.

---

## 1. 9가지 스킬 유형

어떤 스킬을 만들어야 할지 모를 때 이 분류를 참고. 좋은 스킬은 하나의 유형에 깔끔하게 속한다.

### 1) Library & API Reference

내부/외부 라이브러리의 올바른 사용법, 엣지 케이스, footguns.

- billing-lib — 내부 결제 라이브러리의 gotchas
- internal-platform-cli — 내부 CLI의 모든 서브커맨드와 사용 예시
- frontend-design — Claude의 디자인 감각 개선 (Inter 폰트, 보라색 그라디언트 회피 등)

### 2) Product Verification

코드가 동작하는지 외부 도구(Playwright, tmux 등)로 검증. 엔지니어가 1주일을 투자해서 만들 가치가 있는 유형.

- signup-flow-driver — headless 브라우저로 가입→이메일 인증→온보딩 전체 플로우 실행
- checkout-verifier — Stripe 테스트 카드로 결제 UI 구동, 인보이스 상태 검증
- tmux-cli-driver — TTY가 필요한 인터랙티브 CLI 테스트

**팁**: Claude가 테스트 과정을 영상 녹화하거나, 각 단계에서 프로그래밍적 assertion을 수행하는 스크립트를 포함하면 검증 품질이 극적으로 올라간다.

### 3) Data Fetching & Analysis

데이터/모니터링 스택 연결. credentials, 대시보드 ID, 일반적인 분석 워크플로우 포함.

- funnel-query — "가입→활성화→유료 전환에 어떤 이벤트를 조인하는가" + canonical user_id 테이블
- cohort-compare — 두 코호트의 리텐션/전환율 비교, 통계적 유의성 플래그
- grafana — datasource UID, 클러스터 이름, 문제→대시보드 매핑 테이블

### 4) Business Process & Team Automation

반복 워크플로우를 하나의 커맨드로 자동화. 이전 실행 결과를 로그에 저장하면 일관성 유지에 도움.

- standup-post — 티켓 트래커 + GitHub 활동 + Slack → 포맷된 스탠드업
- create-ticket — 스키마 강제(유효 enum, 필수 필드) + 생성 후 워크플로우(리뷰어 핑, Slack 링크)
- weekly-recap — 머지된 PR + 닫힌 티켓 + 배포 → 주간 리캡

### 5) Code Scaffolding & Templates

프레임워크 보일러플레이트 생성. 코드만으로 커버 못하는 자연어 요구사항이 있을 때 특히 유용.

- new-workflow — 프레임워크의 새 서비스/워크플로우/핸들러 스캐폴딩
- new-migration — 마이그레이션 파일 템플릿 + 일반적 gotchas
- create-app — 인증, 로깅, 배포 설정이 미리 연결된 새 내부 앱

### 6) Code Quality & Review

코드 품질 강제 및 리뷰. 결정적 스크립트/도구와 결합하면 견고함 극대화. hooks나 GitHub Action으로 자동 실행 가능.

- adversarial-review — 별도 subagent가 코드 비판, 수정, 지적이 nitpick 수준이 될 때까지 반복
- code-style — Claude가 기본적으로 잘 못하는 코드 스타일 강제
- testing-practices — 테스트 작성법과 테스트 대상 지침

### 7) CI/CD & Deployment

코드 fetch, push, 배포 워크플로우.

- babysit-pr — PR 모니터링 → flaky CI 재시도 → 머지 충돌 해결 → auto-merge
- deploy-service — 빌드→스모크 테스트→점진적 트래픽 전환→에러율 비교→자동 롤백
- cherry-pick-prod — 격리된 worktree → cherry-pick → 충돌 해결 → 템플릿 PR

### 8) Runbooks

증상(Slack 스레드, 알림, 에러 시그니처)을 받아 다단계 조사를 거쳐 구조화된 보고서 생성.

- service-debugging — 증상→도구→쿼리 패턴 매핑
- oncall-runner — 알림 fetch → 일반적 원인 점검 → 소견서 포맷
- log-correlator — request ID로 관련 시스템의 로그 수집

### 9) Infrastructure Operations

인프라 유지보수, 정리, 가드레일이 필요한 파괴적 작업.

- orphan-cleaner — 고아 pod/volume 발견 → Slack 알림 → 대기 → 사용자 확인 → 정리
- dependency-management — 조직의 의존성 승인 워크플로우
- cost-investigation — "스토리지/이그레스 비용이 왜 급증했나" + 구체적 버킷과 쿼리 패턴

---

## 2. 고급 패턴

### Setup with config.json

스킬이 사용자별 설정이 필요할 때 (예: Slack 채널, 프로젝트 ID), config.json에 저장하는 패턴:

```markdown
## Setup

Before first use, check `config.json` in this skill directory.
If it doesn't exist, ask the user:
- Which Slack channel for standup posts?
- What's the Linear project key?

Save to `config.json`:
\`\`\`json
{
  "slack_channel": "#team-standup",
  "linear_project": "PROJ-123"
}
\`\`\`
```

구조화된 객관식 질문이 필요하면 AskUserQuestion 도구를 사용하도록 지시.

### Memory & Data Storage

스킬이 이전 실행 기록을 유지하면 품질이 올라간다. 예를 들어 standup-post 스킬이 `standups.log`를 유지하면, 다음 실행 시 "어제와 뭐가 달라졌는지" 파악 가능.

저장 옵션:
- Append-only 텍스트 로그
- JSON 파일
- SQLite 데이터베이스

**주의**: 스킬 디렉토리 내 데이터는 스킬 업그레이드 시 삭제될 수 있다. 안정적인 저장이 필요하면 `${CLAUDE_PLUGIN_DATA}`를 사용하라 (플러그인별 안정 폴더).

### Scripts for Composition

단순 검증 스크립트를 넘어, Claude에게 **조합용 라이브러리**를 제공하면 Claude가 boilerplate 대신 composition에 집중한다.

```python
# scripts/analytics.py — 스킬에 번들된 헬퍼 라이브러리
def fetch_events(event_type, start_date, end_date):
    """Fetch events from the analytics pipeline."""
    ...

def compute_funnel(events, stages):
    """Calculate conversion rates between funnel stages."""
    ...

def statistical_significance(control, experiment):
    """Run chi-squared test on two groups."""
    ...
```

Claude가 이 함수들을 조합해서 "화요일에 무슨 일이 있었나?" 같은 복잡한 분석을 위한 일회용 스크립트를 즉석 생성.

### On Demand Hooks

스킬이 호출될 때만 활성화되고, 세션이 끝나면 사라지는 hooks. 항상 켜두면 방해가 되지만 특정 상황에서 극히 유용한 가드레일에 적합.

예시:
- `/careful` — PreToolUse에서 `rm -rf`, `DROP TABLE`, force-push, `kubectl delete` 차단. 프로덕션 작업 시에만 활성화
- `/freeze` — 특정 디렉토리 외의 Edit/Write를 차단. 디버깅 중 로그만 추가하고 싶을 때

### Composing Skills

스킬이 다른 스킬을 이름으로 참조할 수 있다. 네이티브 의존성 관리는 아직 없지만, SKILL.md에서 다른 스킬을 언급하면 Claude가 설치되어 있을 경우 호출한다.

```markdown
## Workflow
1. Generate the CSV report
2. Upload using the `file-upload` skill
3. Notify via the `slack-poster` skill
```

---

## 3. 배포 전략

### Repo vs Marketplace

| 방식 | 적합한 경우 |
|------|------------|
| `.claude/skills/`에 체크인 | 소규모 팀, 소수 리포 |
| 내부 Plugin Marketplace | 대규모 조직, 스킬 수가 많을 때 |

체크인된 스킬은 모델 컨텍스트에 항상 추가된다. 스킬이 늘어나면 marketplace로 전환해서 사용자가 필요한 것만 설치하도록.

### Marketplace Curation

1. 새 스킬을 sandbox 폴더에 업로드, Slack 등에서 공유
2. 충분한 traction을 얻으면 (스킬 작성자 판단) marketplace PR
3. 나쁘거나 중복 스킬이 쉽게 생기므로 릴리즈 전 큐레이션 필수

### Measuring Usage

PreToolUse hook으로 스킬 호출을 로깅하면 인기도 추적과 under-triggering 감지가 가능하다.

참고: [usage logging gist](https://gist.github.com/ThariqS/24defad423d701746e23dc19aace4de5)
