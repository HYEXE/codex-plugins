# Prompt Compiler 0.4.0 개선

## 목표

`prompt-compiler` 플러그인에 요청 충분성을 판단하고 필요한 경우에만 질문으로 니즈를 구체화해 최종 프롬프트를 작성하는 `prompt-coach` 스킬을 추가한다.

## 범위

- one-shot과 task-scoped Prompt Sufficiency Gate
- `pass-through`, `refine-directly`, `clarify-before-compile` 결정 경계
- 한 차례 1~3개, 최대 두 차례의 질문 제한
- Coach·Compiler·Evaluator 간 비파괴적 라우팅 경계
- 플러그인 시작 프롬프트와 현재 작업 범위의 비보장적 지속 동작 안내
- 라우팅 평가, Prompt Coach 행동 평가, 공식 validator와 설치 cache 검증
- 플러그인 0.4.0 버전 갱신

## 완료 기준

- [x] 기존 저장소·브랜치·작업 트리 상태 확인
- [x] prompt-coach 스킬과 UI 메타데이터 구현
- [x] manifest, README, validator와 라우팅 평가 연결
- [x] Prompt Coach 독립 forward test와 행동 평가 통과
- [x] 공식 skill·plugin validator 통과
- [x] 임시 marketplace 설치와 source/cache 동일성 확인
- [x] 전체 diff와 Git 상태 검토
