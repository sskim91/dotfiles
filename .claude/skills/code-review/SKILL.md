---
name: code-review
description: Provides 5-axis review methodology (correctness/readability/architecture/security/performance) with change sizing guidelines (~100 lines target) and severity labels (Critical/Nit/Optional/FYI). Use when conducting a review — yours or from another agent/model. Do NOT use for receiving feedback (use superpowers:receiving-code-review), requesting review (use superpowers:requesting-code-review), security audit only (use springboot-security), or refactoring (use simplify).
---

# Code Review & Quality

다축(multi-axis) 리뷰 + 품질 게이트. 모든 변경은 병합 전에 리뷰된다 — 예외 없음.

## Quick Start

- **리뷰 승인 기준?** → [Approval Standard](#approval-standard) below
- **5축 리뷰 체크?** → [Five-Axis Review](#five-axis-review) below
- **변경 크기 지침?** → [Change Sizing](#change-sizing) below
- **코멘트 심각도 라벨?** → [Severity Labels](#severity-labels) below
- **AI 생성 코드 리뷰 주의점?** → [AI-Generated Code](#ai-generated-code) below
- **최종 체크리스트?** → [Review Checklist](#review-checklist) below
- **리뷰 결과 보고 형식?** → [Review Output Template](#review-output-template) below

## CRITICAL Rules

1. **ALWAYS label severity** — `Critical`/`Nit`/`Optional`/`FYI`. 라벨 없으면 작성자가 모든 피드백을 필수로 오해.
2. **NEVER rubber-stamp** — 증거 없는 `LGTM` 금지. 리뷰는 품질 게이트지 의례가 아니다.
3. **ALWAYS separate refactor from feature** — 한 PR에서 섞지 말 것. 리뷰어가 혼란해지고 롤백이 어려워진다.
4. **NEVER accept "I'll clean it up later"** — 나중은 오지 않는다. 병합 전에 정리.
5. **ALWAYS ~100 lines target** — 300까지 허용, 1000+는 거의 항상 분할.
6. **ALWAYS review AI-generated code harder, not softer** — AI 코드는 자신 있게 틀리므로 더 많은 검증 필요.
7. **ALWAYS respond within 1 business day** — 느린 리뷰는 팀 전체를 블로킹.
8. **NEVER block on "이렇게 안 써서"** — 관습과 일치하고 코드 건강을 개선하면 승인.

## Approval Standard

> 변경이 **전체 코드 건강을 명확히 개선**하면 승인하라 — 완벽하지 않아도.

완벽한 코드는 없다. 목표는 지속적 개선이지 당신의 스타일 강제가 아니다. 프로젝트 규칙을 따르고 코드베이스를 개선하면, 당신이라면 다르게 썼을지라도 승인.

## Five-Axis Review

각 변경은 이 5개 축을 평가한다.

### 1. Correctness — 의도대로 동작하는가

- 명세·태스크 요구사항과 일치?
- edge case 처리 (null, empty, boundary)?
- error path 처리 (happy path만 아니라)?
- 테스트가 **옳은 것**을 테스트하는가? (구현 상세 테스트 = bad)
- off-by-one, race, state 비일관성?

### 2. Readability & Simplicity — 설명 없이 읽히는가

- 이름이 설명적이고 프로젝트 관습과 일치? (`temp`, `data`, `result` 단독 금지)
- 제어 흐름이 단순? (중첩 삼항, 깊은 콜백 금지)
- **100줄이면 될 것을 1000줄로 썼는가?**
- **추상화가 복잡도 값을 하는가?** (세 번째 사용처 전까지 일반화 금지)
- 죽은 코드 잔존물? (`_unused`, `// removed`, 호환성 shim)

### 3. Architecture — 시스템 설계에 맞는가

- 기존 패턴 따름? 새 패턴 도입이면 정당화됨?
- 모듈 경계 명확? 순환 의존 없음?
- 중복 코드는 공유되어야 하는가?
- 추상화 레벨 적절? (과잉 엔지니어링·과잉 결합 금지)

### 4. Security — 취약점 도입 없음

> 상세한 보안 가이드는 `springboot-security` / `api-design` Security Boundaries 참조.

- 외부 입력 검증 + sanitize
- 시크릿이 코드·로그·VCS에 없음
- 인증/인가 체크 위치 적절
- SQL 파라미터화 (문자열 연결 금지)
- XSS 방지를 위한 출력 인코딩
- **외부 서비스 응답도 untrusted로 취급**
- 의존성 vulnerability 체크

### 5. Performance — 병목 없음

> 상세한 프로파일링은 플러그인 `web-perf` + `sql-optimization-patterns` 참조.

- N+1 쿼리 패턴
- 무한/무경계 루프, unbounded fetch
- sync여서 async여야 할 것
- UI 컴포넌트 불필요한 re-render
- list 엔드포인트 pagination 누락
- hot path에서 큰 객체 생성

## Change Sizing

작고 집중된 변경이 리뷰·병합·배포 모두에서 안전하다.

| 변경 라인 수 | 평가 | 조치 |
|---|---|---|
| ~100 | Good | 한 자리에서 리뷰 가능 |
| ~300 | Acceptable | 단일 논리적 변경일 때만 |
| ~1000+ | Too large | **분할 필요** |

**"한 변경"의 정의:** 한 가지를 다루고, 관련 테스트 포함, 병합 후에도 시스템이 동작하는 자기 완결적 수정. **기능의 한 조각**이지 기능 전체가 아님.

### 분할 전략

| 전략 | 방법 | 적합한 경우 |
|---|---|---|
| **Stack** | 작은 변경 제출, 그 위에 다음 변경 | 순차 의존 |
| **By file group** | 리뷰어가 다른 파일 그룹별 분리 | cross-cutting 관심사 |
| **Horizontal** | 공유 코드/stub 먼저, 소비자 나중 | layered 아키텍처 |
| **Vertical** | 작은 full-stack slice로 쪼개기 | 기능 작업 |

**큰 변경이 허용되는 경우:** 파일 전체 삭제, 자동 리팩토링 — 리뷰어가 각 라인이 아니라 의도만 확인하면 되는 경우.

**리팩토링과 기능 작업 분리:** 기존 코드 리팩토링 + 새 동작 추가 = 두 변경. 별도 제출. 작은 이름 변경 정도는 리뷰어 재량.

## Severity Labels

모든 코멘트에 심각도를 붙여라. 작성자가 필수와 선택을 구분하도록.

| Prefix | 의미 | 작성자 액션 |
|---|---|---|
| *(no prefix)* | Required change | 병합 전 반드시 해결 |
| **Critical:** | Blocks merge | 보안·데이터 손실·기능 파손 |
| **Nit:** | Minor, optional | 무시해도 됨 — 포맷·스타일 선호 |
| **Optional:** / **Consider:** | Suggestion | 고려할 가치, 필수 아님 |
| **FYI** | Informational | 액션 없음 — 맥락 제공 |

## Review Process

### Step 1 — Context 이해

코드 보기 전 의도 파악:
- 이 변경이 뭘 달성하려는가?
- 어떤 명세/태스크를 구현하는가?
- 예상되는 동작 변화는?

### Step 2 — 테스트부터 리뷰

테스트가 의도와 커버리지를 드러낸다.
- 테스트 존재?
- 동작을 테스트하는가 구현을 테스트하는가?
- edge case 커버?
- 이름이 설명적?
- 코드가 깨지면 regression을 잡을 수 있는가?

### Step 3 — 구현 워크스루

각 파일에 5축을 대입:
1. Correctness — 테스트가 말하는 대로 동작?
2. Readability — 설명 없이 이해?
3. Architecture — 시스템에 적합?
4. Security — 취약점?
5. Performance — 병목?

### Step 4 — 발견 사항 라벨링

Severity Labels 적용. 라벨 없는 코멘트 금지.

### Step 5 — 검증 스토리 확인

작성자가 어떻게 검증했는가?
- 어떤 테스트 실행?
- 빌드 통과?
- 수동 테스트?
- UI는 스크린샷?
- before/after 비교?

## AI-Generated Code

**AI 코드는 더 엄격히 리뷰한다, 덜이 아니다.**

- AI는 **자신 있게 틀린다** — 존재하지 않는 API, 환각 import, 틀린 타입
- "plausible"과 "correct"는 다르다
- 테스트가 통과해도 보안/아키/가독성 문제는 남는다
- 프로젝트 관습을 모르고 일반적 패턴을 쓸 수 있다

**특히 체크:**
- import가 실제 존재? (환각 모듈)
- 함수 시그니처가 실제 라이브러리와 일치?
- 에러 처리가 **진짜** 에러 케이스를 잡는가, 아니면 의례적 try-catch인가?
- 복사된 것처럼 보이는 generic 코드 — 여기 context에 맞는가?

## Multi-Model Review

다른 모델이 다른 blind spot을 가지므로 교차 리뷰가 효과적.

```
Model A가 코드 작성
    ↓
Model B가 correctness + architecture 리뷰
    ↓
Model A가 피드백 반영
    ↓
사람이 최종 판단
```

에이전트 리뷰 프롬프트 예:
```
이 코드 변경을 정확성·보안·프로젝트 관습 준수 관점에서 리뷰하라.
명세는 [X]이다. 변경은 [Y]해야 한다.
발견 사항을 Critical / Important / Suggestion으로 분류하라.
```

## Dead Code Hygiene

리팩토링·구현 변경 후 고아 코드 체크:

1. 이제 unreachable/unused인 코드 식별
2. 목록으로 명시
3. **삭제 전 확인:** "이 사용되지 않는 요소들을 제거해도 될까요: [list]?"

조용히 삭제하지 말 것 — 확신 없으면 물어라.

```
DEAD CODE IDENTIFIED:
- formatLegacyDate() in src/utils/date.ts — formatDate()로 대체됨
- OldTaskCard in src/components/ — TaskCard로 대체됨
- LEGACY_API_URL in src/config.ts — 참조 없음
→ 제거해도 될까요?
```

## Handling Disagreements

리뷰 논쟁 해결 계층:

1. **기술적 사실·데이터**가 의견·선호를 오버라이드
2. **스타일 가이드**는 스타일 문제의 절대 권위
3. **소프트웨어 설계**는 엔지니어링 원칙으로 평가 — 개인 선호 아님
4. **코드베이스 일관성**은 전체 건강을 훼손하지 않는 한 허용

**"I'll fix it later" 불가.** 경험상 지연된 정리는 거의 일어나지 않는다. 진짜 긴급이 아닌 한 제출 전 정리 요구. 이 변경에서 처리 못 하면 self-assigned 버그 티켓 필수.

## Honesty in Review

리뷰어의 정직함:

- **rubber-stamp 금지** — 증거 없는 `LGTM`은 아무도 돕지 않는다
- **진짜 문제를 부드럽게 포장 금지** — "minor concern"인 척 하는 프로덕션 버그 = dishonest
- **가능하면 정량화** — "느릴 수 있다"보다 "N+1이라 목록당 ~50ms 추가"가 낫다
- **문제 있는 접근은 밀어내라** — sycophancy는 리뷰의 실패 모드
- **override는 품위 있게 수용** — 작성자가 full context 가지고 동의 안 하면 존중. **코드를 비판하되 사람을 비판하지 말 것**

## Dependency Discipline

의존성 추가 전 체크:

1. 기존 스택으로 해결 가능? (대부분 가능)
2. 의존성 크기? (bundle 영향)
3. 활발히 유지되는가? (마지막 커밋, open issue)
4. 알려진 vulnerability? (`npm audit`, `./gradlew dependencyCheckAnalyze`)
5. 라이선스 호환성?

**원칙:** 새 의존성보다 표준 라이브러리·기존 유틸 우선. **모든 의존성은 부채다.**

## Review Checklist

```markdown
## Review: [PR 제목]

### Context
- [ ] 이 변경의 목적과 이유를 이해

### Correctness
- [ ] 명세/태스크 요구사항과 일치
- [ ] edge case 처리
- [ ] error path 처리
- [ ] 테스트가 변경을 적절히 커버

### Readability
- [ ] 이름이 명확하고 일관
- [ ] 로직이 단순
- [ ] 불필요한 복잡도 없음

### Architecture
- [ ] 기존 패턴 준수
- [ ] 불필요한 결합/의존 없음
- [ ] 추상화 레벨 적절

### Security
- [ ] 코드에 시크릿 없음
- [ ] 경계에서 입력 검증
- [ ] injection 취약점 없음
- [ ] 인증/인가 체크 존재
- [ ] 외부 데이터 소스를 untrusted로 취급

### Performance
- [ ] N+1 패턴 없음
- [ ] unbounded 작업 없음
- [ ] list 엔드포인트 pagination

### Verification
- [ ] 테스트 통과
- [ ] 빌드 성공
- [ ] 수동 검증 (해당 시)

### Verdict
- [ ] **Approve** — 병합 준비 완료
- [ ] **Request changes** — 해결해야 할 이슈 존재
```

## Review Output Template

리뷰 결과를 보고할 때 사용하는 구조화된 형식. [Review Checklist](#review-checklist)는 **과정** 체크용, 이 템플릿은 **결과 보고**용.

```markdown
## Review Summary

**Verdict:** APPROVE | REQUEST CHANGES

**Overview:** [1-2 sentences summarizing the change and overall assessment]

### Critical Issues
- [File:line] [Description and recommended fix]

### Important Issues
- [File:line] [Description and recommended fix]

### Suggestions
- [File:line] [Description]

### What's Done Well
- [Positive observation — always include at least one]

### Verification Story
- Tests reviewed: [yes/no, observations]
- Build verified: [yes/no]
- Security checked: [yes/no, observations]
```

**규칙:**
- Critical/Important 발견에는 반드시 **구체적 수정 제안** 포함
- "What's Done Well" 최소 1개 — 칭찬이 좋은 관행을 강화
- Verdict가 REQUEST CHANGES면 Critical Issues가 1개 이상
- Verification Story는 작성자의 검증 노력을 기록 — 빈 항목은 리스크 신호

## Common Rationalizations

| 변명 | 반박 |
|---|---|
| "동작하니까 충분해요" | 읽히지 않거나 안전하지 않거나 설계가 틀린 **동작 코드**는 복리로 쌓이는 부채다. |
| "제가 썼으니 맞는지 알아요" | 작성자는 자기 가정에 눈먼다. 모든 변경은 다른 눈을 얻는다. |
| "나중에 정리할게요" | 나중은 오지 않는다. **병합 전**이 게이트. |
| "AI 생성 코드니 아마 괜찮아요" | AI 코드는 **더** 엄격히 봐야 한다. 자신 있게 틀린다. |
| "테스트 통과하니 좋아요" | 테스트는 필요하지만 충분하지 않다. 아키·보안·가독성은 못 잡는다. |
| "작은 리팩토링 하나 껴 넣었어요" | 두 변경으로 분리. 리뷰어가 feature와 cleanup을 구분 못 한다. |
| "리뷰가 너무 오래 걸려요" | 그 리뷰가 없으면 프로덕션에서 훨씬 더 오래 걸린다. |

## Red Flags

- 리뷰 없이 병합된 PR
- 테스트 통과만 확인하는 리뷰 (다른 축 무시)
- 증거 없는 `LGTM`
- 보안 민감 변경에 보안 초점 리뷰 없음
- "너무 커서 제대로 리뷰 못 하겠어요" PR → 분할
- 버그 fix PR에 regression test 없음
- severity 라벨 없는 코멘트 — 필수인지 선택인지 불명
- "I'll fix it later" 수용 → 일어나지 않는다

## Cross-References

| Topic | Skill / Agent |
|---|---|
| 심층 코드 리뷰 실행 (diff 기반) | `superpowers:code-reviewer` 에이전트 |
| 코드 단순화·중복 제거 | `simplify` 스킬, `code-simplifier` 에이전트 |
| Java/Spring 코드 품질 분석 | `java-enterprise-analyzer` 에이전트 |
| Python 코드 품질 분석 | `python-analysis-expert` 에이전트 |
| SQL 성능 최적화 | `sql-performance-optimizer` 에이전트 |
| 리뷰 피드백 수용 프로세스 | `superpowers:receiving-code-review` |
| 리뷰 요청 프로세스 | `superpowers:requesting-code-review` |
| 보안 관점 리뷰 (Spring) | `springboot-security` |
| 범용 보안 감사 (언어 무관) | `security-auditor` 에이전트 |
| API 설계 리뷰 | `api-design` |

## References

- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [Software Engineering at Google — Chapter 9: Code Review](https://abseil.io/resources/swe-book/html/ch09.html)
- [Yelp Code Review Guidelines](https://engineeringblog.yelp.com/2017/11/code-review-guidelines.html)
