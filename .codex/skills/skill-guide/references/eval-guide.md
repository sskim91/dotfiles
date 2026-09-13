# skill-creator Eval 사용 가이드

skill-creator 플러그인의 eval 기능으로 스킬 품질을 측정하고 개선하는 방법.

## 4단계 루프

```
Create → Eval → Improve → Benchmark
  ↑                          ↓
  └──────────────────────────┘
```

1. **Create**: 스킬 작성 또는 수정
2. **Eval**: 테스트 프롬프트로 with-skill vs baseline 비교
3. **Improve**: eval 결과 기반 스킬 개선
4. **Benchmark**: 분산 분석으로 통계적 유의성 확인

## Eval 실행 방법

### 기본 eval

skill-creator 플러그인을 호출하여 eval 실행:

```
/skill-creator eval <skill-name>
```

### 테스트 프롬프트 작성

좋은 eval 프롬프트는:
- 스킬의 핵심 기능을 테스트하는 실제 사용 시나리오
- 최소 3개, 권장 5개 이상
- 다양한 난이도와 엣지 케이스 포함

예시 (obsidian-note 스킬):
```
1. "Redis Pub/Sub에 대해 옵시디언 노트 작성해줘"
2. "MoE 아키텍처에 대해 Obsidian에 정리해줘"
3. "CAP 정리와 실제 트레이드오프에 대해 노트 작성"
```

### Baseline 비교

- **with-skill**: 현재 SKILL.md를 로딩한 상태에서 실행
- **baseline**: SKILL.md 없이 (또는 이전 버전 SKILL.md로) 실행
- 동일 프롬프트로 둘 다 실행하여 품질 비교

### 평가 기준

| 기준 | 설명 |
|------|------|
| 정확성 | 사실 오류 없는지 |
| 구조 | 스킬이 지시한 포맷을 따르는지 |
| 완성도 | 필수 섹션/단계를 빠뜨리지 않았는지 |
| 차별화 | baseline 대비 눈에 띄는 품질 차이가 있는지 |

## Benchmark

여러 번 반복 실행하여 분산(variance)을 측정:
- 동일 프롬프트를 3-5회 반복
- 점수의 평균과 표준편차 비교
- 통계적으로 유의미한 차이가 있는지 확인

## 비용과 주의사항

> **CRITICAL**: 스킬 테스트는 반드시 **Claude Code subagent 방식**(Agent tool)으로 실행할 것.
> 구독 사용량으로 처리되므로 별도 API 과금이 발생하지 않는다.
> skill-creator의 `claude -p` 방식은 API 크레딧을 직접 소모하므로 사용하지 않는다.

- **Claude Code subagent 방식 (권장)**: 세션 내 Agent tool로 실행. 구독 사용량으로 잡힘. 스킬 1개당 약 70-80k 토큰 (with-skill + old-skill + grading)
- **skill-creator `claude -p` 방식 (비권장)**: 별도 CLI 프로세스로 실행. API 크레딧 직접 소모
- API 과부하(529) 시 재시도 필요 — 시간을 두고 다시 실행
- 전체 스킬 eval은 비용이 크므로, **변경된 스킬만** 대상으로 실행
- 스킬 수정 후 eval을 돌려야 개선 여부를 객관적으로 확인 가능
