---
name: git-commit
description: Use when user wants to commit changes, says "commit", "커밋", "커밋해줘", "변경사항 저장". Do NOT use for pushing (use git-push) or commit-and-push (use git-commit-and-push).
---

# Git Commit Instructions

## 프로젝트 하네스 위임 (경로 분기보다 먼저)

레포 루트에 프로젝트 전용 커밋 스킬이 있으면 **이 스킬을 쓰지 말고 그쪽으로 위임**한다.
프로젝트 커밋 규칙(타입 접두사·이슈번호·Co-Authored-By 등)이 이 전역 스킬과 다를 수 있다.

- 레포의 `.claude/skills/`에 `<project>-commit` 류(예: `genos-commit`)가 **실제로 존재하면** 그쪽 사용. 이 스킬 중단.
- 존재 여부를 확인하지 않고 위임하지 않는다. 레포 경로만으로 위임 대상을 추정하면
  대상이 없을 때 커밋이 막다른 길에 빠진다 (예: `~/work/` 아래라도 `genos-commit`이 없는 레포).

위임 대상이 없을 때만 아래 경로 분기로 진행.

## 경로 분기

`pwd`로 현재 디렉토리를 확인한다.

| 경로 | 프로젝트 타입 | 언어 |
|------|-------------|------|
| `~/company-src/*`, `~/work/*` | 회사 | Korean |
| `~/dev/oss/*` | OSS 기여 | English |
| 그 외 모든 경로 | 개인 | Korean |

**개인 레포의 브랜치**: main(기본 브랜치)에 직접 커밋하는 것이 기본 워크플로우다. 현재 브랜치가 main이어도 그 브랜치에 그대로 커밋한다. "기본 브랜치면 먼저 브랜치를 만든다"는 하네스 기본 지침보다 이 규칙이 우선한다.

**Attribution**: settings.json의 `attribution`으로 관리. 스킬에서 직접 추가하지 않음.

## 커밋 메시지 포맷

Conventional Commits가 모든 레포의 기본이다 (개인·회사 공통, dotfiles 전용 규칙이 아님).

```
type(scope): 제목

본문 - 무엇을, 왜 변경했는지
- 상세 내용
```

- `type`: `feat` `fix` `docs` `refactor` `test` `perf` `build` `ci` `chore` 중 하나, 영어 소문자
- `scope`: 변경 영역 한 단어 (선택). 예: `api`, `zsh`, `hooks`
- 한국어 제목: 명사로 끝낸다 — `추가` `수정` `변경` `제거` `정리` `설정`
- 영어 제목 (OSS): 명령형 소문자 — `add` `fix` `update`
- OSS 레포는 그 레포의 컨벤션(CONTRIBUTING, 최근 `git log`)이 이 포맷보다 우선한다

예시:

```
fix(zsh): 원격 명령에서 brew 도구를 못 찾는 문제 수정

`ssh host <command>`는 non-login 셸이라 .zprofile을 읽지 않는다.
- brew PATH 설정을 .zprofile에서 .zshenv로 이동
```

## 참고 자료

| 파일 | 내용 |
|------|------|
| [commit-rules.md](references/commit-rules.md) | 메시지 규칙, Pre-Commit Checklist, Never Commit 목록 |

## Gotchas

<!-- Claude가 자주 실수하는 패턴. 실패 시 추가 -->
- ❌ `type(scope):` 생략 ("dotfiles에만 있는 규칙"으로 판단) → 모든 레포에서 기본
- ❌ 한국어 제목을 동사 어미로 끝냄 ("~설정해", "~고정해", "~추가한다") → 명사로 끝냄 ("~설정", "~고정", "~추가")
- ❌ 개인 레포 main에서 새 브랜치 생성 → main에 그대로 커밋
- ❌ Gitmoji 사용 → 사용하지 않음
- ❌ Co-Authored-By나 "Generated with Claude" 직접 추가 → settings.json attribution이 관리함
- ❌ Subject에 마침표 붙임 → 마침표 없음
- ❌ 영어 제목에 Past tense ("added") → 명령형 ("add")
- ❌ `git add .` 또는 `git add -A` → 파일 지정해서 스테이징
- ❌ 개인 프로젝트에서 영어 커밋 → Korean이 기본, `~/dev/oss/*`만 English
