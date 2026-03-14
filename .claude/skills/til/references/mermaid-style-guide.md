# Mermaid 스타일 가이드

TIL 문서에서 mermaid 다이어그램 작성 시 따라야 할 규칙.

## ASCII 박스 금지

한글과 영문의 폭이 달라서 정렬이 깨진다. 테이블 또는 mermaid를 사용하라.

| 기존 ASCII | 변환 대상 |
|------------|----------|
| 박스형 정보 나열 | **테이블** |
| 흐름도, 화살표 | **mermaid flowchart** |
| 구조도, 계층 | **mermaid flowchart + subgraph** |
| 시퀀스, 순서 | **mermaid sequenceDiagram** |
| 단순 목록 | **불릿 포인트** 또는 **테이블** |

> **ASCII 박스를 반드시 사용해야 하는 경우:** 박스 내부 텍스트는 **영어만 사용하라.**

## 다이어그램 타입 선택

| 상황 | 다이어그램 타입 |
|------|-----------------|
| 워크플로우, 프로세스 | `graph` / `flowchart` |
| 시간 순서 상호작용 | `sequenceDiagram` |
| 클래스 구조, 아키텍처 | `classDiagram` |
| DB 스키마, 엔티티 관계 | `erDiagram` |
| 역사/타임라인 | `timeline` |
| 네트워크 패킷 구조 | `packet-beta` |

**시각화가 유용한 경우:**
- Before/After 비교
- 단계별 프로세스 (1->2->3->4)
- 시스템 아키텍처
- 상태 전이

## 노드 스타일 규칙 (CRITICAL)

**개별 노드는 어두운 배경 + 흰 글씨만 사용. subgraph는 기본 배경.**

```markdown
❌ Bad: style Node fill:#e1f5ff          (color 생략 -> 글씨 안 보임)
❌ Bad: style Node fill:#E3F2FD,color:#000  (밝은 배경 -> 눈에 안 띔)

✅ Good: style Node fill:#1565C0,color:#fff  (어두운 배경 + 흰 글씨)
```

### 권장 색상 팔레트

| 용도 | fill (배경) | color (글씨) |
|------|-------------|--------------|
| 시작/핵심 (파랑) | `#1565C0` | `#fff` |
| 종료/성공 (초록) | `#2E7D32` | `#fff` |
| 조건/분기 (주황) | `#E65100` | `#fff` |
| 오류/위험 (빨강) | `#C62828` | `#fff` |

### subgraph 규칙

```markdown
❌ Bad: subgraph에 style 지정
subgraph Group["그룹"]
    ...
end
style Group fill:#E3F2FD,color:#000

✅ Good: subgraph는 기본 배경 사용 (style 생략)
subgraph Group["그룹"]
    ...
end
```

> **원칙:** 개별 노드만 어두운 배경 + `color:#fff`로 강조. subgraph는 style 지정하지 않음.

## 줄바꿈 규칙

`\n`은 텍스트로 출력된다. `<br>`을 사용하라.

```markdown
❌ Bad: ["첫째 줄\n둘째 줄"]
✅ Good: ["첫째 줄<br>둘째 줄"]
```

**적용 예시:**

```mermaid
flowchart LR
    A["Cost-Based Optimizer<br>(CBO)"] --> B["통계 기반<br>비용 계산"]
```

## sequenceDiagram 전용 규칙

**sequenceDiagram은 `style` 선언을 지원하지 않는다.** 영역 강조에는 `rect rgba()`를 사용하라.

```markdown
❌ Bad: style 선언 시도 (무시됨)
style A fill:#1565C0,color:#fff

❌ Bad: 밝은 불투명 색상 (다크 모드에서 눈이 아픔)
rect rgb(200, 220, 255)

✅ Good: 반투명 어두운 색상
rect rgba(198, 40, 40, 0.3)
    Note right of A: 설명
end
```

### 권장 색상

| 용도 | rgba 값 |
|------|---------|
| 비효율/문제 (빨강) | `rgba(198, 40, 40, 0.3)` |
| 효율/해결 (초록) | `rgba(46, 125, 50, 0.3)` |
| 정보/강조 (파랑) | `rgba(21, 101, 192, 0.3)` |
| 주의/경고 (주황) | `rgba(230, 81, 0, 0.3)` |

> **원칙:** sequenceDiagram에서는 `style`이 아닌 `rect rgba()`로 영역을 강조. 투명도 `0.3`이 다크/라이트 모드 모두 적절.
