# Scene lifecycle

자동 시연은 슬라이드에 붙인 일회성 timer 묶음이 아니라 명시적인 Scene Controller로 구현한다.

## 상태

```text
ready → running → complete
  ↑        │          │
  └─ reset/replay ────┘
           │
         cancel
```

- `ready`: 결정적인 초기 화면이며 재생 가능한 상태
- `running`: 현재 run token이 소유한 timer와 비동기 작업만 화면을 변경할 수 있는 상태
- `complete`: 핵심 결과와 다음 이동이 가능한 상태
- `cancel`: 상태 이름이 아니라 현재 run을 무효화하고 자원을 정리하는 동작

## Scene Controller 인터페이스

```js
{
  blocksAdvance: true,
  status: "ready",
  start(),
  advance(),
  skip(),
  replay(autoplay),
  cancel(),
  destroy()
}
```

- Deck Controller는 `status`와 `blocksAdvance`만 보고 진행을 결정한다.
- `start()`는 demo 자동 재생을 시작한다.
- `advance()`는 experience에서 다음 phase를 직접 표시한다.
- `skip()`은 남은 phase를 즉시 완료 상태로 만들거나 장면을 떠나기 전에 취소한다.
- `replay(true)`는 reset 후 자동 재생하고 `replay(false)`는 ready로 돌아간다.
- `destroy()`는 timer, interval, listener, observer와 장면이 소유한 DOM 참조를 정리한다.

## 실행 안전성

- 새 실행마다 증가하는 run token을 만들고 callback은 자신의 token이 현재 token과 같을 때만 상태를 바꾼다.
- slide 이동, mode 전환, replay와 destroy에서 이전 run token을 무효화한다.
- reduced motion에서는 같은 phase와 결과를 유지하되 delay를 짧게 줄인다.
- 장면 중 오류가 나면 핵심 결과를 정적 텍스트로 남기고 Deck Controller 이동을 막지 않는다.
- 실제 명령·개인정보·포렌식 로그처럼 보이는 재구성 데이터에는 `SYNTHETIC TELEMETRY` 또는 동등한 표시를 둔다.
- 사용자가 제공하지 않은 사실, 수치와 인용을 시연 효과를 위해 만들지 않는다.
