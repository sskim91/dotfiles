---
name: code-simplifier
description: Simplifies and refines code for clarity, consistency, and maintainability while preserving all functionality. Focuses on recently modified code unless instructed otherwise.
user_invocable: true
---

# Code Simplifier

코드의 명확성, 일관성, 유지보수성을 개선하는 리팩토링 스킬입니다.

## 사용법

```
/code-simplifier              # 대화형으로 언어/범위 선택
/code-simplifier <file_path>  # 특정 파일 리뷰
```

## Instructions

### Step 1: 언어 선택

**AskUserQuestion**으로 대상 언어를 확인합니다:

```
header: "Language"
question: "어떤 언어의 코드를 리뷰할까요?"
options:
  - label: "Java"
    description: "Spring, Enterprise Java 등"
  - label: "Python"
    description: "FastAPI, Django, 일반 Python 등"
```

### Step 2: 범위 선택

**AskUserQuestion**으로 리뷰 범위를 확인합니다:

```
header: "Scope"
question: "리뷰할 범위를 지정해주세요"
options:
  - label: "최근 수정된 파일"
    description: "git diff로 변경된 파일들"
  - label: "전체 프로젝트"
    description: "프로젝트 전체 스캔"
```

**사용자가 Other를 선택하면** 직접 패키지/모듈 경로를 입력받습니다.
- Java 예시: `com.example.service`, `src/main/java/com/example`
- Python 예시: `app/services`, `src/utils`

### Step 3: 리뷰 수행

Task 도구로 `code-simplifier` agent를 호출합니다. 언어에 따라 다른 프롬프트를 전달합니다.

---

## Java 리뷰 가이드라인

Java 프로젝트 리뷰 시 아래 항목을 순서대로 검토합니다:

### 1. Critical Issues (크리티컬 이슈)
- **NullPointerException 위험**: Optional 미사용, null 체크 누락
- **리소스 누수**: try-with-resources 미사용, 스트림/커넥션 미닫힘
- **동시성 버그**: 비동기 코드의 race condition, 잘못된 synchronized
- **보안 취약점**: SQL injection, XSS, 하드코딩된 credential
- **트랜잭션 문제**: 트랜잭션 경계 누락, 잘못된 propagation, 롤백 미처리

### 2. Potential Bugs (잠재적 버그)
- equals/hashCode 불일치
- 잘못된 예외 처리 (catch all, 빈 catch block)
- 무한 루프 가능성
- 잘못된 타입 캐스팅
- **Null 전파**: null을 반환하고 호출자가 처리 안 함
- **Deprecated API**: 프로젝트 Java 버전에서 deprecated된 API 사용 지양
- **에러 코드/상수 불일치**: 정의와 실제 사용처가 다른 경우
- **DTO 필드 누락**: 실제 사용되는 필드가 DTO/Entity에 정의 안 됨

### 3. Performance Issues (성능 문제)
- N+1 쿼리 문제
- 불필요한 객체 생성 (루프 내 new)
- 비효율적인 컬렉션 사용
- 불필요한 동기화
- **쿼리 최적화**: 인덱스 미사용, 풀스캔 쿼리

### 4. Over-Engineering (과도한 구현)
- 불필요한 추상화 레이어
- 과도한 디자인 패턴 적용
- 미래를 위한 불필요한 확장 포인트

### 5. Code Organization (코드 구조)
- **긴 메서드 분리**: 50줄 이상이면 분리 검토
- **긴 클래스 분리**: 500줄 이상이면 책임 분리 검토
- **God Object**: 너무 많은 책임을 가진 클래스

### 6. Reusability (재사용성)
- 중복 코드 추출
- 공통 유틸리티 함수화
- 상수 추출

### 7. Design Issues (설계 문제)
- SOLID 원칙 위반
- 순환 의존성
- 잘못된 계층 구조
- 응집도/결합도 문제

### 8. Code Hygiene (코드 위생)
- **Dead Code**: 사용되지 않는 메서드, 변수, import
- **주석 처리된 코드**: 삭제하고 git history 활용
- **Magic Numbers**: 의미 없는 숫자/문자열 상수화
- **네이밍**: 의도가 불명확한 변수명, 약어 남용
- **TODO/FIXME**: 오래된 TODO 정리, 실제 이슈로 전환
- **중복 import**: 같은 클래스를 여러 번 import
- **미사용 모듈**: 공통 라이브러리와 중복되는 로컬 클래스 (삭제 대상)
- **로거 불일치**: 프로젝트 내 `java.util.logging` vs `SLF4J` vs `Log4j` 혼용

### 9. Testability (테스트 용이성)
- **의존성 주입**: new로 직접 생성하는 의존성 → DI로 변경
- **Mocking 불가**: static 메서드 과다 사용, final 클래스
- **숨겨진 의존성**: 메서드 내부에서 외부 서비스 직접 호출

### 10. 로깅 및 모니터링
- **로그 레벨 적절성**: DEBUG/INFO/WARN/ERROR 구분
- **민감정보 로깅 금지**: 비밀번호, 토큰, 개인정보
- **추적 가능성**: 요청 ID, 사용자 ID 등 context 정보

---

## Python 리뷰 가이드라인

Python 프로젝트 리뷰 시 아래 항목을 순서대로 검토합니다:

### 0. 로깅 규칙 (Python 전용)
**중요**: 로그는 f-string 포맷팅을 그대로 유지합니다.

```python
# 이렇게 사용하는 것을 유지
logger.info(f"User {user_id} logged in")
logger.error(f"Failed to process {item}: {error}")

# lazy % formatting으로 변경하지 않음
# logger.info("User %s logged in", user_id)  # 이렇게 바꾸지 마세요
```

### 1. Critical Issues (크리티컬 이슈)
- **보안 취약점**: SQL injection, 하드코딩된 credential, pickle 보안
- **리소스 누수**: context manager 미사용, 파일/커넥션 미닫힘
- **동시성 버그**: async/await 오용, race condition
- **트랜잭션 문제**: DB 세션 관리 미흡, 커밋/롤백 누락

### 2. Potential Bugs (잠재적 버그)
- Mutable default argument (`def func(items=[])`)
- Late binding closure 문제
- 잘못된 예외 처리 (bare except, 빈 except)
- 타입 관련 런타임 에러 가능성
- **None 전파**: None 반환 후 호출자가 처리 안 함
- **타입 힌트 불일치**: 반환 타입이 실제와 다름, 시그니처 불일치 (`list` vs `Sequence`)
- **Deprecated API**: 프로젝트 Python 버전에서 deprecated된 API 사용 지양
- **에러 코드/상수 불일치**: 정의와 실제 사용처가 다른 경우
- **모델 필드 누락**: 실제 사용되는 필드가 Pydantic 모델에 정의 안 됨

### 3. Performance Issues (성능 문제)
- 비효율적인 루프 (리스트 컴프리헨션으로 대체 가능)
- 불필요한 리스트 생성 (제너레이터 사용 가능)
- N+1 쿼리 문제 (ORM 사용 시)
- 큰 데이터셋의 메모리 이슈
- **쿼리 최적화**: select_related/prefetch_related 미사용, 불필요한 쿼리

### 4. Over-Engineering (과도한 구현)
- 불필요한 클래스 (함수로 충분한 경우)
- 과도한 메타클래스/데코레이터 사용
- 불필요한 추상화

### 5. Code Organization (코드 구조)
- **긴 함수 분리**: 50줄 이상이면 분리 검토
- **긴 모듈 분리**: 500줄 이상이면 분리 검토
- 순환 import 문제

### 6. Reusability (재사용성)
- 중복 코드 추출
- 공통 유틸리티 함수화
- 상수/설정 추출

### 7. Design Issues (설계 문제)
- 단일 책임 원칙 위반
- 잘못된 모듈 구조
- 응집도/결합도 문제

### 8. Code Hygiene (코드 위생)
- **Dead Code**: 사용되지 않는 함수, 변수, import
- **주석 처리된 코드**: 삭제하고 git history 활용
- **Magic Numbers**: 의미 없는 숫자/문자열 상수화
- **네이밍**: 의도가 불명확한 변수명, 단일 문자 변수 (i, j, x 제외)
- **TODO/FIXME**: 오래된 TODO 정리
- **중복 import**: 같은 모듈을 여러 번 import (상단 + 함수 내부)
- **미사용 모듈**: 공통 라이브러리와 중복되는 로컬 모듈 (삭제 대상)

### 9. Testability (테스트 용이성)
- **의존성 주입**: 함수/클래스 내부에서 직접 생성하는 의존성
- **Mocking 불가**: 모듈 레벨 코드 실행, 하드코딩된 외부 호출
- **부작용 분리**: I/O와 비즈니스 로직 혼재

### 10. 로깅 및 모니터링
- **로그 레벨 적절성**: DEBUG/INFO/WARNING/ERROR 구분
- **민감정보 로깅 금지**: 비밀번호, 토큰, 개인정보
- **추적 가능성**: request_id, user_id 등 context 정보

---

## Step 4: Agent 호출

위 가이드라인을 포함하여 **Task 도구의 `code-simplifier` agent**를 호출합니다.

프롬프트 예시:
```
아래 가이드라인에 따라 [범위]의 [언어] 코드를 리뷰해주세요.

[언어별 가이드라인 전체 내용]

리뷰 후 발견된 문제를 심각도 순으로 정리하고,
각 문제에 대한 수정 제안을 코드와 함께 제시해주세요.
```

## 출력 형식

리뷰 결과는 심각도 순으로 정리합니다:
- Critical Issues (즉시 수정)
- High Priority
- Medium Priority
- Low Priority / Suggestions

## 주의사항

- 리팩토링 시 기존 동작을 반드시 보존
- 테스트가 있다면 테스트 통과 확인
- 한 번에 너무 많은 변경보다 점진적 개선 권장
