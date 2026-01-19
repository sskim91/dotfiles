---
name: gemini-fetch
description: WebFetch 차단 사이트 우회. Reddit, LinkedIn, X 등 403/차단 에러 시 Gemini CLI로 콘텐츠 가져오기. (user)
---

# Gemini Fetch - WebFetch 차단 우회

WebFetch가 차단된 사이트(403, blocked, JavaScript 필요 등)에서 Gemini CLI를 통해 콘텐츠를 가져옵니다.

## 지원 사이트

- Reddit (reddit.com)
- LinkedIn (linkedin.com)
- X (x.com, twitter.com)
- Medium (medium.com) - 페이월/멤버십 글
- Quora (quora.com)
- Facebook (facebook.com)
- Instagram (instagram.com)
- Glassdoor (glassdoor.com) - 회사 리뷰
- 뉴스 사이트 (paywall 있는 경우)
- 기타 WebFetch 차단 사이트

## 사용 방법

고유한 세션 이름을 선택하고 (예: `gemini_abc123`) 일관되게 사용하세요.

### 1. 세션 시작

```bash
tmux new-session -d -s <session_name> -x 200 -y 50
tmux send-keys -t <session_name> 'gemini' Enter
sleep 3  # Gemini CLI 로딩 대기
```

### 2. 쿼리 전송 및 출력 캡처

```bash
tmux send-keys -t <session_name> 'Fetch content from <URL>: <your query>' Enter
sleep 30  # 응답 대기 (복잡한 검색은 최대 90초)
tmux capture-pane -t <session_name> -p -S -500  # 출력 캡처
```

### 3. Enter 전송 여부 확인

**쿼리 텍스트 위치**를 확인하세요:

**Enter 미전송** - 쿼리가 박스 **안에** 있음:
```
╭─────────────────────────────────────╮
│ > Your query text here               │
╰─────────────────────────────────────╯
```

**Enter 전송됨** - 쿼리가 박스 **밖에** 있고 처리 중:
```
> Your query text here

⠋ Our hamsters are working... (processing)

╭────────────────────────────────────────────╮
│ >   Type your message or @path/to/file     │
╰────────────────────────────────────────────╯
```

빈 프롬프트 `Type your message or @path/to/file`는 정상입니다. 중요한 것은 **당신의 쿼리 텍스트**가 박스 안인지 밖인지입니다.

쿼리가 박스 안에 있으면 Enter 재전송:
```bash
tmux send-keys -t <session_name> Enter
```

### 4. 세션 정리

```bash
tmux kill-session -t <session_name>
```

## 쿼리 예시

```bash
# Reddit
tmux send-keys -t gemini_session 'Summarize the top posts from r/programming about Claude Code' Enter

# LinkedIn
tmux send-keys -t gemini_session 'What are the key points from this LinkedIn article: <url>' Enter

# X (구 Twitter)
tmux send-keys -t gemini_session 'What is the discussion about in this X thread: <url>' Enter

# Medium
tmux send-keys -t gemini_session 'Summarize this Medium article: <url>' Enter

# Glassdoor
tmux send-keys -t gemini_session 'What are the reviews saying about <company> on Glassdoor?' Enter

# 일반 차단 사이트
tmux send-keys -t gemini_session 'Fetch and summarize the content from <blocked_url>' Enter
```

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| 응답 없음 | sleep 시간 늘리기 (최대 90초) |
| Enter 미전송 | `tmux send-keys -t <session> Enter` 재실행 |
| 세션 충돌 | 고유한 세션 이름 사용 |
| 출력 잘림 | `-S -1000`으로 더 많은 라인 캡처 |
