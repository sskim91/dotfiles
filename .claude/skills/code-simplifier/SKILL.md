---
name: code-simplifier
description: 코드 리뷰 및 개선 제안. 최근 커밋, 현재 세션 작업, staged 파일 중 선택하여 리뷰.
user_invocable: true
---

# Code Simplifier

코드의 명확성, 일관성, 유지보수성을 개선하는 리팩토링 스킬입니다.

## 사용법

```
/code-simplifier              # 대화형으로 범위 선택
/code-simplifier <file_path>  # 특정 파일 리뷰 (바로 진행)
```

## Instructions

### Step 1: 범위 선택

파일 경로가 인자로 주어지면 Step 2로 바로 진행합니다.

인자가 없으면 **AskUserQuestion**으로 리뷰 범위를 확인합니다:

```
header: "Scope"
question: "어떤 코드를 리뷰할까요?"
options:
  - label: "최근 커밋"
    description: "가장 최근 커밋의 변경사항 분석"
  - label: "현재 세션 작업"
    description: "이번 대화에서 수정한 파일들"
  - label: "Staged 파일"
    description: "git status의 staged 파일들"
```

**사용자가 Other를 선택하면** 직접 파일/디렉토리 경로를 입력받습니다.

### Step 2: 코드 수집

선택된 범위에 따라 코드를 수집합니다:

| 범위 | 수집 방법 |
|------|-----------|
| 최근 커밋 | `git show --stat HEAD` + `git diff HEAD~1` |
| 현재 세션 작업 | 대화 중 Edit/Write한 파일 목록 |
| Staged 파일 | `git diff --cached` |
| 직접 지정 | 해당 경로의 파일 읽기 |

### Step 3: Agent 호출

Task 도구로 `code-simplifier:code-simplifier` agent를 호출합니다.

```
Task(
  subagent_type: "code-simplifier:code-simplifier",
  description: "코드 리뷰",
  prompt: "다음 코드를 리뷰해주세요. 언어와 프레임워크에 맞는 best practice 기준으로 검토하고, 발견된 문제를 심각도 순으로 정리해주세요.

[수집된 코드/diff 내용]"
)
```

## 리뷰 카테고리

Agent가 자동으로 언어/프레임워크를 감지하고 아래 카테고리로 리뷰합니다:

1. **Critical Issues** - 보안 취약점, 리소스 누수, 동시성 버그
2. **Potential Bugs** - 예외 처리 누락, 타입 오류 가능성
3. **Performance** - N+1 쿼리, 비효율적 루프
4. **Code Hygiene** - Dead code, magic numbers, 네이밍
5. **Design** - SOLID 위반, 과도한 추상화

## 출력 형식

```markdown
## 리뷰 결과

### Critical (즉시 수정)
- [파일:라인] 문제 설명 + 수정 제안

### High Priority
- ...

### Medium Priority
- ...

### Suggestions
- ...
```

## 주의사항

- 리팩토링 시 기존 동작 보존
- 테스트가 있다면 테스트 통과 확인
- 점진적 개선 권장
