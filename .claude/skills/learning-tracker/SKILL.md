---
name: learning-tracker
description: Use when user says "learning summary", "what I learned today", "오늘 뭐 배웠지", "session summary", "학습 정리", or wants to extract learnings from current session. Do NOT use for session handoff (use session-handoff), development work logs (use devlog), or direct TIL/note creation (use til or obsidian-note).
---

# Learning Tracker

현재 대화에서 확인한 기술 지식과 남은 질문을 추출한다. 학습 요약을 제공하고, 저장 요청이 있으면 `til`에 전달한다.

## 추출 기준

- 사용자가 지정한 주제·기간을 우선한다. 대화의 설명, 코드, 실행 결과와 질문에서 재사용할 내용을 고른다.
- 직접 확인한 사실, 코드·자료에서 도출한 해석, 미확인 추정을 구분한다.
- 사용자가 이해했다고 말하지 않았다면 이해 완료로 단정하지 않는다. 대화에서 다룬 내용으로 표현한다.
- 실행하지 않은 예제는 실행 검증된 것으로 표시하지 않는다. 비밀값·인증정보는 제외한다.

## 요약 형식

주제마다 필요한 항목을 채운다. 카테고리는 전달용 제안이며 실제 분류·파일 형식은 `til`의 현재 규칙을 따른다.

```markdown
## 주제

- 한 줄 요약:
- 배경: 어떤 문제나 질문에서 시작했는가
- 핵심 내용:
- 근거: 대화의 실행 결과, 파일 위치, 확인한 문서
- 코드·명령 예시: 실제 실행 여부를 함께 표시
- 남은 질문·미확인 사항:
- 제안 카테고리:
```

## 저장 경계

- 학습 요약만 요청받으면 대화에 결과를 제공한다.
- TIL 저장까지 요청받았으면 이미 받은 요청에 따라 `til`로 전달한다. 저장 의사가 없다면 저장 여부를 제안할 수 있다.
- `til`이 없으면 임의의 경로·양식으로 저장하지 않고 요약과 미완료 범위를 알린다.
- 이 스킬은 직접 파일을 저장하지 않는다. 파일명·경로·Git 작업 규칙은 저장 스킬과 사용자 요청을 따른다.

작업 결과 기록은 `devlog`, 다음 세션의 작업 재개 문서는 `session-handoff`의 범위다.
