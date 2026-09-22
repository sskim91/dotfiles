# Global Instructions

## 협업 방식
나와 일하는 법(작업 워크플로우·자율성·응답 스타일)은 별도 문서에 명세한다. 모든 작업에서 따른다.

@docs/working-style.md

## 웹 검색
도구 라우팅·최신성 규칙은 `rules/web-search.md`를 따른다 (자동 로드됨).

## 문서화
- 제목·본문에 장식 기호를 붙이지 않는다. 섹션은 마크다운 헤딩(`##`)과 목록 기호(`-`)만으로 구분하라. 특히 `§`(section sign)은 사용자가 명시적으로 요청한 경우에만 쓴다.
```
❌ Bad: 장식 기호 삽입
## § 1. 설치
### §1.2 의존성

✅ Good: 순수 마크다운
## 1. 설치
### 1.2 의존성
```
- ASCII 박스를 반드시 사용해야 하는 경우: 박스 내부 텍스트는 영어만 사용하라. 한글과 영문의 고정폭(monospace) 너비가 달라서 정렬이 깨진다.
```
❌ Bad: 한글 포함 (정렬 깨짐)
┌─────────────────────────────────┐
│ Name: My App Docker             │
│ Bind mounts: ./src:/app (핫 리로드)  │  ← 깨짐
└─────────────────────────────────┘

✅ Good: 영어만 사용
┌─────────────────────────────────────────┐
│ Name: My App Docker                     │
│ Bind mounts: ./src:/app (Hot Reload)    │
└─────────────────────────────────────────┘
```

## 기본 프로세스: superpowers
superpowers 플러그인의 스킬이 모든 작업의 기본 프로세스 레이어다. 답변·조사·계획을 시작하기 전에 해당 스킬을 먼저 호출하고 그 절차를 따른다. 다른 플러그인이나 기본 동작은 superpowers 스킬이 다루지 않는 영역에만 쓴다.
- 기능 추가·동작 변경·새 구성 요소: `superpowers:brainstorming` → `superpowers:writing-plans` → 실행(`subagent-driven-development` 또는 `executing-plans`).
- 버그·테스트 실패·예상 밖 동작: 수정안을 내기 전에 `superpowers:systematic-debugging`.
- 구현 중: `superpowers:test-driven-development`. 완료를 선언하기 전: `superpowers:verification-before-completion`.
- 리뷰: 작업 단위가 끝나면 `superpowers:requesting-code-review`, 피드백을 받으면 `superpowers:receiving-code-review`.
- brainstorming 면제 범위는 working-style.md 2절의 "자명한 변경"(오타·주석, alias/함수 1개, 단일 파일 소규모 수정)과 읽기 전용 조사·질문에 한정한다. 그 외는 작아 보여도 건너뛰지 않는다.
- working-style.md의 "비자명한 변경은 Plan 승인 후 실행"은 brainstorming과 writing-plans의 산출물로 충족한다. 별도 Plan 형식을 이중으로 만들지 않는다.
