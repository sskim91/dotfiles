---
name: write-genos-patch-notes
description: Create detailed Korean GenOS patch notes by reconciling a target release with its predecessor across curated release metadata, Git tags and diffs, migrations, configuration changes, and available Notion content, then save the note to the user's Obsidian vault and maintain MOC discoverability. Use when the user asks for a GenOS version patch note, release note, upgrade summary, changes since a version, or customer-update release material such as "v1.8.7 패치노트", "1.8.6부터 변경사항", or "고객사 업데이트용 릴리스 노트". Do NOT use for generic GenOS knowledge capture, session logs, or customer-specific branch notes unless the user explicitly includes them.
---

# Write GenOS Patch Notes

GenOS의 특정 릴리스를 이전 운영 버전과 비교해, 고객사 업데이트 검토에 사용할 수 있는 상세 한국어 패치노트를 작성한다. 공식 공개 항목과 코드에만 존재하는 흔적을 분리하고, 구현 근거는 내부 검증에 사용하되 최종 노트에는 노출하지 않는다.

## 필수 참조

작업을 시작할 때 다음 파일을 모두 읽는다.

- [references/release-evidence-policy.md](references/release-evidence-policy.md): 릴리스 범위와 증거 우선순위, 공개 여부 판정 기준
- [references/patch-note-format.md](references/patch-note-format.md): Obsidian 문서 구조와 항목별 상세 작성 기준

## 기본 작업 경로

- 플랫폼 기본 repository는 `~/work/GenOS`다. 현재 cwd가 다른 위치면 이 repository를 기준으로 조사한다.
- 조사 전에 Git top-level, origin의 `genonai/GenOS` 식별자, target tag 존재를 확인한다.
- 기본 경로가 없거나 target tag가 없으면 `~/work` 아래에서 후보를 찾고, 올바른 플랫폼 repository를 확정할 수 없을 때만 사용자에게 묻는다.
- `GenOS-samsung-securities` 같은 고객사 repository를 플랫폼 정식 릴리스의 기본 source로 자동 선택하지 않는다. 고객사 변경은 사용자가 명시적으로 포함한 경우에만 해당 repository와 branch를 별도 확인한다.

## 작업 경계

- 기본 범위는 플랫폼 정식 릴리스 tag 사이의 변경이다.
- CVE 변형 tag, 고객사 커스텀 브랜치, target 이후 hotfix는 사용자가 포함하라고 한 경우에만 다룬다.
- 고객사별 변경을 포함하면 플랫폼 기본 변경과 별도 섹션으로 분리한다.
- `genos-knowledge-capture`를 수정하거나 대체하지 않는다. 패치노트 작성 중 발견한 일반화 가능한 지식은 별도 요청이 있을 때만 그 Skill로 캡처한다.
- 회사 repository의 코드와 설정은 읽기 전용 증거로 사용한다. 패치노트 작성 요청만으로 제품 코드를 변경하지 않는다.

## 워크플로우

### 1. 요청과 완료 조건 확정

다음을 요청에서 추출한다.

- target version
- 비교 시작 version 또는 이전 정식 릴리스
- 플랫폼 기본 범위인지 고객사 브랜치까지 포함하는지
- 최종 산출물이 대화 초안인지 Obsidian 노트인지
- 사내 Notion 원문 접근 가능 여부

비교 기준이나 포함 범위가 결과를 크게 바꾸는데 확인할 수 없으면 한 가지 정밀한 질문만 한다. 그 외에는 안전한 기본값을 명시하고 진행한다.

노트를 새로 만들거나 범위를 크게 바꾸는 경우, 작성 전에 짧은 Plan과 완료 조건을 제시한다. 사용자가 이미 진행을 승인했다면 다시 묻지 않는다.

### 2. release ref와 비교 구간 검증

repository에서 target tag의 존재, predecessor tag, ancestry, 실제 tree를 확인한다. 단순 버전 문자열이나 현재 checkout을 배포본으로 가정하지 않는다.

predecessor 기본 선택 규칙:

1. target보다 낮은 가장 가까운 정식 production tag를 찾는다.
2. patch tag가 있으면 base minor tag보다 patch tag를 우선한다.
3. `-cve`, `-customer`, 임시 suffix tag는 기본 비교에서 제외한다.
4. tag topology가 모호하면 비교 후보와 차이를 사용자에게 보여준다.

### 3. 공식 항목 ledger 작성

`release-evidence-policy.md`의 우선순위대로 증거를 모은다. target tag 시점의 curated release metadata를 먼저 찾고, 각 공식 항목을 내부 ledger에 한 줄씩 등록한다.

ledger에는 최소한 다음을 기록한다.

| 필드 | 의미 |
|---|---|
| 공식 항목 | 릴리스 자료의 원문 항목 |
| 분류 | 신규·고도화 / 사용성·성능 / 버그 수정 |
| 검증 상태 | 확인 / 부분 확인 / 미확인 |
| 사용자 의미 | 사용자가 무엇을 할 수 있게 됐는지 |
| 운영 영향 | 설정, migration, dependency, 배포 영향 |
| 공개 여부 | 공개 / 비공개 흔적 / 판단 보류 |

ledger는 검증용이며 최종 노트에 코드 경로나 commit hash와 함께 복사하지 않는다.

### 4. tag diff로 의미와 경계 보강

공식 항목마다 관련 frontend, API, schema migration, Helm/config, tests를 확인한다. 목적은 기능을 새로 발굴해 부풀리는 것이 아니라 다음을 설명할 근거를 확보하는 것이다.

- 기존에 어떤 불편이나 제약이 있었는가
- 사용자는 어떤 흐름으로 기능을 사용하는가
- 운영자는 무엇을 설정하거나 확인해야 하는가
- 무엇까지 지원하며 무엇은 지원하지 않는가
- 기존 데이터와 배포에 어떤 주의가 필요한가

공식 자료에 없고 코드에만 흔적이 있는 기능은 공개 기능으로 승격하지 않는다. 필요하면 `공개 범위에서 제외된 항목`에 이유와 함께 기록한다.

### 5. 상세 패치노트 작성

`patch-note-format.md`의 구조를 그대로 사용한다. 특히 `신규 기능 및 고도화`와 `사용성 및 성능 개선`은 기능명만 나열하지 말고 다음 순서로 풀어쓴다.

1. 해결하려는 문제
2. 동작 방식과 사용자 흐름
3. 사용자 관점의 변화
4. 운영·관리 관점의 영향
5. 적용 범위와 헷갈리기 쉬운 경계

공식 자료가 짧아 세부 동작을 확정할 수 없으면 단정하지 않는다. 직접 확인한 사실, 합리적 해석, 미확인 영역을 문장 수준에서 구분한다.

### 6. Obsidian 저장과 연결

기본 vault와 저장 위치:

```text
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note
└── Projects/GenonAI/GenOS/GenOS v<version> 패치노트.md
```

navigation 노트의 고정 경로:

```text
<vault>/Projects/GenonAI/GenOS/GenOS 지식 MOC.md
<vault>/Projects/GenonAI/GenOS/GenOS 카테고리별 읽는 순서.md
```

macOS vault의 한글 파일명은 NFD Unicode로 저장될 수 있다. 이름 검색이 실패해도 파일이 없다고 결론 내리지 말고 위 literal path를 먼저 열어본다. 파일 목록을 비교해야 하면 이름을 NFC로 정규화한 뒤 대조한다.

저장 전 같은 버전의 노트를 검색한다. 기존 노트가 있으면 원문을 보존하면서 요청된 범위만 갱신하고, 새 중복 노트를 만들지 않는다.

노트의 `related_notes`에 `[[GenOS 지식 MOC]]`를 포함하고 MOC에 노트 링크가 없으면 적절한 릴리스·참고 영역에 추가한다. `GenOS 카테고리별 읽는 순서.md`도 열어보되, 릴리스 참고 기록은 학습 순서에 반드시 넣지 않는다. 추가하지 않았다면 그 이유를 결과에 남긴다.

### 7. 검증

완료를 선언하기 전에 다음을 실제 파일과 repository 상태로 확인한다.

- target과 predecessor가 정확하다.
- 공식 항목 ledger의 모든 항목이 본문에 반영됐다.
- `신규 기능 및 고도화`, `사용성 및 성능 개선`이 상세 작성 기준을 충족한다.
- 공개 기능과 비공개 코드 흔적이 분리됐다.
- 최종 노트 본문에 commit hash와 구현 코드 경로가 없다.
- `다음에 확인할 것` 섹션이 없다.
- frontmatter가 유효하고 MOC backlink가 있다.
- 새 노트가 MOC에서 발견 가능하다.
- 제품 repository에는 의도하지 않은 변경이 없다.

접근하지 못한 Notion, 확인할 수 없는 배포본, 누락된 tag가 있으면 문서 상태와 최종 보고에 한계를 명시한다. 확인하지 못한 내용을 완료된 사실처럼 표현하지 않는다.
