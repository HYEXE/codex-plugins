---
name: implement-async-ui-state
description: 기존 프론트엔드에서 요청·스트림·background job·batch 작업의 비동기 상태를 실제 코드로 구현하고 검증한다. 사용자가 upload·generate·export·save·agent·tool 실행 화면에 접수·진행·사용자 입력 대기·부분 성공·오류·취소·재시도·재연결을 구현하거나 중복 실행, optimistic rollback, stale·late response와 job identity 문제를 해결해 달라고 할 때 사용한다. Dialog·Combobox·Carousel의 키보드·포커스·제스처 계약이 주 결과면 implement-ui-interaction을, 시간 기반 시각 전환은 implement-ui-motion을, 원칙·명세만 필요하면 uiux-advisor를, 기존 결과의 문제 감사만 필요하면 uiux-auditor를 사용한다.
---

# Async UI State Implementer

비동기 작업의 시각 효과보다 서버 사실, 요청 식별자, 상태 전이와 사용자 통제 계약을 먼저 구현한다. 빠른 정상 경로뿐 아니라 중복 실행, 순서가 바뀐 응답, 중단·재연결과 부분 실패에서도 UI가 실제 작업 상태를 정직하게 보여주게 한다.

## 시작 절차

1. 저장소 지침과 현재 diff를 확인하고 framework, 상태 관리, transport, backend API, persistence와 테스트 도구를 읽는다.
2. 실제 요청·응답·event·job schema와 취소 API를 확인한다. 관찰하지 않은 server cancel, progress, idempotency 또는 background persistence를 지원한다고 가정하지 않는다.
3. 작업 유형을 분류한다.

   - `request`: 현재 화면 수명 안에서 끝나는 조회·저장·mutation
   - `stream`: chunk·event가 순차 또는 누적 도착하는 응답
   - `background-job`: 화면을 떠난 뒤에도 계속될 수 있고 재조회가 필요한 작업
   - `batch`: 항목별 성공·실패와 재시도 범위가 갈리는 작업

4. 구현 전 다음 상태 계약을 짧게 고정한다.

   ```text
   사용자 과업과 완료 상태:
   request·operation·job·item identity:
   진실 원본과 상태 전이:
   순서·중복·동시 실행 정책:
   취소 범위와 server side effect:
   retry·idempotency·optimistic rollback:
   partial result와 실패 단위:
   refresh·reconnect·multi-tab 복원:
   접근 가능한 피드백과 focus 정책:
   성공·반증 기준:
   ```

5. 상태 모델과 QA에는 `references/async-state-contract-and-qa.md`를 읽어 적용한다.
6. agent·tool 실행 화면은 `references/agent-tool-state-ux.md`도 읽는다.

## 구현 규칙

### 식별자와 상태 원본

- UI component instance, network request, logical operation, server job과 batch item identity를 필요한 수준으로 분리한다.
- 현재 결과를 갱신할 자격이 있는 operation을 명시하고 stale·late response가 최신 상태를 덮지 못하게 한다.
- server가 진실 원본이면 local label이나 timer로 완료를 추정하지 않고 status 조회·event 또는 명시적 응답과 동기화한다.
- component unmount, route change, account·workspace 변경 때 구독과 local state의 소유권을 정리한다.

### 중복·취소·재시도

- disable만으로 중복 요청이 완전히 방지된다고 가정하지 않는다. 실행 단위, deduplication과 idempotency 경계를 정한다.
- network abort, UI가 기다림을 중단하는 cancel, server job 취소를 같은 동작으로 표현하지 않는다.
- 취소와 완료가 경합하면 어떤 terminal state를 채택할지 backend 계약에 맞춰 결정한다.
- retry는 새 operation인지 같은 job의 재개인지 구분하고, 생성·결제·전송 같은 side effect에는 검증된 idempotency를 사용한다.

### 낙관적 갱신과 부분 결과

- optimistic update는 해당 mutation의 이전 값·version과 rollback 범위를 보존할 수 있을 때만 사용한다.
- 늦은 실패가 이후의 성공한 편집을 되돌리지 않도록 mutation identity와 version을 비교한다.
- batch·stream의 일부가 성공하면 전체 성공이나 전체 실패로 축약하지 않고 완료·실패·대기 항목을 구분한다.
- 실패 항목만 안전하게 재시도할 수 있는 단위를 제공하고 이미 성공한 side effect를 반복하지 않는다.

### 표현과 접근성

- 실제 수치를 계산할 수 있을 때만 percentage를 표시하고, 그 외에는 단계나 비결정적 진행을 사용한다.
- 중요한 완료·실패·부분 결과는 사라지는 toast, color 또는 motion 하나에만 의존하지 않는다.
- 상태 변경을 `aria-live`로 모두 읽지 않는다. 사용자 행동에 필요한 시작·blocker·완료·실패만 적절한 빈도로 알린다.
- 상태가 바뀔 때마다 focus를 빼앗지 않는다. 사용자 입력이 필요한 blocker는 발견 가능한 위치와 명시적 이동 경로를 제공한다.
- 오류는 보존된 작업, 영향 범위, 안전한 다음 행동을 설명하고 credential, prompt, 개인정보와 내부 stack을 노출하지 않는다.

## 검증

1. 관련 unit·state-machine·integration 테스트, type check, lint와 build를 실행한다.
2. 정상 완료와 함께 빠른 이중 실행, 응답 순서 역전, 중복 event와 오래된 cache를 확인한다.
3. timeout, offline, reconnect, refresh, route change, unmount, background tab과 multi-tab을 범위에 맞게 확인한다.
4. cancel 요청과 완료의 경합, cancel 실패, server side effect 잔존과 다시 시작을 검증한다.
5. optimistic success·failure·version conflict와 이후 편집을 침범하지 않는 rollback을 검증한다.
6. batch·stream의 partial success, 실패 범위 재시도, 중복 chunk와 재연결 resume를 검증한다.
7. keyboard 흐름, focus 유지, live announcement 빈도와 motion·color 없이 상태를 이해할 수 있는지 확인한다.
8. 구현한 상태 계약, backend에서 확인한 사실, 채택·제외한 정책, 실행한 검증과 미검증 환경을 보고한다.

## 경계

- Dialog·Popover·Menu·Combobox·Carousel·drag의 keyboard, focus, touch와 gesture 계약이 주 결과면 `implement-ui-interaction`을 사용한다.
- Combobox에 server 검색이 있어도 주 결과가 option 탐색·선택과 focus 계약이면 `implement-ui-interaction`을 사용하고, request ordering과 server 상태 원본·전이는 이 스킬이 맡고, option 탐색·선택·focus와 접근 가능한 표현은 `implement-ui-interaction`이 맡는다.
- easing, timeline, scroll choreography와 시각 전환 자체가 주 결과면 `implement-ui-motion`을 사용한다.
- 상태 원칙, 컴포넌트 명세와 대안 비교만 필요하면 `uiux-advisor`를 사용한다.
- 기존 화면에서 상태 누락과 복구 결함을 찾고 우선순위만 정하면 `uiux-auditor`를 사용한다.
- Rive·Three.js·R3F·PixiJS 장면이 상태를 표현하는 것이 주 결과면 `build-interactive-graphics`를 사용하고, 실제 작업 수명주기는 이 스킬의 계약과 분리한다.
