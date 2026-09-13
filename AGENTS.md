# Dotfiles 작업 규칙

## 원본과 실행 상태

- 설정 원본은 `~/.dotfiles/`에 있다. 홈의 symlink 대신 이 저장소의 원본을 수정한다.
- `~/.gitconfig`는 `git/.gitconfig`를 include하는 로컬 stub이다. Codex의 `~/.codex/config.toml`은 앱이 관리하는 실행 상태이며, 지속할 기본 설정은 `.codex/config.toml.example`에도 반영한다. 인증·프로젝트 신뢰·앱 상태를 템플릿으로 덮어쓰지 않는다.
- `install.sh`가 링크와 최초 설치를 관리한다. Codex 협업 지침은 `.codex/AGENTS.md`, Claude/Gemini는 `.claude/docs/working-style.md`가 정본이다.
- cmux는 Codex의 `.codex/config/global.json`에 훅을 합칠 수 있다. Gemini의 `~/.gemini/config/hooks.json`은 `merge_hooks_json`을 유지한다. `link_file`로 바꾸면 호스트별 훅이 덮어써질 수 있다.

## 작업별 위치

- Shell: `zsh/aliases.zsh`, `zsh/functions.zsh`, `zsh/path.zsh`. 로그인 시 PATH는 `.zprofile`, 비대화형 SSH PATH는 `.zshenv`를 확인한다.
- 앱 설정: `.config/`. Git 설정: `git/`. 설치 패키지: `Brewfile`, `Brewfile.cask`.
- Codex 구성과 비활성 스킬의 이유는 [.codex/README.md](.codex/README.md)에 있다. 설정·스킬 구성을 바꿀 때 참고한다.
- 터미널·Claude 플러그인·훅 문제는 [운영 메모](.codex/docs/dotfiles-operations.md)의 해당 항목을 참고한다.

## 검증과 훅

- 수정한 Shell 파일마다 `zsh -n <파일>` 또는 `bash -n <파일>`로 문법을 확인한다. 셸 동작을 바꿨으면 실제 reload도 확인한다.
- PR/merge 전에는 `pre-commit run --all-files`가 필요하다. 일반 수정은 영향을 받는 검증을 수행한다.
- Codex 훅은 커밋 보호(`pre-commit-gate.sh`, `block-rm.sh`)와 Python/Ruff(`file-dispatcher.sh`)를 담당한다. Codex의 `CODEX_ENABLE_*` 설정은 `.codex/config/hook-settings.sh`, Claude의 `ENABLE_*` 설정은 `zsh/path.zsh`에서 관리한다.
- 훅이 실제 위반을 보고하면 해당 내용을 수정한다. 작업을 통과시키려고 훅이나 `ENABLE_*` 설정을 우회하지 않는다.

## 커밋

- Conventional Commits: `type(scope): subject`. 개인·회사 작업은 한국어 명령형, 마침표·emoji 없음. 저장소별 규칙이 있으면 따른다.
- 합의한 파일만 명시적으로 stage한다. PR에는 변경 이유·영향 경로·검증 결과를 적는다.
- 실제 비밀값과 `.env`는 커밋하지 않는다. `.env.local.example`을 사용한다.
