---
name: session-handoff
description: Generate comprehensive session summary for handoff to new LLM session. Use when user says "session handoff", "세션 인계", "세션 정리", "handoff", "다음 세션에 넘겨줘", or when ending a session and needing to preserve full context for continuation. Do NOT use for learning summaries (use learning-tracker skill), TIL documents (use til skill), or development work logs (use devlog skill).
---

# Session Handoff - 대화 세션 인계 요약본 생성

## 목표

현재 세션의 모든 내용을 극도로 상세하게 요약하여, 새 LLM 세션에서 완벽하게 맥락을 이어받을 수 있도록 합니다.

## 실행 단계

### 1단계: 슬러그 결정
세션 핵심 주제를 영문 kebab-case 슬러그로 요약 (2~4단어). 사용자에게 제안 후 확인. `_session/{topic-slug}.md` 기존 파일 있으면 읽어서 이전 맥락 파악.

### 2단계: 상세 요약 생성
기존 핸드오프가 있으면 이전 맥락을 흡수하여 통합 작성. 아래 9개 섹션 구조를 따라 극도로 상세하게 작성 (상세는 references 참조).

**섹션 목록:**
- I. 빠른 시작 가이드 (Quick Start) — 반드시 최상단
- II. 근본적인 목표 및 초기 설정
- III. 상세한 대화 전개 과정
- IV. 공유된 중요 정보 및 배경 맥락
- V. 시도한 접근법과 결과 (CRITICAL)
- VI. 중간 결론, 합의, 잠정적 성과
- VII. 대화 중단 시점의 정확한 상태
- VIII. 남은 계획 및 다음 단계 (CRITICAL)
- IX. 핵심 개념, 용어, 반복된 패턴

### 3단계: 파일 저장 + Clipboard 복사
`_session/` 폴더 확인/생성 → Write tool로 저장 → `cat _session/{topic-slug}.md | pbcopy`

### 4단계: 사용자 안내
저장 경로 + "Clipboard에 복사되었습니다" + 새 세션 사용법 안내.

## 핵심 원칙

- **자립성**: 이 파일 하나만으로 다음 에이전트가 바로 작업 이어받기 가능. 맥락 독립적
- **상세성**: 정보 누락 금지. "답변했다"가 아니라 "어떤 답변을 했는지". 코드 스니펫 포함
- **Rolling 통합**: 최근 2세션 상세 유지, 이전은 핵심만 압축. 실패한 것들/핵심 파일/남은 계획은 항상 유지
- **한국어** 작성

## References

| 파일 | 내용 |
|------|------|
| `references/section-template.md` | I~IX 전체 섹션 상세 구조 (25개 항목) |

## Gotchas

- **추상적 기술**: "리팩토링했다"로 끝내지 말고 구체적 변경사항, 파일, 코드 포함
- **실패 접근법 누락**: Section V의 "What Didn't Work"는 다음 에이전트가 같은 실수 반복 방지에 핵심
- **기존 파일 무시**: `_session/{slug}.md` 기존 파일이 있으면 반드시 읽고 통합. 덮어쓰기만 하면 이전 맥락 유실
