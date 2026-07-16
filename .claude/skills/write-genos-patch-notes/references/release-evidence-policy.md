# GenOS 릴리스 증거 정책

## 목적

패치노트의 범위와 공개 여부를 코드 흔적만으로 과장하지 않도록 증거의 우선순위와 판정 규칙을 고정한다.

## 증거 우선순위

같은 항목에 증거가 충돌하면 아래 순서를 기준으로 판단하고, 충돌 자체를 문서 상태에 기록한다.

1. 접근 가능한 사내 공식 릴리스 원문 또는 승인된 Notion 페이지
2. target tag에 포함된 curated release metadata
3. target과 predecessor tag 사이의 Git diff
4. schema migration, 배포 manifest, 환경변수와 설정 변화
5. tests, UI label, API contract
6. 현재 checkout의 코드 흔적

현재 checkout은 target tag와 다를 수 있으므로 target 릴리스의 확정 근거로 단독 사용하지 않는다.

## 기본 조사 순서

### 1. repository와 ref 확인

```bash
git status --short --branch
git tag --list 'v*' --sort=version:refname
git rev-parse --verify 'refs/tags/<target>'
git rev-parse --verify 'refs/tags/<predecessor>'
git merge-base --is-ancestor '<predecessor>' '<target>'
git diff --stat '<predecessor>..<target>'
```

tag가 annotated인지 lightweight인지보다 실제 commit과 tree가 무엇인지가 중요하다. 같은 버전명의 branch가 있어도 tag와 동일하다고 가정하지 않는다.

### 2. curated release metadata 찾기

우선 target tag의 tree에서 release metadata를 찾는다. 알려진 예시는 `admin-api/static/version.ini`지만 경로가 바뀔 수 있으므로 없으면 파일명과 버전 문자열을 검색한다.

```bash
git show '<target>:admin-api/static/version.ini'
git grep -n '"version": "<target>"' '<target>'
```

metadata에 기록된 항목을 먼저 ledger로 만들고, diff는 각 항목의 의미와 영향 범위를 보강하는 데 사용한다.

### 3. 변경 영역 분류

```bash
git diff --name-status '<predecessor>..<target>'
git diff '<predecessor>..<target>' -- '*migration*' '*.sql' '*.yaml' '*.yml' '*.env*'
```

필요할 때만 기능명, UI label, API route를 중심으로 관련 diff를 좁힌다. 전체 diff를 그대로 패치노트 항목으로 변환하지 않는다.

## 공개 여부 판정

| 상태 | 판정 기준 | 패치노트 처리 |
|---|---|---|
| 공식 공개 | 공식 원문 또는 curated metadata에 있으며 구현 근거와 모순되지 않음 | 해당 분류의 본문에 상세 작성 |
| 부분 확인 | 공식 항목이지만 동작 범위 일부를 코드에서 확인하지 못함 | 공식 항목으로 쓰되 미확인 경계를 표시 |
| 비공개 흔적 | 코드나 migration에는 있으나 공식 항목에 없음 | 공개 범위 제외 항목으로 분리하거나 생략 |
| 판단 보류 | 공식 자료와 target tree가 충돌하거나 target ref가 불명확함 | 단정하지 않고 문서 상태에 충돌 기록 |
| 고객사 전용 | 고객사 branch 또는 별도 overlay에만 존재 | 사용자가 요청한 경우 별도 고객사 섹션에만 작성 |

코드가 존재한다는 사실은 사용자에게 공개됐다는 증거가 아니다. UI, 권한, feature flag, 배포 설정에 따라 비활성일 수 있다.

## Notion 접근 규칙

- 사용자가 URL을 제공하면 먼저 접근 가능 여부를 확인한다.
- 로그인이나 권한으로 접근할 수 없으면 우회해서 내용을 추측하지 않는다.
- 접근 불가 사실은 `문서 상태`에 한 문장으로 기록한다.
- Notion 없이 작성할 때는 target tag의 curated metadata를 공식 항목 기준으로 삼고, 이를 “Notion 대조 완료”라고 표현하지 않는다.
- 이후 원문을 확보해 재검토할 때는 항목 추가·삭제·표현 차이를 ledger 단위로 대조한다.

## 릴리스 범위 규칙

- target 이후 commit은 포함하지 않는다.
- CVE suffix tag는 base release와 별도 릴리스로 본다.
- predecessor와 target 사이에 patch tag가 있으면 사용자가 요청한 업데이트 출발점에 맞춰 비교한다.
- 여러 버전을 한 번에 요청하면 버전별 공식 항목을 먼저 분리한 뒤 누적 upgrade 주의사항을 마지막에 합친다.
- 고객사 현재 버전을 모르면 플랫폼 누적 변경은 작성할 수 있지만 실제 적용 가능성과 migration 순서를 확정하지 않는다.

## 성능과 버그 표현 규칙

- benchmark나 측정 결과가 없으면 “몇 배 향상”, “응답 시간이 단축됐다” 같은 정량 표현을 쓰지 않는다.
- 코드 구조 개선만 확인된 경우 사용자 체감 성능 개선으로 단정하지 않는다.
- 버그 수정은 재현 증상과 수정 결과를 중심으로 쓰고, root cause는 확인된 경우에만 쓴다.
- migration이 존재하면 schema 변경 사실과 운영 확인사항을 구분한다. migration 파일만으로 무중단 적용을 보장하지 않는다.

## 내부 ledger 완료 조건

다음 질문에 모두 답할 수 있어야 본문 작성을 시작한다.

- 공식 항목 수와 각 분류는 무엇인가?
- 각 항목이 target 범위 안에 있는가?
- 공개 기능과 코드 흔적을 구분했는가?
- 사용자 흐름과 운영 영향 중 확인하지 못한 부분은 무엇인가?
- DB, 설정, 외부 dependency 변화가 있는가?
- 최종 노트에서 제외해야 할 고객사·CVE·후속 변경은 무엇인가?
