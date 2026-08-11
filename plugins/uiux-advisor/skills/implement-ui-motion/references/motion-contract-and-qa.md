# 모션 계약과 QA

## 상태 계약

모션이 있는 UI도 상태 머신으로 다룬다.

| 항목 | 확인 질문 |
| --- | --- |
| 진입 | 어떤 사용자·시스템 이벤트가 시작하는가? |
| 시작 상태 | DOM, 시각, 접근성 tree와 focus는 어디에 있는가? |
| 진행 상태 | 입력을 계속 받을 수 있는가? 반복 입력은 어떻게 합쳐지는가? |
| 완료 상태 | 시각 상태와 실제 application state가 일치하는가? |
| 취소 | 사용자 취소, route change, unmount와 오류에서 어디로 가는가? |
| 역방향 | 열기 중 닫기, 전진 중 뒤로 가기가 자연스럽고 결정적인가? |
| 감소 모션 | 공간 이동·자동 반복을 제거한 동등한 상태 전달이 있는가? |

## 구현 패턴

### 컴포넌트 lifecycle

- animation instance, timer, event listener와 observer의 owner를 명확히 한다.
- 재실행 전에 이전 instance를 cancel하거나 의도적으로 이어받는다.
- cleanup은 완료된 animation에서도 안전하게 호출 가능하게 한다.
- 개발 모드의 이중 mount나 hot reload에서 중복 listener와 timeline이 생기지 않는지 확인한다.

### 사용자 입력

- 빠른 double click, key repeat, pointer cancel과 touch interruption을 확인한다.
- 애니메이션 중 disabled가 필요한 경우 이유와 사용자 피드백을 제공한다.
- dialog, popover와 menu는 시각 transition과 별개로 focus contract를 지킨다.
- drag, hover와 pointer-follow effect에는 keyboard·touch 또는 정적 대안을 둔다.

### reduced motion

- `prefers-reduced-motion: reduce`를 CSS와 JavaScript 양쪽 경로에서 반영한다.
- 큰 이동, zoom, parallax, camera motion, 자동 회전과 무한 반복을 우선 제거한다.
- opacity flash도 과도하면 즉시 상태 변경이나 짧은 crossfade로 바꾼다.
- 설정 변경이 열린 페이지에 즉시 반영되는지 확인한다.

### 렌더링과 성능

- duration, easing과 stagger는 기존 제품 token·선례를 우선한다. 새 값은 출처가 있는 요구사항이 아니면 초기 가설로 표시하고 입력 연속성·인지 가능성과 성능을 보며 조정한다.
- animation 전후 DOM 측정을 한 프레임에 섞어 강제 layout을 만들지 않는다.
- 요소 수와 animation 대상 수를 제한하고 보이지 않는 반복 효과를 중지한다.
- canvas, shader와 SVG filter는 CPU·GPU 사용, battery와 저사양 기기 대안을 확인한다.
- `will-change`를 상시·광범위하게 적용하지 않는다.

## 브라우저 QA 시나리오

1. 첫 진입과 재진입
2. animation 중 반대 입력
3. 빠른 반복 입력
4. 뒤로 가기와 route change
5. viewport resize와 orientation change
6. background tab 전환 후 복귀
7. reduced motion 설정 전환
8. keyboard-only와 touch-only 조작
9. 느린 CPU 또는 저성능 device emulation
10. 오류·loading 상태 중 transition

## 완료 보고

다음을 구분해 보고한다.

- 실제 구현한 transition과 사용 기술
- 네이티브 또는 기존 도구 대신 새 도구를 쓴 이유
- 중단·역재생·cleanup 동작
- reduced-motion 대안
- 실행한 자동·브라우저·성능 검증
- 확인하지 못한 브라우저, 보조기술과 장치
