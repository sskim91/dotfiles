# Post-write Linking (지식 복리 패턴)

노트 작성/저장 완료 후 실행하는 양방향 링킹 절차.
Karpathy의 "filing back" 패턴 — 모든 노트가 기존 지식과 연결되어 탐색이 누적되는 구조.

## 절차

### 1. 새 노트에서 키워드 추출

작성한 노트의 `## 핵심 아이디어`(또는 `## 핵심 요약`)와 `tags`에서 검색 키워드 3-5개를 추출한다.

### 2. Vault에서 관련 노트 검색

```bash
VAULT="~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note"
grep -rli "키워드" "$VAULT" --include="*.md" | head -10
```

**검색 제외 대상:**
- 방금 작성한 노트 자신
- `99.Template/` 하위 파일
- `10.Flashcards/` 하위 파일

### 3. 양방향 related_notes 업데이트

**새 노트 → 기존 노트:**
새 노트의 frontmatter `related_notes`에 발견된 관련 노트를 `[[wikilink]]`로 추가.

**기존 노트 → 새 노트 (선택적):**
관련도가 높은 기존 노트(2개 이하)의 `related_notes`에 새 노트를 추가할지 사용자에게 제안.

> ⚠️ 기존 노트를 자동 수정하지 않는다. 반드시 "이 노트들에 역링크를 추가할까요?"로 사용자 확인.

### 4. 후속 탐구 큐 체크

발견된 관련 노트 중 `## 더 알아보기` 섹션에 현재 노트 주제와 겹치는 미탐구 항목이 있으면 알려준다:
"[[기존노트]]의 '더 알아보기'에 이 주제가 언급되어 있습니다. 체크오프할까요?"

## 출력 형식

```
📎 Post-write Linking 완료
├── 관련 노트 발견: N건
│   ├── [[노트A]] — tags 매칭
│   └── [[노트B]] — 키워드 매칭
├── related_notes 업데이트: 새 노트에 N건 추가
└── 역링크 제안: [[노트A]]에 역링크 추가? (y/n)
```

## vault-linker hook과의 관계

`ENABLE_VAULT_LINKER=1`이면 PostToolUse hook이 Write/Edit 시 vault 전체 노트 목록을 자동으로 Claude에게 전달한다.
이 경우 **Step 2의 grep 검색을 건너뛰고** hook이 제공한 노트 목록에서 의미적으로 관련된 노트를 직접 선택할 수 있다.

- hook 활성화 시: 노트 목록이 이미 컨텍스트에 있으므로 grep 없이 바로 Step 3으로
- hook 비활성화 시 (기본): Step 2의 grep 검색으로 관련 노트를 찾는 기존 절차 수행

## 스킵 조건

- 관련 노트가 0건이면 "관련 노트를 찾지 못했습니다" 한 줄로 끝낸다
- 사용자가 `--no-link` 플래그를 지정하면 이 단계를 건너뛴다
