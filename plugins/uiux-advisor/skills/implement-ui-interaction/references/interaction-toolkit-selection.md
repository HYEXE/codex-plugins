# 상호작용 도구 선택

공식 문서 확인 기준일: 2026-08-12

이 문서는 고정된 API 사본이 아니다. 구현할 때 설치된 버전과 현재 공식 문서를 다시 확인한다. 구조화 후보는 `../uiux-advisor/scripts/search_toolkits.py`에서 capability, surface와 ecosystem으로 먼저 좁힌다.

## 선택 순서

1. semantic HTML과 native browser behavior로 과업을 완료할 수 있는가?
2. 현재 프로젝트의 primitive와 component가 이미 상태·focus·keyboard 계약을 제공하는가?
3. 필요한 것은 전체 widget인가, positioning·gesture·physics 같은 좁은 engine인가?
4. 새 도구가 제공하는 고유 기능이 dependency, bundle과 유지보수 비용을 정당화하는가?
5. 도구가 없어도 핵심 과업이 유지되는 fallback을 만들 수 있는가?

## 후보별 역할

| 후보 | 우선 검토 상황 | 주의·피할 상황 | 공식 자료 |
| --- | --- | --- | --- |
| Semantic HTML·CSS | button, disclosure, native scroll, form과 단순 focus | 복합 widget의 keyboard pattern을 임의로 축약할 때 | [HTML elements](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements) |
| Base UI·Radix·React Aria | React의 Dialog, Menu, Tooltip, Combobox와 focus 관리 | 기존 foundation과 중복되거나 styling·state 모델이 충돌할 때 | [Base UI](https://base-ui.com/react/overview/about), [Radix](https://www.radix-ui.com/primitives/docs/overview/introduction), [React Aria](https://react-spectrum.adobe.com/react-aria/) |
| Ark UI | React·Vue·Svelte·Solid에서 headless state machine이 필요할 때 | 프로젝트 native component가 이미 같은 역할을 할 때 | [Ark UI](https://ark-ui.com/docs/overview/about) |
| Floating UI | Tooltip, Popover, Menu와 floating toolbar의 offset·flip·shift·size | positioning만으로 semantics·focus·dismiss가 완성됐다고 볼 때 | [Floating UI](https://floating-ui.com/docs/usefloating) |
| Embla Carousel | 디자인 시스템에 맞춘 headless carousel과 custom controls | carousel이 불필요하거나 기본 scroll 영역으로 충분할 때 | [Embla API](https://www.embla-carousel.com/docs/api), [accessibility](https://www.embla-carousel.com/docs/plugins/accessibility) |
| Swiper | zoom, effect, virtual slide 등 풍부한 내장 기능이 실제 요구일 때 | 단순 carousel에 큰 기능 집합을 도입할 때 | [Swiper](https://swiperjs.com/) |
| `@use-gesture` | drag, swipe, pinch, pan, wheel의 시작·진행·종료·취소 인식 | click·keyboard 대안 없이 gesture를 핵심 과업으로 만들 때 | [Gestures](https://use-gesture.netlify.app/docs/gestures/) |
| React Spring | gesture 결과의 physics, elastic return과 interruptible spring | duration transition이나 기존 Motion으로 충분할 때 | [React Spring](https://react-spring.dev/docs/getting-started) |
| AutoAnimate | DOM 자식의 add·remove·move에 작은 layout feedback이 필요할 때 | 세밀한 sequence, business state 또는 focus 이동을 맡길 때 | [AutoAnimate](https://auto-animate.formkit.com/) |

## Interaction과 Motion의 결합

- gesture recognizer는 input을 해석하고, animation library는 시각 반응을 표현한다. 두 역할을 섞어 상태의 진실 원본을 만들지 않는다.
- Floating UI의 positioning transform과 animation transform이 충돌하면 positioned wrapper와 animated child를 분리한다.
- Carousel의 slide animation보다 current item, controls, focus, announcement와 autoplay 중단 계약을 먼저 고정한다.
- spring이나 inertia가 끝나지 않아도 application state, focus와 accessible state는 결정적이어야 한다.

## 의존성 도입 게이트

- 정확한 package와 설치 버전
- 현재 framework·SSR·hydration 호환성
- official docs, repository와 release 상태
- license·유료 기능·asset 권리
- tree-shaking, bundle, runtime와 memory 비용
- global CSS, portal, z-index와 event system 영향
- keyboard, screen reader, touch와 reduced-motion 지원 범위
- 제거·교체·fallback 비용

확인할 수 없는 항목은 성공 조건으로 가정하지 말고 미검증으로 보고한다.
