# Codex / GPT-6 Astra

2026-09-13에 [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)를 기준으로 정리했다. 개인 업무 지식과 필요한 보호 장치는 유지하고, 일반 지식·반복 절차·중복 도구가 기본 문맥에 들어오는 양을 줄인다. Claude와 Codex의 지침·스킬·훅 설정은 각각 관리한다.

## 소유권과 실제 연결

| 항목 | Codex 정본 / 실행 경로 | Claude 정본 / 실행 경로 |
| --- | --- | --- |
| 협업 지침 | `.codex/AGENTS.md` → `~/.codex/AGENTS.md` | `.claude/docs/working-style.md` ← `~/.claude/CLAUDE.md`의 import |
| 개인 스킬과 자원 | `.codex/skills/` → `~/.agents/skills` | `.claude/skills/<name>/` → `~/.claude/skills/<name>` |
| 훅 | `.codex/hooks/`, `.codex/config/global.json` | `.claude/hooks/`, `.claude/settings.json` |
| 훅 설정 | `.codex/config/hook-settings.sh`의 `CODEX_ENABLE_*` | `zsh/path.zsh`의 `ENABLE_*` |

`install.sh`도 이 연결을 만든다. 두 스킬 디렉터리는 파일 자체가 분리되어 한쪽 수정이 다른 쪽으로 전파되지 않는다. Codex 스킬에 필요한 스크립트·템플릿·이미지·참고 문서도 함께 복사했다. 2026-09-15 정리 후 개인 스킬은 양쪽 각각 26개다. 도구별 description과 활성 상태는 독립적으로 관리한다. Gemini는 기존대로 Claude 쪽 정본을 사용한다.

저장소 `AGENTS.md`와 시스템 도구, 연결용 `.env.local`은 공통 자산이다. Claude 설정을 조사하는 `cc-changelog-review`의 대상 경로와 Claude 작성법을 설명하는 `skill-guide`는 그 목적에 맞게 남겼다. 이들은 Claude 스킬을 Codex 실행 원본으로 연결하지 않는다.

## Astra 구성

- `config.toml.example`은 재설치용 기본값이다. 모델은 `gpt-6-astra`, reasoning은 `high`이며 모델 기본 compaction 설정을 사용한다.
- 최상위 `suppress_unstable_features_warning = true`로 개발 중 기능의 시작 경고를 숨긴다. `chronicle` 등 기능의 활성 상태는 바꾸지 않는다.
- `~/.codex/config.toml`은 실제 설정과 앱 관리 상태다. 템플릿으로 통째로 덮어쓰지 않고 필요한 키만 반영한다. 인증·앱·프로젝트 신뢰·권한은 보존한다.
- `docs/runtime-diagnostics.md`는 실제 환경의 버전·원시 증거·재현 자격을 확인하는 Codex 참고 문서다. 해당 진단에서만 읽는다.
- 일반 검색은 native `web_search = "live"`를 사용한다. Brave와 Tavily MCP는 접속 설정을 보존한 채 비활성화했다. Context7은 챗앱에서 연결한 플러그인을 사용하며, 중복되는 `[mcp_servers.context7]`은 `enabled = false`로 보관한다. 새 환경에서는 플러그인 연결을 확인하고, 플러그인을 사용할 수 없으면 기존 MCP의 재활성화를 검토한다. 공식 OpenAI Docs와 기존 업무 연결은 유지한다.

개인 스킬 26개 중 다음 4개는 Codex의 `[skills].config`에서 비활성화하고 원본을 보관한다. 경로는 모두 `.codex/skills/` 아래다.

- 일반 설계·탐색: `adr`, `api-design`
- Claude 스킬 설계 참고: `skill-guide`
- 일반 SQL 지침: `sql-optimization-patterns`

나머지 22개는 GenOS·개인 vault·TIL·커밋 규칙·문서 변환·전용 도구 등 업무 지식과 자원을 제공한다. Codex 사본의 description을 짧게 정리하고 Obsidian 형식과 Excalidraw 예시는 필요할 때 읽는 references로 옮겼다. 재활성화가 필요하면 적용 조건·도구·버전·경로를 확인한 뒤 템플릿과 실제 설정의 해당 override만 변경한다.

Superpowers는 양쪽 모두 유지한다. Codex 쪽은 원격 설치본(`source: remote`)이라 버전을 고정할 수 없고 자동으로 upstream을 따른다. 설치·활성 상태와 현재 버전은 `codex plugin list --json`으로 확인한다. Claude는 `superpowers@superpowers-marketplace`(obra/superpowers-marketplace, upstream 추적)를 별도로 활성화한다. 공식 마켓플레이스(`claude-plugins-official`)는 커밋 sha를 고정해 upstream보다 뒤처지므로 2026-09-22에 전환했다. Astra 정리는 Superpowers를 제거하는 조건이 아니다.

## 스킬 유지 기준

스킬의 원칙·컨벤션·버전 의존 지침·업무 자원을 구분한다. 한 스킬에 여러 성격이 섞일 수 있으며, 안정적인 원칙이 있어도 실행 명령과 환경은 재확인한다. 분류 예시는 [CLAUDE.md의 Skills 절](../CLAUDE.md#skills)을 참고한다.

유지·삭제는 변화 속도가 아니라 고유한 규칙·실패 기록·재사용 자원과 실제 사용 필요성으로 판단한다. `find-docs`·`project-overview`는 일반 도구 설명·탐색 절차와 중복돼 제거했다. 먼저 삭제한 Java/Spring/JPA/Python 스킬 9개도 복원하지 않는다.

공통 스킬을 정리할 때는 양쪽 영향을 확인한다. 도구별 스킬을 같은 목록으로 강제하거나 Claude 설정을 Codex에 그대로 적용하지 않는다. 실제 앱 설정은 삭제한 스킬 override 등 필요한 항목만 정리한다.

## 훅과 유지보수

Codex는 `pre-commit-gate.sh`, `block-rm.sh`, `file-dispatcher.sh` 세 훅을 등록한다. Ruff 기본값 1, env 파일 검사 0, secret 패턴 검사 0은 기존 선택을 유지한다. 민감한 키 파일 검사는 계속 항상 켜져 있다. 기본값은 `config/hook-settings.sh`에서 관리하며 명시적인 `CODEX_ENABLE_*` 환경 변수가 우선한다. Claude의 `ENABLE_*` 값을 바꿔도 Codex 검사에는 영향을 주지 않는다.

중복 문맥·프롬프트 재작성·자동 링크·자동 다중 모델 리뷰를 수행하던 Codex의 `session-context.sh`, `link-skills.sh`, `prompt-rewriter.sh`, `til-review.sh`, `vault-linker.sh`는 등록과 복제본을 제거했다. Claude 훅은 유지한다. 제거한 Codex 훅은 Git 이력에서 복원할 수 있다.

Codex 개인 스킬은 `.codex/skills/<name>/`에서 수정하거나 추가한다. 디렉터리 링크이므로 별도 Claude 동기화가 필요 없다. 스크립트의 로컬 의존성·캐시는 각 도구의 스킬 디렉터리에서 관리한다.

## 적용과 검증 범위

변경 후 새 Codex 세션을 시작한다. 현재 대화에 이미 들어온 지침·스킬 목록은 소급해서 바뀌지 않는다. 앱에서 이전 목록이 계속 보이면 앱을 다시 실행한다.

검증 대상은 실제 링크, 도구별 정본·활성 상태 보존, TOML/JSON 파싱, strict doctor, CLI 프롬프트의 스킬 경로와 비활성 처리, 유지한 훅의 동작 및 pre-commit 검사다. `install.sh` 전체 실행은 패키지와 다른 앱 설정까지 바꾸므로 수행하지 않는다. 실제 작업 속도·정답률·토큰 비용 개선은 별도 측정이 필요하다.

설정 형식은 [Codex skills](https://developers.openai.com/codex/skills)와 [configuration reference](https://developers.openai.com/codex/config-reference)를 따른다.
