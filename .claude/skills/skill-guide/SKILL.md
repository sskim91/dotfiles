---
name: skill-guide
description: Use when user wants to create a new Skill, validate SKILL.md structure, or reference Anthropic skill design guide. Do NOT use for eval-based improvement or benchmark testing (use skill-creator plugin).
---

# Claude Skill Guide

Claude용 스킬을 작성·검토할 때 참고 자료를 찾고 적용 범위를 점검한다. 이 파일이 Codex에 있어도 검토 대상은 Claude 스킬이다. Codex 스킬 작성에는 해당 환경의 `skill-creator`를 사용한다.

## 먼저 확인할 것

- 대상이 Claude Code, Claude의 다른 제품, Codex 중 무엇인지 확인한다.
- 기존 폴더, 호출자, 참고 자료와 사용자의 요청 범위를 읽는다. 이름이 비슷하다는 이유만으로 다른 도구의 스킬을 함께 변경하지 않는다.
- 지원 frontmatter, 배치 위치, 도구 제한과 로딩 방식은 [Claude Code 공식 문서](https://code.claude.com/docs/en/skills)에서 대상 환경 기준으로 확인한다. 아래 로컬 자료는 작성 시점의 참고본이며 최신 명세를 대신하지 않는다.

## 내용 선택

- 사용자의 컨벤션, 재사용 자원, 실제로 확인된 실패 지점처럼 판단을 바꾸는 정보를 남긴다.
- `description`에는 호출할 상황과 필요한 경계를 적는다. 본문 작업 순서를 길게 요약하지 않는다.
- 본문에는 목적·적용 조건·중요한 규칙을 두고, 긴 참고 자료는 필요한 경우에만 읽도록 연결한다.
- 원칙, 프로젝트의 선택, 버전·환경에 의존하는 명령을 구분한다.
- 요청받은 조사·수정 범위를 지킨다. 참고 자료의 예시를 외부 쓰기·설치·공유·유료 실행에 대한 허가로 해석하지 않는다.

## 참고 자료 선택

| 자료 | 읽을 때 |
|---|---|
| [Anthropic 가이드 참고본](references/anthropic-skill-guide.md) | 설계 원칙과 워크플로우 구성을 검토할 때 |
| [실전 작성 팁](references/practical-tips.md) | 자원 배치·스킬 조합의 사례가 필요할 때 |
| [평가 절차 메모](references/eval-guide.md) | 사용자가 비교 평가를 요청하고 당시 도구·실행 방식이 현재도 유효한지 확인할 때 |

## 검증

- frontmatter 파싱, 상대 링크, 참조 자원과 호출자의 존재를 확인한다.
- description이 요청한 상황에 맞고, 기존 사용자 규칙과 충돌하지 않는지 확인한다.
- 명령·스크립트를 바꿨으면 승인된 환경에서 실제 동작을 확인한다. 행동 품질 비교가 필요하면 대표 요청으로 평가하고, 형식 검사와 행동 평가 결과를 구분해 보고한다.
