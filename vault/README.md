# vaultkit — Obsidian vault 운영 가이드와 작업 기록

이 폴더는 Obsidian vault(`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note`)와 TIL 저장소(`~/dev/TIL`)의 노트 규칙을 한곳에서 관리한다. 사람도 Claude도 vault 구조나 동기화가 헷갈리면 이 문서부터 읽는다.

- 규칙 원본: `vault-policy.json` (태그 허용 목록·변경표, 폴더별 frontmatter 순서, MOC·허브 대응표)
- 스킬이 따르는 규칙 요약: `references/note-rules.md`
- 설계 문서: `~/.dotfiles/docs/superpowers/specs/2026-09-26-vault-policy-design.md`, 구현 계획: `~/.dotfiles/docs/superpowers/plans/2026-09-26-vault-policy.md` (둘 다 git 비추적)

## 1. 어디서 무엇을 고치나

| 고칠 것 | 어디서 | 이유 |
|---|---|---|
| TIL 노트 본문 | `~/dev/TIL` | 본문 원본은 TIL. 커밋·pull 때 Wiki로 자동 반영 |
| TIL 노트 태그 | `~/dev/TIL/tag-mapping.json` | Wiki에서 고친 태그는 다음 동기화 때 TIL 값으로 돌아감 |
| TIL 노트의 `related_notes`·`created` | Obsidian(Wiki) | 이 두 필드는 Wiki가 원본, 동기화가 보존 |
| Wiki 전용 노트(TIL에 없음) | Obsidian | 원본이 Wiki뿐 |
| Projects·Sources·Archive | Obsidian | TIL과 무관 |

TIL 노트 판별: 하이픈 파일명 + `til` 태그. 정확히는 `~/dev/TIL/<폴더>/<같은 이름>.md`가 있는지로 판단한다.

## 2. 명령

```bash
python3 ~/.dotfiles/vault/vk check              # 규칙 위반 점검(읽기 전용, 위반 있으면 exit 1)
python3 ~/.dotfiles/vault/vk apply --dry-run    # 기계적 수정 미리보기
python3 ~/.dotfiles/vault/vk apply              # 태그·frontmatter 정규화 + MOC·허브 등록 (쓰기 전 백업)
python3 ~/.dotfiles/vault/vk apply --til-mapping # tag-mapping.json 정규화
python3 ~/.dotfiles/vault/vk register <file>    # 노트 하나 정규화·등록 (스킬이 저장 후 호출)
python3 ~/dev/TIL/.githooks/sync-to-obsidian.py [--dry-run] [--verbose]  # TIL→Wiki 전체 동기화
cd ~/.dotfiles/vault && python3 -m unittest discover -s tests -v          # 테스트
```

TIL git hook: post-commit은 `--diff`(바뀐 파일만), post-merge는 전체 동기화를 돌린다.

## 3. 경고가 나오면

**`⚠️ 이관 필요(Wiki 본문 수정됨)`** — Wiki에서 TIL 노트 본문을 고쳤다는 뜻. 동기화는 그 노트 본문을 덮지 않고 멈춘다(내용 손실 없음, 대신 TIL 수정도 반영 안 됨).
1. TIL은 안 고쳤으면: Wiki 본문을 TIL로 옮긴다.
   ```bash
   python3 ~/.dotfiles/vault/scripts/til_backport.py --plan --out /tmp/bp
   python3 ~/.dotfiles/vault/scripts/til_backport.py --apply --out /tmp/bp --only <노트> --real
   ```
   직접 TIL 파일에 같은 수정을 복사해도 된다. 두 본문이 같아지면(링크 표기 차이는 무시) 다음 동기화가 자동으로 정상화한다.
2. TIL도 고쳤으면(plan이 `diverged`로 표시, `--apply`가 기본 제외): 3-way 병합한다.
   - 공통 조상 = plan.json의 `base.commit` 시점 TIL 파일(`git show <commit>:<폴더>/<노트>.md`)
   - Wiki 본문은 `vaultkit.tilsync.reverse_port`로 TIL 형식으로 바꾼 뒤 `git merge-file <til> <base> <wiki>`
   - 충돌 0이면 결과를 TIL에 쓰고, `Wiki/.til-sync-state.json`의 해당 노트 `body_sha`를 현재 Wiki 본문 해시(`tilsync.body_sha`)로 바꾼 뒤 동기화 → `update` 후 재실행 `unchanged` 확인
   - 2026-09-27 ConfigMap-Secret·Deployment-Strategy·Ingress 3편을 이 방식으로 처리했다.
3. Claude에게 "<노트> TIL로 옮겨줘"라고 하면 위 절차를 수행한다.

**`⚠️ 충돌`** — TIL에 새 노트가 생겼는데 Wiki에 같은 이름(대소문자만 달라도)의 Wiki 전용 노트가 있음. 한쪽 이름을 바꾼다.

**`📋 MOC 미분류`** / `vk check`의 `moc-missing`·`hub-missing` — 태그로 MOC·허브 섹션을 못 정함. 태그를 고치거나(섹션은 **첫 번째로 매칭되는 태그**로 정해진다) `vault-policy.json`의 `moc`/`hubs`에 대응을 추가한다.

**`empty-after-normalize`** — 태그를 정리하면 하나도 안 남는 노트(예: Wiki에 업무용 태그만 있는 노트). apply가 건드리지 않으니 위치와 태그를 사람이 정한다.

## 4. 백업과 복구

| 위치 | 내용 |
|---|---|
| `~/.local/state/vaultkit/backups/<시각>/` | `vk apply`가 쓰기 전 원본 |
| `~/.local/state/vaultkit/backups/til-sync-<시각>/` | 동기화가 덮어쓴 Wiki 파일 원본 |
| `~/.local/state/vaultkit/snapshots/pre-migration-20260927-074942/` | 최초 이관 직전 Wiki 폴더 전체 + TIL tar |
| `~/.local/state/vaultkit/removed/` | vault에서 뺀 노트(macOS 휴지통이 iCloud 폴더에서 권한 오류를 내서 여기로 옮김) |

vault 파일 삭제는 `trash`가 iCloud 경로에서 `Code=513` 권한 오류를 낼 수 있다. 그때는 `removed/`로 `mv`한다.

## 5. 작업 기록

### 2026-09-26 ~ 27: 노트 생성 경로 단일 규칙화

배경: 노트를 만드는 경로(스킬 9개 Claude·Codex 두 판, TIL 동기화)가 각자 규칙을 써서 태그 515종·frontmatter 순서 불일치가 생겼고, TIL 동기화는 파일 전체 해시 가드 때문에 210편 중 204편이 동결돼 있었다.

결정(설계 대화):
- D1 본문 원본은 TIL. Wiki에서만 고친 본문은 1회 TIL로 이관
- D2 TIL에 없는 Wiki 노트는 Wiki 전용(`til` 태그 제거)
- D3 MOC·허브는 태그 대응표로 자동 등록, 못 정하면 미분류 보고
- D4 Claude·Codex 스킬은 공통 규칙 문서 하나를 가리킴
- D5 공용 모듈 `vaultkit` 하나를 모든 경로가 사용(표준 라이브러리만)

한 일:
- `vaultkit`(policy·frontmatter·tags·register·check·apply·tilsync), `vk` CLI, 테스트 210개
- TIL 동기화를 필드 단위 병합으로 교체(본문·title·source·topics·tags는 TIL, related_notes·created는 Wiki), 상태 파일 v2(`Wiki/.til-sync-state.json`)
- 최초 이관: Wiki 본문 81편 + 출처 URL 4개를 TIL로(`--carry-sources`), 양쪽 수정 3편은 3-way 병합, Helm 1편은 옛 사본이라 TIL 최신으로 갱신. 옛 SKIP 6편은 `retired`
- 태그 일괄 정규화 148편, 미분류 TIL 20편 태깅, `design-pattern/factory`→`cs/design-pattern`
- 스킬 정비: obsidian-note·youtube-summarizer·translate-article·tech-blog-writer·genos-knowledge-capture·write-genos-patch-notes·til·til-tagger·vault-linter(두 판). `agentic-notes`·`learning-tracker` 삭제
- vault 정리: kubectl 노트 → `Projects/GenonAI/삼성증권`, `Templates/Prompts` → `Sources/Prompts`, `Genos 현장 FDE 학습 로드맵` 제거, 고객사 허브 `00 … 시작하기` 4편 신설(09-26)

남은 것:
- (해결 2026-09-27) `Sources/Clippings`의 파일명에서 ` | kciter.so`를 빼 `vk check` 위반 0
- notebook-navigator 템플릿 폴더 설정(`Templates`)이 Obsidian 재시작 후에도 유지되는지 확인
- 진행 원장(판정 35건 포함): `~/.dotfiles/.superpowers/sdd/2026-09-26-vault-policy/progress.md` (git 비추적)
