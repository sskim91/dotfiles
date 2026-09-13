# Anthropic 공식 스킬 빌딩 가이드 요약

> 원본: "The Complete Guide to Building Skills for Claude" (Anthropic, 2026)
> https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

스킬 생성/개선 시 이 문서를 참조하여 Anthropic의 공식 권장사항을 따른다.

---

## 1. 스킬이란?

스킬은 폴더로 패키징된 지시사항(instructions)으로, Claude에게 특정 작업이나 워크플로우를 처리하는 방법을 가르친다. 매 대화마다 선호사항, 프로세스, 도메인 전문성을 반복 설명하는 대신, 한 번 가르치면 매번 활용된다.

**스킬이 강력한 경우:**
- 반복 가능한 워크플로우 (프론트엔드 디자인, 리서치, 문서 생성)
- Claude의 내장 기능(코드 실행, 문서 생성)과 함께 사용
- MCP 통합 위에 워크플로우 계층 추가

**플랫폼 호환성:**
- Claude.ai, Claude Code, API 모두에서 동일하게 작동
- 환경 의존성만 지원하면 수정 없이 이식 가능

---

## 2. 핵심 설계 원칙

### 2.1 Progressive Disclosure (3단계 시스템)

| 단계 | 로드 시점 | 내용 | 역할 |
|------|-----------|------|------|
| **1단계: YAML frontmatter** | 항상 (시스템 프롬프트) | name, description | 스킬 사용 여부 판단용 |
| **2단계: SKILL.md 본문** | 스킬이 관련 있다고 판단 시 | 전체 지시사항과 가이드 | 핵심 작업 수행 |
| **3단계: 참조 파일** | 필요할 때만 | references/, scripts/, assets/ | 상세 문서, 스크립트 |

- 1단계가 가장 중요: 여기서 Claude가 스킬을 로드할지 결정
- 토큰 사용을 최소화하면서 전문 지식 유지
- **SKILL.md는 5,000 단어 이내** 유지, 상세 내용은 references/로 이동

### 2.2 Composability (조합성)

- Claude는 여러 스킬을 동시에 로드할 수 있음
- 스킬은 다른 스킬과 함께 잘 작동해야 함
- 자신이 유일한 기능이라고 가정하지 말 것

---

## 3. 파일 구조

```
your-skill-name/
├── SKILL.md          # 필수 - 메인 스킬 파일
├── scripts/          # 선택 - 실행 가능한 코드
│   ├── process_data.py
│   └── validate.sh
├── references/       # 선택 - 필요 시 로드되는 문서
│   ├── api-guide.md
│   └── examples/
└── assets/           # 선택 - 템플릿, 폰트, 아이콘
    └── report-template.md
```

### 필수 규칙

| 규칙 | 설명 |
|------|------|
| 파일명 | 반드시 `SKILL.md` (대소문자 구분, SKILL.MD나 skill.md 불가) |
| 폴더명 | kebab-case만 (`notion-project-setup`), 공백/밑줄/대문자 금지 |
| name 필드 | 폴더명과 일치, kebab-case, 64자 이내 |
| description | 1024자 이내, XML 태그(`<>`) 금지 |
| README.md | 스킬 폴더 내에 포함하지 말 것 (문서는 SKILL.md 또는 references/) |
| 예약어 | name에 "claude" 또는 "anthropic" 접두사 금지 |

---

## 4. YAML Frontmatter 완전 참조

### 필수 필드

```yaml
---
name: skill-name-in-kebab-case
description: What it does and when to use it. Include specific trigger phrases.
---
```

### 선택 필드

```yaml
---
name: skill-name
description: [필수 설명]
license: MIT                    # 오픈소스 시
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"  # 도구 접근 제한
compatibility: "Claude Code only"  # 환경 요구사항 (1-500자)
metadata:                       # 커스텀 키-값
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
---
```

### 보안 제한

- **허용**: 표준 YAML 타입(문자열, 숫자, 불리언, 리스트, 객체), 커스텀 메타데이터, 긴 설명(1024자)
- **금지**: XML 꺾쇠괄호(`< >`), YAML 내 코드 실행, "claude"/"anthropic" 접두사

---

## 5. Description 작성법 (가장 중요)

### 공식 구조

```
[What it does] + [When to use it] + [Key capabilities/trigger phrases]
```

Anthropic 엔지니어링 블로그: "이 메타데이터는... Claude가 전체 내용을 컨텍스트에 로드하지 않고도 각 스킬을 언제 사용해야 하는지 알 수 있는 충분한 정보만 제공합니다."

### 좋은 예시

```yaml
# 구체적이고 실행 가능
description: Analyzes Figma design files and generates developer handoff
documentation. Use when user uploads .fig files, asks for "design specs",
"component documentation", or "design-to-code handoff".

# 트리거 문구 포함
description: Manages Linear project workflows including sprint planning, task
creation, and status tracking. Use when user mentions "sprint", "Linear tasks",
"project planning", or asks to "create tickets".

# 명확한 가치 제안
description: End-to-end customer onboarding workflow for PayFlow. Handles
account creation, payment setup, and subscription management. Use when user
says "onboard new customer", "set up subscription", or "create PayFlow account".
```

### 나쁜 예시

```yaml
# 너무 모호
description: Helps with projects.

# 트리거 누락
description: Creates sophisticated multi-page documentation systems.

# 너무 기술적, 사용자 트리거 없음
description: Implements the Project entity model with hierarchical relationships.
```

### Negative Trigger (과잉 트리거 방지)

```yaml
description: Advanced data analysis for CSV files. Use for statistical modeling,
regression, clustering. Do NOT use for simple data exploration
(use data-viz skill instead).
```

---

## 6. 스킬 카테고리 (3가지)

### Category 1: Document & Asset Creation

- **용도**: 일관되고 고품질의 출력물 생성 (문서, 프레젠테이션, 앱, 디자인, 코드)
- **실례**: frontend-design, docx, pptx, xlsx, pdf 스킬
- **핵심 기법**:
  - 임베디드 스타일 가이드 및 브랜드 표준
  - 일관된 출력을 위한 템플릿 구조
  - 최종화 전 품질 체크리스트
  - 외부 도구 불필요 (Claude 내장 기능 활용)

### Category 2: Workflow Automation

- **용도**: 일관된 방법론이 필요한 다단계 프로세스
- **실례**: skill-creator 스킬
- **핵심 기법**:
  - 검증 게이트가 있는 단계별 워크플로우
  - 공통 구조를 위한 템플릿
  - 내장 검토 및 개선 제안
  - 반복 개선 루프

### Category 3: MCP Enhancement

- **용도**: MCP 서버의 도구 접근 위에 워크플로우 가이드 추가
- **실례**: sentry-code-review 스킬
- **핵심 기법**:
  - 순차적 MCP 호출 조율
  - 도메인 전문 지식 내장
  - 사용자가 직접 지정할 필요 없는 컨텍스트 제공
  - 일반적 MCP 오류 처리

### MCP와 스킬의 관계 (주방 비유)

| | MCP (Connectivity) | Skills (Knowledge) |
|---|---|---|
| 역할 | 전문 주방 (도구, 재료, 장비) | 레시피 (단계별 지시사항) |
| 제공 | 실시간 데이터 접근 및 도구 호출 | 워크플로우와 모범 사례 |
| 질문 | Claude가 **무엇을** 할 수 있는가 | Claude가 **어떻게** 해야 하는가 |

---

## 7. 성공 기준 정의

### 정량적 메트릭

| 메트릭 | 목표 | 측정 방법 |
|--------|------|-----------|
| 트리거 정확도 | 관련 쿼리의 90%+ 자동 트리거 | 10-20개 테스트 쿼리 실행, 자동 로드 비율 추적 |
| 워크플로우 효율 | X번의 tool call 내 완료 | 스킬 유무 비교, tool call 수와 토큰 소비 측정 |
| API 실패율 | 워크플로우당 0건 | MCP 서버 로그에서 재시도율과 에러 코드 추적 |

### 정성적 메트릭

| 메트릭 | 평가 방법 |
|--------|-----------|
| 사용자가 다음 단계를 묻지 않아도 됨 | 테스트 중 리디렉트/명확화 필요 횟수 기록 |
| 사용자 수정 없이 워크플로우 완료 | 동일 요청 3-5회 실행, 구조적 일관성과 품질 비교 |
| 세션 간 일관된 결과 | 신규 사용자가 최소 가이드로 첫 시도에 성공 가능한지 확인 |

---

## 8. 지시사항 작성 모범 사례

### 권장 SKILL.md 구조

```markdown
---
name: your-skill
description: [...]
---
# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

```bash
python scripts/fetch_data.py --project-id PROJECT_ID
Expected output: [describe what success looks like]
```

(Add more steps as needed)

## Examples
Example 1: [common scenario]
User says: "Set up a new marketing campaign"
Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters
Result: Campaign created with confirmation link

## Troubleshooting
Error: [Common error message]
Cause: [Why it happens]
Solution: [How to fix]
```

### DO (해야 할 것)

1. **구체적이고 실행 가능하게**:
   ```
   ✅ Run `python scripts/validate.py --input {filename}` to check data format.
   If validation fails, common issues include:
   - Missing required fields (add them to the CSV)
   - Invalid date formats (use YYYY-MM-DD)

   ❌ Validate the data before proceeding.
   ```

2. **번들 리소스를 명확히 참조**:
   ```
   Before writing queries, consult `references/api-patterns.md` for:
   - Rate limiting guidance
   - Pagination patterns
   - Error codes and handling
   ```

3. **에러 핸들링 포함**:
   ```
   ## Common Issues
   ### MCP Connection Failed
   If you see "Connection refused":
   1. Verify MCP server is running: Check Settings > Extensions
   2. Confirm API key is valid
   3. Try reconnecting
   ```

4. **Progressive Disclosure 활용**: SKILL.md에는 핵심 지시사항만, 상세 문서는 `references/`에 링크

5. **중요한 검증은 스크립트로**: "코드는 결정적(deterministic), 언어 해석은 아님"
   - 중요한 검증은 `scripts/`에 Python/Bash 스크립트로 번들
   - Office 스킬(docx, pptx 등)이 이 패턴의 좋은 예

6. **모델 "게으름" 대응**: 명시적 격려 추가
   ```
   ## Performance Notes
   - Take your time to do this thoroughly
   - Quality is more important than speed
   - Do not skip validation steps
   ```
   참고: 이것은 SKILL.md보다 사용자 프롬프트에 추가하는 것이 더 효과적

### DON'T (하지 말 것)

- 지시사항이 너무 장황 → 간결하게, 불릿 포인트와 번호 리스트 사용
- 중요 지시사항이 파묻힘 → 상단에 배치, `## Important` / `## Critical` 헤더 사용
- 모호한 언어:
  ```
  ❌ Make sure to validate things properly
  ✅ CRITICAL: Before calling create_project, verify:
  - Project name is non-empty
  - At least one team member assigned
  - Start date is not in the past
  ```

---

## 9. 워크플로우 패턴 (5가지)

### Pattern 1: Sequential Workflow Orchestration

**적합한 경우**: 특정 순서의 다단계 프로세스

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

**핵심 기법**: 명시적 단계 순서, 단계 간 의존성, 각 단계 검증, 실패 시 롤백 지시

### Pattern 2: Multi-MCP Coordination

**적합한 경우**: 여러 서비스에 걸친 워크플로우

```
Phase 1: Design Export (Figma MCP) → asset manifest 생성
Phase 2: Asset Storage (Drive MCP) → 폴더 생성, 업로드
Phase 3: Task Creation (Linear MCP) → 개발 작업 생성
Phase 4: Notification (Slack MCP) → 핸드오프 요약 포스트
```

**핵심 기법**: 명확한 페이즈 분리, MCP 간 데이터 전달, 다음 페이즈 전 검증, 중앙화된 에러 핸들링

### Pattern 3: Iterative Refinement

**적합한 경우**: 반복으로 출력 품질이 향상되는 경우

```
Initial Draft → Quality Check (scripts/check_report.py) → Refinement Loop → Finalization
```

**핵심 기법**: 명시적 품질 기준, 반복 개선, 검증 스크립트, 반복 중단 시점 명확화

### Pattern 4: Context-Aware Tool Selection

**적합한 경우**: 같은 결과, 컨텍스트에 따라 다른 도구

```
파일 크기 확인 → 대형(>10MB): Cloud Storage MCP
                → 협업 문서: Notion/Docs MCP
                → 코드 파일: GitHub MCP
                → 임시 파일: 로컬 저장소
```

**핵심 기법**: 명확한 의사결정 기준, 폴백 옵션, 선택 이유 투명성

### Pattern 5: Domain-Specific Intelligence

**적합한 경우**: 도구 접근 이상의 전문 지식 추가

```
Transaction → Compliance Check (제재 리스트, 관할권, 위험도)
           → IF passed: 결제 처리
           → ELSE: 리뷰 플래그 + 컴플라이언스 케이스 생성
           → Audit Trail: 모든 결정 로그
```

**핵심 기법**: 로직에 도메인 전문성 내장, 행동 전 컴플라이언스 확인, 포괄적 문서화, 명확한 거버넌스

---

## 10. 테스트 전략

### 테스트 접근 수준

| 수준 | 방법 | 적합한 경우 |
|------|------|-------------|
| Manual | Claude.ai에서 직접 쿼리 실행 | 빠른 반복, 소규모 팀 |
| Scripted | Claude Code에서 자동화된 테스트 케이스 | 반복 가능한 검증 |
| Programmatic | Skills API로 체계적 평가 | 대규모 배포, 엔터프라이즈 |

### 3가지 테스트 영역

#### 1. Triggering Tests (트리거 테스트)

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless skill handles sheets)
```

**디버깅**: Claude에게 물어보기 → "When would you use the [skill name] skill?"
→ Claude가 description을 인용하며 답함 → 부족한 부분 파악

#### 2. Functional Tests (기능 테스트)

```
Test: Create project with 5 tasks
Given: Project name "Q4 Planning", 5 task descriptions
When: Skill executes workflow
Then:
- Project created in ProjectHub
- 5 tasks created with correct properties
- All tasks linked to project
- No API errors
```

#### 3. Performance Comparison (성능 비교)

| | Without Skill | With Skill |
|---|---|---|
| 메시지 교환 | 15 back-and-forth | 2 clarifying questions |
| API 실패 | 3 retries | 0 failures |
| 토큰 소비 | 12,000 | 6,000 |
| 워크플로우 | 수동 지시 | 자동 실행 |

### Pro Tip

> 가장 효과적인 스킬 작성자는 단일 어려운 작업에서 Claude가 성공할 때까지 반복한 후, 성공한 접근법을 스킬로 추출한다. Claude의 인컨텍스트 학습을 활용하며, 넓은 테스트보다 빠른 신호를 제공한다.

---

## 11. 피드백 기반 반복

### Under-triggering 신호

- 스킬이 로드되어야 할 때 안 됨
- 사용자가 수동으로 활성화
- "언제 사용하나요?" 같은 지원 질문

→ **해결**: description에 더 많은 디테일과 뉘앙스 추가, 특히 기술 용어 키워드

### Over-triggering 신호

- 무관한 쿼리에서 스킬 로드
- 사용자가 비활성화
- 목적에 대한 혼란

→ **해결**: negative trigger 추가, 더 구체적으로 범위 한정

### 지시사항 미준수

1. 지시사항이 너무 장황 → 간결하게, references/로 이동
2. 중요 지시사항이 파묻힘 → 상단 배치, CRITICAL 헤더
3. 모호한 언어 → 구체적 조건과 체크리스트로 변환
4. 중요 검증 → 스크립트로 번들 (코드는 결정적, 언어 해석은 아님)

---

## 12. 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| "Could not find SKILL.md" | 파일명 정확하지 않음 | `SKILL.md` (대소문자 정확히) |
| "Invalid frontmatter" | YAML 포맷 오류 | `---` 구분자 확인, 따옴표 닫기 확인 |
| "Invalid skill name" | 공백 또는 대문자 | kebab-case만 사용 |
| 스킬 트리거 안됨 | description 너무 모호 | 트리거 문구 추가, 파일 타입 명시 |
| 스킬 과잉 트리거 | description 너무 넓음 | negative trigger, 범위 구체화 |
| 지시사항 미준수 | 장황하거나 모호 | 간결하게, CRITICAL 헤더, 스크립트 검증 |
| MCP 호출 실패 | 연결/인증 문제 | MCP 서버 상태 확인, API 키 유효성, 도구 이름 정확성 |
| 응답 느림/품질 저하 | 컨텍스트 과다 | SKILL.md 5000단어 이내, references/로 분리, 동시 활성 스킬 20-50개 이내 |

---

## 13. 배포 및 공유

### 현재 배포 모델

**개인 사용자:**
1. 스킬 폴더 다운로드
2. 폴더 zip 압축
3. Claude.ai → Settings > Capabilities > Skills에 업로드
4. 또는 Claude Code skills 디렉토리에 배치

**조직 수준:**
- 관리자가 워크스페이스 전체에 스킬 배포 가능 (2025년 12월 출시)
- 자동 업데이트, 중앙 관리

**API 사용:**
- `/v1/skills` 엔드포인트로 스킬 관리
- Messages API의 `container.skills` 파라미터로 스킬 추가
- Claude Agent SDK와 함께 사용 가능

### 추천 배포 방법

1. **GitHub에 호스팅**: 공개 리포, README, 사용 예시 + 스크린샷
2. **MCP 리포에 문서화**: MCP 문서에서 스킬 링크, 함께 사용하는 가치 설명
3. **설치 가이드 제공**: 단계별 설치 지침

### 포지셔닝 원칙

```
✅ 결과 중심: "ProjectHub 스킬로 팀이 완전한 프로젝트 워크스페이스를
   몇 초 만에 설정할 수 있습니다 — 30분 수동 설정 대신."

❌ 기능 중심: "ProjectHub 스킬은 YAML frontmatter와 Markdown 지시사항을
   포함하는 폴더로 MCP 서버 도구를 호출합니다."
```

---

## 14. 빠른 체크리스트 (Reference A)

### 시작 전

- [ ] 2-3개 구체적 사용 사례 식별
- [ ] 필요한 도구 식별 (내장 또는 MCP)
- [ ] 가이드와 예제 스킬 검토
- [ ] 폴더 구조 계획

### 개발 중

- [ ] 폴더명 kebab-case
- [ ] SKILL.md 파일 존재 (정확한 철자)
- [ ] YAML frontmatter에 `---` 구분자
- [ ] name 필드: kebab-case, 공백/대문자 없음
- [ ] description에 WHAT과 WHEN 포함
- [ ] XML 태그 (`<>`) 없음
- [ ] 지시사항이 명확하고 실행 가능
- [ ] 에러 핸들링 포함
- [ ] 예제 제공
- [ ] 참조 파일 명확히 링크

### 업로드 전

- [ ] 명확한 작업에서 트리거 테스트
- [ ] 변형된 표현으로 트리거 테스트
- [ ] 무관한 주제에서 트리거되지 않음 확인
- [ ] 기능 테스트 통과
- [ ] 도구 통합 작동 확인 (해당 시)
- [ ] .zip 압축 (Claude.ai 업로드 시)

### 업로드 후

- [ ] 실제 대화에서 테스트
- [ ] under/over-triggering 모니터링
- [ ] 사용자 피드백 수집
- [ ] description과 지시사항 반복 개선
- [ ] 메타데이터에 버전 업데이트
