# 상호작용 계약과 QA

패턴별 keyboard·focus 계약은 현재 프로젝트의 primitive와 함께 [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) 및 [Keyboard Interface Practice](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)를 확인한다. gesture가 핵심 조작이면 [WCAG 2.5.7 Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements)도 적용한다. 예제 코드를 복사하는 대신 실제 pattern의 role, state, keyboard와 focus 요구를 함께 구현한다.

## 상태 계약

| 항목 | 확인 질문 |
| --- | --- |
| 진입 | 어떤 사용자·시스템 event가 시작하며 중복 event는 어떻게 처리하는가? |
| 상태 원본 | visual, DOM, URL 중 무엇이 widget 상태의 진실 원본인가? |
| 입력 | keyboard, pointer, touch, gesture와 assistive technology 경로가 동등한가? |
| focus | 시작, 이동, trap 또는 roving, 닫힘 뒤 복귀가 결정적인가? |
| 진행 | 입력 도중 focus와 활성 항목이 일관되며 중단 가능한가? |
| 완료 | 시각 상태, accessible state와 application state가 일치하는가? |
| 실패 | invalid·disabled 상태와 대체 경로가 명확한가? |
| 중단 | Escape, pointer cancel, route change와 unmount를 어떻게 처리하는가? |

## 패턴별 핵심 계약

### Dialog

- 열릴 때 과업 시작점으로 focus를 이동하고 background interaction을 적절히 제한한다.
- Tab 순환, Escape 정책, title·description과 destructive action 우선순위를 정의한다.
- 닫힌 뒤 유효한 trigger 또는 다음 논리적 위치로 focus를 복귀시킨다.
- animation 중에도 focus contract와 accessible state가 뒤늦게 어긋나지 않게 한다.

### Popover·Tooltip·Menu

- trigger, anchor, surface와 dismissal 조건을 구분한다.
- tooltip은 pointer hover만이 아니라 keyboard focus에서 발견 가능하게 한다.
- menu는 단순 link 목록과 application menu를 구분하고 해당 keyboard pattern을 완전하게 구현한다.
- viewport, clipping ancestor, zoom, scroll과 content resize에서 위치를 다시 계산한다.

### Combobox·Listbox·Tabs

- DOM focus와 active descendant 중 하나의 전략을 일관되게 사용한다.
- Arrow, Home, End, Enter, Escape와 typeahead 중 실제 패턴에 필요한 동작을 구현한다.
- selected, active, expanded, disabled와 invalid 상태를 시각·접근성 표현에 동기화한다.
- 비동기 option은 loading, no result, error, stale request와 IME 입력을 처리한다. request 상태 원본·전이와 ordering은 `implement-async-ui-state`가 맡고, option 탐색·선택·focus와 접근 가능한 표현은 이 스킬이 맡는다.

### Carousel

- drag·swipe 외에 이전·다음과 직접 slide 선택 control을 제공한다.
- current position, total count와 control disabled 상태를 전달한다.
- autoplay는 기본 필요성을 검토하고 pause·focus·hover·reduced-motion 정책을 둔다.
- slide가 바뀔 때 focus를 강제로 이동하지 않고 announcement 빈도를 제한한다.
- 작은 화면, zoom, RTL과 긴 콘텐츠에서 slide size와 clipping을 확인한다.

### Drag·Swipe·Pinch·Reorder

- 시작 threshold, allowed axis, bounds, cancel, drop target와 invalid drop을 정의한다.
- drag가 scroll, text selection, browser zoom과 충돌하지 않게 `touch-action`을 필요한 범위에만 사용한다.
- keyboard reorder, stepper, button 또는 직접 값 입력 같은 동등한 조작을 제공한다.
- 이동 중과 drop 뒤 순서·위치 변화를 screen reader가 이해할 수 있게 필요한 정도만 알린다.
- pointer cancel, window blur, multi-touch와 device rotation에서 상태를 복구한다.
- dragging movement가 과업의 일부면 drag 없이 single pointer로 완료할 수 있는 동등한 조작을 제공한다. 예외 적용 여부는 실제 기능과 표준 조건을 확인한다.

## 브라우저 QA 시나리오

1. 첫 진입, 재진입과 빠른 반복 실행
2. keyboard-only 전체 과업과 역방향 탐색
3. mouse, touch, coarse pointer와 hybrid input
4. Escape, 외부 click, pointer cancel과 system interruption
5. loading, empty, invalid, disabled, error와 widget dismiss
6. route change, back navigation, refresh와 component unmount
7. 200%·400% zoom, 좁은 viewport, orientation과 virtual keyboard
8. reduced motion, high contrast, dark mode와 forced colors
9. 긴 한국어·영문, RTL, empty·large collection과 dynamic content
10. slow CPU, background tab 복귀와 multiple tabs

## 완료 보고

- 구현한 상호작용과 상태 원본
- keyboard·focus·touch·gesture 경로
- 채택·제외한 primitive·engine과 이유
- dismiss, invalid input과 복구 동작
- 자동·브라우저·접근성·성능 검증 결과
- 확인하지 못한 browser, device와 assistive technology 조합
