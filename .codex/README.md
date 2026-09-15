# Codex / GPT-6 Astra

2026-09-13에 [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)를 기준으로 정리했다. 개인 업무 지식과 필요한 보호 장치는 유지하고, 일반 지식·반복 절차·중복 도구가 기본 문맥에 들어오는 양을 줄인다. Claude와 Codex의 지침·스킬·훅 설정은 각각 관리한다.

## 소유권과 실제 연결

| 항목 | Codex 정본 / 실행 경로 | Claude 정본 / 실행 경로 |
| --- | --- | --- |
| 협업 지침 | `.codex/AGENTS.md` → `~/.codex/AGENTS.md` | `.claude/docs/working-style.md` ← `~/.claude/CLAUDE.md`의 import |
| 개인 스킬과 자원 | `.codex/skills/` → `~/.agents/skills` | `.claude/skills/<name>/` → `~/.claude/skills/<name>` |
| 훅 | `.codex/hooks/`, `.codex/config/global.json` | `.claude/hooks/`, `.claude/settings.json` |
| 훅 설정 | `.codex/config/hook-settings.sh`의 `CODEX_ENABLE_*` | `zsh/path.zsh`의 `ENABLE_*` |

`install.sh`도 이 연결을 만든다. 두 스킬 디렉터리는 파일 자체가 분리되어 한쪽 수정이 다른 쪽으로 전파되지 않는다. Codex 스킬에 필요한 스크립트·템플릿·이미지·참고 문서도 함께 복사했다. Claude 스킬 37개와 그 자원은 최적화 전 원본으로 복원했다. Claude 협업 지침도 복원하고, 공유 범위를 설명하는 마지막 문장만 현재 구조에 맞췄다. Gemini는 기존대로 Claude 쪽 정본을 사용한다.

저장소 `AGENTS.md`와 시스템 도구, 연결용 `.env.local`은 공통 자산이다. Claude 설정을 조사하는 `cc-changelog-review`의 대상 경로와 Claude 작성법을 설명하는 `skill-guide`는 그 목적에 맞게 남겼다. 이들은 Claude 스킬을 Codex 실행 원본으로 연결하지 않는다.

## Astra 구성

- `config.toml.example`은 재설치용 기본값이다. 모델은 `gpt-6-astra`, reasoning은 `high`이며 모델 기본 compaction 설정을 사용한다.
- `~/.codex/config.toml`은 실제 설정과 앱 관리 상태다. 템플릿으로 통째로 덮어쓰지 않고 필요한 키만 반영한다. 인증·앱·프로젝트 신뢰·권한은 보존한다.
- `docs/runtime-diagnostics.md`는 실제 환경의 버전·원시 증거·재현 자격을 확인하는 Codex 참고 문서다. 해당 진단에서만 읽는다.
- 일반 검색은 native `web_search = "live"`를 사용한다. Brave와 Tavily MCP는 접속 설정을 보존한 채 비활성화했다. Context7, 공식 OpenAI Docs와 기존 업무 연결은 유지한다.

개인 스킬 37개 중 다음 15개는 Codex의 `[skills].config`에서 비활성화하고 원본을 보관한다. 경로는 모두 `.codex/skills/` 아래다.

- 일반 설계·탐색: `adr`, `api-design`, `project-overview`
- 문서·스킬 사용 절차 중복: `find-docs`, `skill-guide`
- 일반 SQL 지침: `sql-optimization-patterns`

나머지 22개는 GenOS·개인 vault·TIL·커밋 규칙·문서 변환·전용 도구 등 업무 지식과 자원을 제공한다. Codex 사본의 description을 짧게 정리하고 Obsidian 형식과 Excalidraw 예시는 필요할 때 읽는 references로 옮겼다. 필요한 스킬은 템플릿과 실제 설정에서 해당 override를 제거하거나 `enabled = true`로 바꾸면 된다.

Superpowers는 양쪽 모두 유지한다. Codex 원격 설치본은 `superpowers@openai-curated-remote` 6.3.0이며 `codex plugin list --json`에서 설치·활성 상태를 확인한다. Claude는 `superpowers@claude-plugins-official`을 별도로 활성화한다. Astra 정리는 Superpowers를 제거하는 조건이 아니다.

## 훅과 유지보수

Codex는 `pre-commit-gate.sh`, `block-rm.sh`, `file-dispatcher.sh` 세 훅을 등록한다. Ruff 기본값 1, env 파일 검사 0, secret 패턴 검사 0은 기존 선택을 유지한다. 민감한 키 파일 검사는 계속 항상 켜져 있다. 기본값은 `config/hook-settings.sh`에서 관리하며 명시적인 `CODEX_ENABLE_*` 환경 변수가 우선한다. Claude의 `ENABLE_*` 값을 바꿔도 Codex 검사에는 영향을 주지 않는다.

중복 문맥·프롬프트 재작성·자동 링크·자동 다중 모델 리뷰를 수행하던 Codex의 `session-context.sh`, `link-skills.sh`, `prompt-rewriter.sh`, `til-review.sh`, `vault-linker.sh`는 등록과 복제본을 제거했다. Claude 훅은 유지한다. 제거한 Codex 훅은 Git 이력에서 복원할 수 있다.

Codex 개인 스킬은 `.codex/skills/<name>/`에서 수정하거나 추가한다. 디렉터리 링크이므로 별도 Claude 동기화가 필요 없다. 스크립트의 로컬 의존성·캐시는 각 도구의 스킬 디렉터리에서 관리한다.

## 적용과 검증 범위

변경 후 새 Codex 세션을 시작한다. 현재 대화에 이미 들어온 지침·스킬 목록은 소급해서 바뀌지 않는다. 앱에서 이전 목록이 계속 보이면 앱을 다시 실행한다.

검증 대상은 실제 링크, Claude 원본 보존, TOML/JSON 파싱, strict doctor, CLI 프롬프트의 스킬 경로와 비활성 처리, 유지한 훅의 동작 및 pre-commit 검사다. `install.sh` 전체 실행은 패키지와 다른 앱 설정까지 바꾸므로 수행하지 않는다. 실제 작업 속도·정답률·토큰 비용 개선은 별도 측정이 필요하다.

설정 형식은 [Codex skills](https://developers.openai.com/codex/skills)와 [configuration reference](https://developers.openai.com/codex/config-reference)를 따른다.
