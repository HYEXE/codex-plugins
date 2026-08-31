# Mode contracts

하나의 deck 콘텐츠가 `experience`와 `demo`에서 서로 다른 진행 방식을 제공한다. `meta.modeLocked`가 `false`일 때만 URL의 `?mode=experience` 또는 `?mode=demo`로 초기 모드를 지정하고 화면 제어로 전환할 수 있게 한다. `modeLocked: true`이면 승인된 `defaultMode`를 유지하고 URL override와 모든 mode 전환 입력을 무시하며 전환 control을 숨긴다.

## Deck Controller

Deck Controller는 장면 내용을 알지 않는다. 슬라이드 이동, 목차, 진행률, hash, 확대·축소, 화면 맞춤, 전체화면, speaker notes, swipe와 전역 단축키만 소유한다. 슬라이드를 떠나기 전에 현재 Scene Controller의 `cancel()`과 `destroy()`를 호출한다.

## experience

- 청중 또는 발표자가 현재 슬라이드의 단계, 선택지와 슬라이더를 임의 순서로 탐색한다.
- `steps`, `comparison`, `choice`, `range`, `diagram`, `before-after`처럼 직접 조작하는 recipe를 사용한다. `sequence`, `timeline`, `code-walkthrough`는 demo 전용 blocking recipe다.
- 숨겨진 정답을 맞혀야 다음으로 갈 수 있게 만들지 않는다.
- 선택 결과에는 즉시 설명을 제공하고 replay는 현재 장면의 초기 상태만 복원한다.
- 직접 조작 없이도 제목과 요약으로 핵심 메시지를 이해할 수 있어야 한다.

## demo

- 전역 다음 키가 `ready` 상태의 blocking 장면을 만나면 다음 슬라이드로 가지 않고 자동 재생을 시작한다.
- 재생 중 전역 다음 키를 다시 누르면 현재 장면을 건너뛰고 다음 슬라이드로 이동한다.
- `complete` 상태에서 다음 키를 누르면 다음 슬라이드로 이동한다.
- replay는 현재 장면을 reset한 뒤 처음부터 다시 재생한다.
- 각 장면은 결정적인 초기값을 가지고 같은 입력으로 반복 가능한 결과를 보여준다.
- 자동 진행은 deck 전체가 아니라 현재 장면 안에서만 사용한다.

## 공통 제어

- `ArrowRight`, `PageDown`, `Space`, `Enter`: 다음 장면 동작 또는 슬라이드
- `ArrowLeft`, `PageUp`, `Backspace`: 이전 슬라이드
- `Home`, `End`: 처음·마지막 슬라이드
- `O`: 목차 열기·닫기
- `M`: mode 전환
- `N`: speaker notes 열기·닫기
- `R`: 현재 장면 replay
- `F`: fullscreen 요청
- `+`, `-`, `0`: 확대·축소·화면 맞춤
- URL hash: `#slide=N` 형식으로 현재 슬라이드 보존

입력 필드와 장면 내부 button에 focus가 있을 때는 문자·Space·Enter를 전역 이동으로 가로채지 않는다. 목차는 focus를 가두고 닫은 뒤 원래 trigger로 돌려보낸다.
