# Skills

개인 스킬의 분류·재검토 기준·작성 규약·삭제 이력. 복원 금지 원칙과 Codex 스킬 독립성은 루트 `CLAUDE.md`에 있다.

## 분류와 재검토 시점

스킬은 아래 성격을 함께 가질 수 있다. **변화 속도는 재검토 기준이고, 유지·삭제는 고유한 가치와 사용 필요성으로 판단한다.** 원칙이 안정적이어도 도구·버전·경로·현재 업무 규칙은 재확인한다.

| 내용 구분 | 예시 | 재검토 시점 |
|---|---|---|
| 개인·팀 컨벤션 | `git-commit`·`git-push`·`git-commit-and-push`, `session-handoff`의 형식·범위 | 사용자·팀·프로젝트 합의가 바뀔 때 |
| 버전·환경 의존 지침 | `ast-grep`, `skill-guide`, `cc-changelog-review`, `translate-article` | 도구·API·실행 환경이 바뀔 때 |
| 업무 절차·자원 | `excalidraw-diagram`, `obsidian-note`, `til`, `til-tagger`, `vault-linter`, `genos-knowledge-capture`, `write-genos-patch-notes`, `bookscan-check` | 업무 흐름·저장 위치·산출물 형식이 바뀔 때 |

일반 지식·도구 설명의 중복은 줄이고, 사용자의 선택·실제 실패 기록·진단 스크립트·템플릿은 필요성에 따라 남긴다. 버전별 사용법은 대상 프로젝트 버전을 확인한 뒤 공식 문서·실제 코드와 대조한다.

## 활성 상태

비활성 스킬은 `.claude/settings.json`의 `skillOverrides`에 `"off"`로 둔다. 디렉터리는 남아 있어 다시 켜기만 하면 된다. 꺼진 채 쓰이지 않는 스킬은 산출물·다른 스킬의 참조를 확인한 뒤 삭제한다. `til-tagger`는 꺼져 있어도 `til`이 그 `SKILL.md`를 직접 읽으므로 삭제 대상이 아니다.

## 삭제 이력

2026-09에 비활성 Java/Spring/JPA/Python 스킬 9개를 제거했고, 일반 탐색·도구 설명과 중복되는 `project-overview`·`find-docs`도 제거했다. 삭제한 스킬은 복원하지 않는다. 새 필요가 생기면 프로젝트 제약은 해당 프로젝트에 기록하고, 공통 스킬은 실제 재사용 가치가 있을 때 별도로 검토한다.

2026-10-17에 꺼져 있던 9개를 제거했다. 일반 지식이라 모델이 이미 아는 `adr`·`api-design`·`sql-optimization-patterns`·`github-actions`, 산출물이 없던 `devlog`·`youtube-summarizer`·`tech-blog-writer`·`sns-writer`, Codex 사본과 중복인 `codex-changelog-review`다. `adr`·`api-design`·`sql-optimization-patterns`는 Codex에서도 꺼져 있어 Codex 사본도 함께 제거했다. 나머지 Codex 사본은 그대로 둔다.

`.claude/skills/`와 `.codex/skills/`는 독립된 정본이다. 공통으로 관리하는 스킬은 양쪽 영향을 확인하되 도구별 description·활성 상태·실행 지침을 보존한다. 한쪽에만 필요한 스킬의 추가·삭제를 다른 쪽에 강제하지 않는다. Codex 구성은 [.codex/README.md](../../.codex/README.md)를 참고한다.

## 작성 규약

- `SKILL.md` frontmatter의 `description`은 English, single-line. "Use when..." trigger hint를 포함한다.
- Claude·Codex 겸용 Skill은 선택적으로 `agents/openai.yaml`을 포함한다. Claude Code는 이 파일을 무시하고, Codex는 Skill 목록과 호출 UI의 metadata로 사용한다.
- 새 스킬 디렉터리는 SessionStart의 `link-skills.sh`가 다음 세션에 `~/.claude/skills/`로 자동 링크한다. 삭제 시에는 링크를 직접 정리한다 (add-only).
