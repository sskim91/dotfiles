---
name: devlog
description: Record development work logs to _devlog/YYYY-MM-DD-topic.md tracking commands, decisions, and next steps. Use when user says "devlog", "작업 로그", "work log", "오늘 작업 기록", or wants to document development progress. Supports /devlog, /devlog [title], and /devlog --summary. Do NOT use for git commits (use git-commit skill), session handoff (use session-handoff skill), or TIL documents (use til skill).
---

# /devlog - 작업 로그 기록

개발 작업 내용을 devlog 파일에 기록합니다. Git 커밋 여부와 관계없이 작업 내용을 남길 수 있습니다.

## 실행 방법

1. **현재 상태 파악**
   - Git 사용 가능 여부 확인 (`git rev-parse --git-dir 2>/dev/null`)
   - Git 있으면: `git status --short` 결과 참고
   - Git 없으면: 수동 입력 모드

2. **주제(topic) 결정**
   - `/devlog 제목` 으로 실행했으면 제목에서 주제 추출
   - `/devlog` 만 실행했으면 사용자에게 "어떤 작업을 하셨나요?" 질문
   - `/devlog --summary` 면 대화 컨텍스트에서 주제 자동 추출
   - 주제는 영문 kebab-case로 변환 (예: "Docker 환경 구축" → `docker-setup`)
   - 한글/영문 혼합 시 영문 키워드 중심으로 변환

3. **devlog 파일 생성/업데이트**
   - 프로젝트 루트: Git repo면 `git rev-parse --show-toplevel`, 아니면 `$PWD`
   - 경로: `{project-root}/_devlog/YYYY-MM-DD-{topic}.md`
   - _devlog 폴더가 없으면 생성
   - 같은 날짜 + 같은 주제 파일이 있으면 해당 파일에 append
   - 순번 결정: 파일 내 마지막 `## N.` 헤더를 찾아 N+1 사용 (새 파일이면 1)

## 파일명 규칙

```
_devlog/
├── 2026-03-05-redis-config.md
├── 2026-03-05-intent-refactor.md
├── 2026-03-04-session-pipeline.md
└── 2026-03-03-docker-setup.md
```

- 형식: `YYYY-MM-DD-{topic}.md`
- topic: 영문 kebab-case, 간결하게 (2~4 단어)
- 같은 날 다른 주제면 별도 파일 생성
- 같은 날 같은 주제면 기존 파일에 순번 증가하며 append

### 주제 변환 예시

| 사용자 입력 | topic | 파일명 |
|-------------|-------|--------|
| Docker 환경 구축 완료 | docker-setup | 2026-03-05-docker-setup.md |
| Redis 설정 변경 | redis-config | 2026-03-05-redis-config.md |
| intent 리팩토링 | intent-refactor | 2026-03-05-intent-refactor.md |
| API 테스트 가이드 작성 | api-test-guide | 2026-03-05-api-test-guide.md |
| 버그 수정 - 세션 타임아웃 | fix-session-timeout | 2026-03-05-fix-session-timeout.md |

## 로그 형식

```markdown
## N. 작업 제목

### 작업 내용
- 수행한 작업 요약

### 실행한 명령어
```bash
# 주요 명령어 (나중에 복붙 가능하도록)
docker-compose up -d
curl -X POST ...
```

### 확인 결과
| 항목 | 상태 |
|------|------|
| 빌드 성공 | ✅ |
| 테스트 통과 | ✅ |
| API 응답 확인 | ✅ |

### 주요 결정사항
- 왜 이렇게 했는지

### 생성/변경된 파일
- `path/to/file.md`

### 다음 단계
- [ ] TODO 1
- [ ] TODO 2

---
```

## 상세 수준 가이드

**포함할 것:**
- 주요 명령어 (나중에 따라할 수 있도록)
- 핵심 결과 (테이블 형태로 간결하게)
- 결정 사항과 이유
- 다음 단계

**생략할 것:**
- 전체 출력 로그 (너무 길면)
- 시행착오 과정 (최종 성공한 것만)
- 자명한 내용

## 순번 규칙

- 시간 대신 순번 사용: `## 1.`, `## 2.`, `## 3.` ...
- 같은 파일(같은 날 + 같은 주제) 내에서 순번 증가
- 새 파일은 항상 1번부터

## 사용 예시

```bash
# 대화형으로 로그 작성 (주제 질문함)
/devlog

# 제목과 함께 바로 작성
/devlog Docker 환경 구축 완료

# 현재 세션 작업 전체 요약
/devlog --summary
```

## 자동 요약 모드 (`--summary`)

`/devlog --summary` 실행 시 현재 세션의 작업을 자동으로 요약:

1. **작업 내용 자동 추출**
   - 대화에서 수행한 작업 식별
   - 파일 생성/수정 내역 수집
   - 주요 결정사항 추출
   - 주제(topic) 자동 결정

2. **실행한 명령어 수집**
   - Bash 도구로 실행한 명령어 목록화
   - 재현 가능한 형태로 정리

3. **결과 요약**
   - 성공/실패 여부
   - 확인된 동작

4. **사용자 확인 후 저장**
   - 요약 내용 미리보기 제공
   - 파일명(주제) 확인/수정 요청 가능
   - 확인 후 파일에 저장

### `--summary` 출력 예시

```markdown
## 1. prompts.chat MCP 서버 통합

### 작업 내용
- prompts.chat MCP 서버를 Claude Code에 remote HTTP 방식으로 등록
- setup-mcp.sh에 자동 등록 스크립트 추가
- 새 세션에서 MCP 도구 10개 정상 동작 확인

### 실행한 명령어
```bash
claude mcp add -s user -t http prompts-chat https://prompts.chat/api/mcp
```

### 확인 결과
| 항목 | 상태 |
|------|------|
| MCP 서버 등록 | ✅ |
| search_prompts 동작 | ✅ |
| search_skills 동작 | ✅ |

### 주요 결정사항
- Local(npx) 대신 Remote HTTP 선택: 설치 불필요, 항상 최신 프롬프트

### 생성/변경된 파일
- `.claude/setup-mcp.sh`

### 다음 단계
- [ ] 유용한 프롬프트 탐색 및 스킬 활용

---
```

## Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `_devlog` 폴더 생성 실패 | 프로젝트 루트 감지 실패 | `git rev-parse --show-toplevel` 확인, Git 없으면 `$PWD` 사용 |
| 같은 파일에 append 안 됨 | 날짜 또는 topic 불일치 | 기존 파일명의 topic과 정확히 동일한지 확인 |
| 순번이 1로 리셋됨 | 새 파일로 생성됨 | 같은 날짜 + 같은 topic인지 파일명 확인 |
| `--summary`가 빈 내용 생성 | 세션에서 작업이 거의 없음 | 수동 모드(`/devlog 제목`)로 전환 |
