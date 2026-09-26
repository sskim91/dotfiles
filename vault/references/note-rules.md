# Vault 노트 공통 규칙

개인 Obsidian vault에 노트를 쓰는 모든 스킬(obsidian-note, youtube-summarizer, translate-article, tech-blog-writer, genos-knowledge-capture, write-genos-patch-notes, til, til-tagger, vault-linter)이 따르는 규칙이다. Claude판·Codex판 스킬이 모두 이 문서를 가리킨다. 스킬 본문에는 저장 위치·본문 구조 같은 스킬 고유 절차만 두고, 아래 규칙은 복제하지 않는다.

- 기계가 읽는 정본: `~/.dotfiles/vault/vault-policy.json` (허용 분야, rename·drop 표, 폴더별 frontmatter, MOC·허브 대응표)
- 도구: `python3 ~/.dotfiles/vault/vk {check|apply|register|derive-maps}`
- 설계 문서: `~/.dotfiles/docs/superpowers/specs/2026-09-26-vault-policy-design.md`
- Vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note` (공백 포함, 셸에서는 항상 따옴표. 따옴표 안에서는 `~`가 풀리지 않으므로 `"$HOME/..."`로 쓴다)

규칙과 policy가 어긋나면 policy가 맞다. 이 문서를 고친다.

## 1. 폴더별 frontmatter

필드는 아래 순서로만 쓴다. 표에 없는 필드는 추가하지 않는다(claim ledger, 판단 근거 같은 긴 정보는 본문에 둔다). 값이 없는 리스트 필드는 `[]`로 남긴다.

| 위치 | 필드 순서 | 필수 |
|---|---|---|
| `Wiki/`, `_Inbox/` | `title`, `source`, `topics`, `related_notes`, `tags`, `created` | `title`, `tags` |
| `Projects/` | `aliases`, `title`, `source`, `related_notes`, `tags`, `created` | `tags`, `created` |
| `Sources/` | `aliases`, `title`, `source`, `related_notes`, `tags`, `created` | `tags` |
| `Archive/` | `aliases`, `title`, `source`, `topics`, `related_notes`, `tags`, `created` | 없음 |

- `_Inbox`는 Wiki로 옮겨 갈 노트의 대기실이므로 Wiki 형식으로 쓴다.
- `aliases`는 선택 필드다. 필요할 때만 맨 앞에 둔다.
- `title`은 파일명과 같은 순수 제목이다. `created`는 `YYYY-MM-DD`.
- `source`는 리스트다(URL 또는 근거 식별자). `related_notes`는 `"[[실존하는 노트]]"` 리스트다.
- `topics`(Wiki만)는 Wiki 상위 주제 1~2개다. 값은 policy `topics`의 값 중에서 고른다(예: `AI`, `Kubernetes`, `Computer Science`).

```bash
jq -r '.topics[]' ~/.dotfiles/vault/vault-policy.json | sort -u
```

## 2. 태그

- 형식: 정확히 두 세그먼트 `domain/sub`, 소문자·하이픈(예: `kubernetes/helm`, `ai/mcp`). 세 세그먼트 이상은 쓰지 않는다.
- `domain`은 policy `tags.domains` 안에서만 고른다. 목록을 기억으로 쓰지 말고 매번 읽는다.

```bash
jq -r '.tags.domains[]' ~/.dotfiles/vault/vault-policy.json
```

- 한 세그먼트 태그는 `tags.single_segment_allowed`(`til`, `clippings`, `translation`, `translation-summary`)만 허용한다.
- `work/`, `customer/`, `feature/`, `type/` facet 태그는 `Projects/` 노트 전용이다. Projects 밖 노트에 쓰면 `vk apply`가 제거한다.
- `til` 태그는 TIL에서 파생된 Wiki 노트에만 붙는다(아래 4절). 직접 쓰는 노트에는 붙이지 않는다.
- `untagged`, `status/*` 같은 임시 태그는 남기지 않는다.
- 옛 태그(`infra/k8s`, `gotcha` 등)는 `tags.rename`이 새 태그로 바꾼다. 새 노트는 처음부터 rename 결과 쪽 태그를 쓴다.
- 허브·MOC 섹션은 `tags` 목록에서 처음 매칭되는 태그로 정해진다. 섹션을 정할 태그(Wiki는 주제 `domain/sub`, 고객사 노트는 `feature/*`)를 범용 태그(`type/*`, `work/*`)보다 앞에 쓴다. 권장 순서는 `customer/*`(해당 시) → `feature/*`·`domain/sub` → `type/*` → `work/*`다.
- `vk register`는 태그를 새로 짓거나 고치지 않는다. 허용 목록 밖 태그는 `vk check`에 `[tag]`로 드러나며, 쓰는 스킬이 대화 중에 다시 고른다.

## 3. 저장 후 등록 (필수)

노트를 저장하거나 `_Inbox`에서 다른 폴더로 옮긴 직후 반드시 실행한다.

```bash
python3 ~/.dotfiles/vault/vk register "<노트 절대 경로>"
```

출력은 `상태<TAB>파일<TAB>대상 허브/MOC<TAB>섹션<TAB>추가한 줄`이다.

| 상태 | 뜻 | 할 일 |
|---|---|---|
| `added` | 허브/MOC에 한 줄 추가함 | 자동 요약 한 줄을 읽기 좋게 다듬는다 |
| `exists` | 이미 등록돼 있음 | 없음 |
| `unclassified` | 대응표로 섹션을 정하지 못함 | 태그·하위폴더를 확인하고, 맞으면 허브에 직접 추가하고 보고한다 |
| `skipped` | 등록 대상 아님 | 없음 |

- 등록 대상은 `Wiki/` 바로 아래 노트와 `Projects/` 허브 아래 노트뿐이다. `_Inbox`, `Sources`, `Archive`, `Templates`는 `skipped`이므로 실행해도 아무것도 바뀌지 않는다. 그래도 저장 후에는 습관적으로 실행하고 결과를 보고한다.
- Wiki 노트는 `tags`로 `Wiki/_MOC/MOC-*.md`의 섹션이 정해진다(policy `moc`).
- 결과(상태, 대상, 섹션)는 사용자에게 그대로 보고한다.
- `added`의 섹션이 의도와 다르면 허브에 들어간 줄을 옮기지 말고, 먼저 허브에서 그 줄을 지운 뒤 `tags` 순서를 고쳐 다시 실행한다(2절 첫 매칭 규칙).

## 4. 원본 규칙 — TIL 파생 노트와 Wiki 전용 노트

Wiki에는 두 종류의 노트가 섞여 있다.

| 종류 | 원본 | 표시 | 고치는 곳 |
|---|---|---|---|
| TIL 파생 | `~/dev/TIL/<폴더>/<이름>.md` | `til` 태그 | 본문·제목·source·topics·tags는 TIL 원본과 `tag-mapping.json` |
| Wiki 전용 | Wiki 파일 자체 | `til` 태그 없음 | Wiki 파일 |

- TIL 파생 노트의 Wiki 본문은 직접 고치지 않는다. TIL에서 고치고 커밋하면 post-commit 동기화(`~/dev/TIL/.githooks/sync-to-obsidian.py`)가 반영한다.
- Wiki 본문을 고치면 다음 동기화는 본문을 유지하고 frontmatter만 병합해 쓰며 "Wiki 본문 수정됨 → TIL로 이관 필요"로 보고한다. 그 수정을 TIL 원본으로 옮겨 커밋하면 다음 동기화에서 본문이 다시 TIL 값으로 정상화된다.
- Wiki 전용 노트와 이름이 겹치는 TIL 노트는 쓰지 않고 충돌로 보고한다.
- 동기화는 필드 단위로 병합한다.

| 필드 | 원본 | 동작 |
|---|---|---|
| `title`, `source`, 본문 | TIL | TIL 값 |
| `topics` | TIL 폴더 | policy `topics[폴더]` |
| `tags` | `tag-mapping.json` | policy로 정규화 + `til`. 매핑이 없으면 `<til_folder_domain 또는 폴더>/untagged` |
| `related_notes` | Wiki | Wiki 목록 유지 + TIL 본문 링크 중 목록에 없는 것만 뒤에 추가 |
| `created` | Wiki | 있으면 유지, 없으면 최초 동기화 날짜 |

- 따라서 TIL 파생 노트의 `related_notes`는 Wiki에서 추가해도 된다.
- TIL 태그는 `~/dev/TIL/tag-mapping.json`(파일명 → 태그 배열)이 정본이다. 동기화가 policy로 정규화하고 `til`을 붙인다.
- Wiki에서 지우거나 `Archive/`로 옮긴 TIL 노트는 다시 생성되지 않는다(retired).
- Wiki 전용 노트는 TIL 노트와 같은 파일명을 쓰지 않는다(동기화 충돌).

## 5. 허브 대응표 요약

정확한 값은 policy `hubs`, `genos_subfolders`, `moc`에 있다.

| 노트 위치 | 허브 | 섹션 결정 |
|---|---|---|
| `Wiki/<노트>.md` | `Wiki/_MOC/MOC-*.md` | 태그 → policy `moc` |
| `Projects/GenonAI/GenOS/0X .../<노트>.md` | `00 GenOS 시작하기` | 하위폴더 이름 = 섹션 |
| `Projects/GenonAI/GenOS/패치노트/<노트>.md` | `GenOS 버전별 변경 요약` | 버전 순서로 표 행 삽입 |
| `Projects/GenonAI/삼성증권/` | `00 삼성증권 시작하기` | 태그 → `section_by_tag` |
| `Projects/GenonAI/삼성카드/` | `00 삼성카드 시작하기` | 태그 → `section_by_tag` |
| `Projects/GenonAI/삼성카드_모니모/` | `00 모니모 시작하기` | 태그 → `section_by_tag` |
| `Projects/GenonAI/인사연동 배치 분석/` | `00 인사연동 배치 분석 시작하기` | 태그 → `section_by_tag` |

- GenOS 하위폴더는 `01 온보딩·로컬개발`부터 `08 운영·런북`까지 8개다(policy `genos_subfolders`, 폴더별 대표 태그 포함). `GenOS/` 바로 아래에 두면 `unclassified`가 된다.
- 고객사 노트는 해당 고객사 `section_by_tag`에 있는 태그를 하나 이상 달아야 섹션이 정해진다. `section_by_tag`에는 `type/pattern` 같은 범용 태그도 들어 있으므로, 섹션을 정할 `feature/*` 태그를 `type/*`보다 앞에 둔다(2절 첫 매칭 규칙).

고객사 폴더별 `customer/` 태그(기존 노트 기준, 새로 짓지 않는다):

| 고객사 폴더 | `customer/` 태그 |
|---|---|
| `삼성증권/` | `customer/samsung-securities` |
| `삼성카드/` | `customer/samsung-card` |
| `삼성카드_모니모/` | `customer/samsung-card` |
| `인사연동 배치 분석/` | 없음(달지 않는다) |

표에 없는 폴더는 같은 폴더 기존 노트의 `customer/*` 태그를 그대로 쓰고, 기존 노트에도 없으면 사용자에게 묻는다.

```bash
jq '.hubs, .genos_subfolders' ~/.dotfiles/vault/vault-policy.json
```

## 6. 링크

- `related_notes`와 본문 wikilink는 vault에 실존하는 노트(또는 이번에 함께 만드는 노트)만 가리킨다.
- 본문에 `## 연결`·`## 연결 고리` 같은 연결 목록 섹션을 만들지 않는다. 연결 목록은 `related_notes`에만 둔다.
- 관련 노트를 검색할 때 `Templates/`, `.obsidian/`, `_Inbox/Vault-Index.md`, `Archive/`, `Wiki/_MOC/`는 제외한다.
- 후속 탐구 목록은 `## 남은 질문` 섹션에 둔다.

## 7. 점검과 적용

```bash
python3 ~/.dotfiles/vault/vk check            # 읽기 전용, 위반 시 exit 1
python3 ~/.dotfiles/vault/vk apply --dry-run  # 바뀔 파일만 출력
python3 ~/.dotfiles/vault/vk apply            # 사용자 승인 후에만
```

- `apply`는 태그 rename·drop, frontmatter 순서, 대응표로 정해지는 등록, MOC 개수 표기만 기계적으로 고친다. 실행 전 대상 파일을 `$TMPDIR/vaultkit-backup/<timestamp>/`에 복사한다.
- TIL 파생 노트의 태그는 Wiki가 아니라 `vk apply --til-mapping`(tag-mapping.json 정규화) 뒤 동기화로 고친다.
