# Global Instructions

## 협업 방식
나와 일하는 법(작업 워크플로우·자율성·응답 스타일)은 별도 문서에 명세한다. 모든 작업에서 따른다.

@docs/working-style.md

## 웹 검색
도구 라우팅·최신성 규칙은 `rules/web-search.md`를 따른다 (자동 로드됨).

## 문서화
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

## OMC 오케스트레이션 레이어
oh-my-claudecode(OMC)의 상시 오케스트레이션 지침을 모든 세션에 적용한다. 위 사용자 지침이 항상 우선한다.
아래 파일은 머신 로컬 산출물(dotfiles 미추적)이며, 새 머신에서는 `/oh-my-claudecode:omc-setup`으로 재생성된다. 없으면 이 import는 무시된다.

@~/.claude/CLAUDE-omc.md
