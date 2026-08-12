---
name: implement-ui-interaction
description: 기존 프론트엔드에 키보드·포커스·터치·포인터·제스처와 비동기 상태가 정확한 상호작용을 구현하고 검증한다. 사용자가 Dialog, Popover, Tooltip, Menu, Combobox, Carousel, drag·swipe·pinch, floating positioning, agent·tool 실행 상태, 취소·재시도·부분 성공 흐름을 실제 코드로 만들어 달라고 할 때 사용한다. 시간 기반 모션 자체가 주 결과물이면 implement-ui-motion을, 화면의 시각적 조합이 주 결과물이면 compose-creative-ui를, 원칙·명세만 필요하면 uiux-advisor를, 기존 결과의 문제 감사만 필요하면 uiux-auditor를 사용한다.
---

# UI Interaction Implementer

상호작용의 시각 효과보다 입력, 상태, 포커스, 피드백과 복구 계약을 먼저 구현한다. pointer에서만 작동하는 데모가 아니라 keyboard, touch, 보조기술과 실패 상태에서도 같은 과업을 완료할 수 있게 한다.

## 시작 절차

1. 저장소 지침과 현재 diff를 확인하고 framework, 렌더링 방식, package manager, browser 범위, 기존 primitive·상태 관리·테스트 도구를 읽는다.
2. 대상 UI를 실행하거나 코드로 확인한다. 관찰하지 않은 keyboard, focus, touch와 보조기술 동작을 사실처럼 단정하지 않는다.
3. 상호작용의 주 결과를 분류한다.

   - `composite-widget`: Dialog, Menu, Tabs, Combobox, Tooltip, Popover
   - `collection-navigation`: Carousel, list navigation, reorder
   - `direct-manipulation`: drag, swipe, pinch, pan, resize
   - `async-operation`: agent·tool 실행, upload, generate, batch action
   - `floating-surface`: anchor positioning과 collision 처리

4. 구현 전에 다음 계약을 짧게 고정한다.

   ```text
   사용자 과업과 완료 상태:
   trigger·entry·exit:
   상태의 진실 원본:
   keyboard·focus·screen reader:
   pointer·touch·gesture와 동등한 대안:
   loading·partial·success·error·cancel·retry:
   dismiss·undo·recovery:
   responsive·zoom·reduced-motion:
   fallback과 성공·반증 기준:
   ```

5. `../uiux-advisor/scripts/search_toolkits.py --capability <capability> --surface <surface> --ecosystem <ecosystem>`으로 후보를 찾는다.
6. 도구 선택은 `references/interaction-toolkit-selection.md`, 상태와 QA는 `references/interaction-contract-and-qa.md`를 읽어 적용한다.
7. agent·tool 실행 화면은 `references/agent-tool-state-ux.md`도 읽는다.

## 도구 선택 규칙

- 먼저 semantic HTML과 현재 프로젝트의 component·primitive로 해결한다.
- focus management와 keyboard pattern이 복잡한 widget은 기존 Base UI, Radix, React Aria, Ark UI 또는 같은 역할의 검증된 primitive를 우선한다.
- Floating UI는 anchor 좌표와 collision 문제를 해결하는 positioning engine으로 사용한다. 그것만으로 Dialog, Menu, Tooltip의 semantics가 완성된다고 가정하지 않는다.
- Carousel은 scroll snap이나 기존 component가 충분한지 먼저 확인하고, 세밀한 headless 제어가 필요하면 Embla, 다수의 내장 효과가 실제 요구면 Swiper를 검토한다.
- drag·swipe·pinch 인식이 복잡하면 `@use-gesture`를 검토하고, 물리 반응이 핵심이면 React Spring 또는 기존 Motion 도구와 결합한다.
- 목록 추가·삭제·재정렬의 작은 layout 변화는 AutoAnimate를 검토하되 focus, 읽기 순서와 완료 상태를 animation에 맡기지 않는다.
- 이미 설치된 적합한 도구가 있으면 새 의존성을 추가하지 않는다. 도입 전 현재 공식 API, 설치 버전, license, bundle, SSR·hydration과 제거 비용을 확인한다.

## 구현 규칙

### 입력과 포커스

- native element로 가능한 동작을 `div`와 임의 ARIA로 다시 만들지 않는다.
- 보이는 label, accessible name, role, value와 state를 실제 동작과 동기화한다.
- trigger에서 surface로 들어가는 focus, 내부 탐색, Escape·외부 dismiss, 닫힌 뒤 focus 복귀를 명시한다.
- hover에만 정보나 행동을 숨기지 않는다. focus, click 또는 touch에서 동등하게 발견 가능하게 한다.
- drag·swipe·pinch가 유일한 조작이 되지 않게 button, keyboard, direct input 같은 동등한 경로를 제공한다.
- screen width로 입력 장치를 추정하지 않는다. coarse pointer, keyboard와 touch가 섞인 환경을 처리한다.

### 상태와 비동기 작업

- application state를 시각 transition이나 animation callback의 결과로만 관리하지 않는다.
- idle, acknowledged, running, waiting, partial, success, error와 cancelled 중 실제로 필요한 상태와 전이를 명시한다.
- 알 수 없는 진행을 허위 percentage로 표현하지 않는다. 중복 실행, 취소, retry와 late response 규칙을 정한다.
- optimistic update는 실패 시 원상 복구와 오류 설명이 가능할 때만 사용한다.
- 일부 항목만 성공하면 완료와 실패 범위를 나누고 안전한 재시도 단위를 제공한다.
- 중요한 완료와 실패는 사라지는 motion이나 color 하나에만 의존하지 않는다.

### 생명주기와 표현

- listener, observer, timer, animation, gesture recognizer와 async request의 owner와 cleanup을 명확히 한다.
- 빠른 반복 입력, pointer cancel, route change, unmount와 development remount에서 중복 실행을 막는다.
- floating surface는 viewport·scroll container collision, zoom, virtual keyboard와 content resize를 처리한다.
- reduced motion은 과업과 상태 피드백을 유지하면서 큰 이동, 반복, parallax와 physics overshoot를 줄인다.
- 작은 화면, 확대, 긴 번역과 virtual keyboard에서도 trigger, surface, 오류와 핵심 action이 가려지지 않게 한다.

## 검증

1. 관련 unit·interaction 테스트, type check, lint와 build를 실행한다.
2. 정상 경로와 함께 빠른 반복, 반대 입력, 취소, timeout, 오류, partial success, retry와 뒤로 가기를 확인한다.
3. Tab·Shift+Tab·Enter·Space·Escape·Arrow·Home·End 중 해당 패턴이 요구하는 keyboard 동작과 focus 복귀를 실제 브라우저에서 확인한다.
4. mouse, touch, coarse pointer, zoom·reflow, orientation change와 virtual keyboard를 범위에 맞게 확인한다.
5. 접근성 tree와 screen reader announcement를 자동 검사만으로 보장하지 말고, 실제 확인 범위와 미검증 조합을 구분한다.
6. 새 dependency를 추가했다면 lockfile, transitive dependency, bundle, license와 사용하지 않는 import를 검토한다.
7. 구현한 상태 계약, 채택·제외 도구, 동등한 입력 경로, 복구 동작, 실행한 검증과 미검증 환경을 보고한다.

## 경계

- 상호작용 원칙, 컴포넌트 명세와 도구 비교만 필요하면 `uiux-advisor`를 사용한다.
- 기존 화면의 상호작용 결함을 찾고 우선순위만 정하면 `uiux-auditor`를 사용한다.
- easing, timeline, scroll choreography와 공간 전환 자체가 핵심이면 `implement-ui-motion`을 사용한다.
- hero, background, card와 text effect 조합이 핵심이면 `compose-creative-ui`를 사용한다.
- 여러 화면이 공유하는 interaction token과 component API를 시스템화하면 `build-design-system`을 함께 적용한다.
- Rive, Three.js·R3F, PixiJS와 Theatre.js 기반 그래픽 장면이 주 결과면 `build-interactive-graphics`를 사용한다. 일반 widget에는 기본 도구처럼 도입하지 않는다.
