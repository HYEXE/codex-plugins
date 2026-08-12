# Render Loop Performance and QA

## 예산

숫자를 보편 기준으로 만들지 말고 대상 기기·network·viewport·scene에서 측정한다.

```text
초기 route·chunk 전송량:
가장 큰 model·texture·Rive asset:
초기화 중 main-thread long task:
현실적 상호작의 CPU·GPU frame time:
대기·이번트 부재 시 render work:
반복 mount·unmount 후 memory·context:
LCP·INP·layout 영향:
품질 저하·fallback trigger:
```

## lifecycle

- 초기화와 파괴를 같은 owner에 둔다.
- `requestAnimationFrame`, renderer ticker, observer, resize·pointer listener, worker, audio, decoder를 파괴 시 종료한다.
- Three.js 계열은 geometry, material, texture, render target과 renderer를 소유 규칙에 따라 dispose한다.
- page visibility, intersection, route state에 따 pause·resume하고, 재개 시 누적 delta로 scene이 튀지 않게 한다.
- resize·DPR 변경은 한 경로에서 처리하고 buffer·camera·CSS size의 불일치를 막는다.

## 성능 순서

1. 필요할 때만 lazy load하고 poster·DOM을 먼저 보여준다.
2. 지속 재생이 아니면 event-driven render로 전환한다.
3. 보이지 않거나 포커스를 잃은 scene의 work를 멈춘다.
4. texture·geometry·draw call·particle·shadow·post-processing을 실측 병목에 따라 줄인다.
5. DPR·LOD·effect quality를 환경에 따라 적응시키되, 핵심 내용·제어는 유지한다.

## 회귀 QA

- 초기 성공, slow load, 404·decode failure, offline·retry
- WebGL·canvas 비지원, context lost·restore, GPU process restart 가능 범위
- 빠른 반복 입력, pointer cancel, multi-touch, tab switch, resize·orientation
- reduced motion, keyboard-only, screen reader 확인 범위, 200%·40 400% zoom·reflow
- development remount, route 왕복, 다중 instance, asset 교체 후 중복 loop·listener·memory 증가
- fallback 중에도 핵심 정보·제어·연결·form 완료
