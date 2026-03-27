---
name: devlog
description: Use when user says "devlog", "작업 로그", "work log", "오늘 작업 기록". Supports /devlog, /devlog [title], /devlog --summary. Do NOT use for git commits (use git-commit), session handoff (use session-handoff), or TIL (use til).
---

# /devlog - 작업 로그 기록

개발 작업 내용을 devlog 파일에 기록합니다. Git 커밋 여부와 관계없이 작업 내용을 남길 수 있습니다.

## 사용법

- `/devlog` — 대화형 (주제 질문)
- `/devlog Docker 환경 구축 완료` — 제목과 함께 바로 작성
- `/devlog --summary` — 현재 세션 작업 전체 자동 요약

## 실행 방법

1. **현재 상태 파악**: Git 사용 가능 여부 확인. 있으면 `git status --short` 참고, 없으면 수동 입력
2. **주제(topic) 결정**: 사용자 입력 또는 대화 컨텍스트에서 추출. 영문 kebab-case 변환
3. **파일 생성/업데이트**: `{project-root}/_devlog/YYYY-MM-DD-{topic}.md`에 저장. 같은 날+주제 파일 있으면 append (순번 증가)

## 파일명 규칙

- 형식: `YYYY-MM-DD-{topic}.md`
- topic: 영문 kebab-case, 간결하게 (2~4 단어)
- 같은 날 다른 주제면 별도 파일 생성
- 같은 날 같은 주제면 기존 파일에 순번 증가하며 append

### 주제 변환 테이블

| 사용자 입력 | topic | 파일명 |
|-------------|-------|--------|
| Docker 환경 구축 완료 | docker-setup | 2026-03-05-docker-setup.md |
| Redis 설정 변경 | redis-config | 2026-03-05-redis-config.md |
| intent 리팩토링 | intent-refactor | 2026-03-05-intent-refactor.md |
| API 테스트 가이드 작성 | api-test-guide | 2026-03-05-api-test-guide.md |
| 버그 수정 - 세션 타임아웃 | fix-session-timeout | 2026-03-05-fix-session-timeout.md |

## References

| 파일 | 내용 |
|------|------|
| `references/log-format.md` | 로그 형식 템플릿, 상세 수준 가이드, 순번 규칙, --summary 상세/출력 예시, 사용 예시, Troubleshooting |

## Gotchas

- **같은 날 새 파일 생성**: 같은 날+같은 topic 파일이 있으면 새 파일 만들지 말고 기존 파일에 append. 순번만 증가
- **한글 topic**: topic은 반드시 영문 kebab-case. 한글/영문 혼합 시 영문 키워드 중심으로 변환
- **전체 로그 포함**: 전체 출력 로그, 시행착오 과정은 생략. 최종 성공한 것만 기록
