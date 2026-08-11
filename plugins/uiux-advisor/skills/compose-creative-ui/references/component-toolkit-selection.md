# 컴포넌트·시각 효과 도구 선택

공식 문서 확인 기준일: 2026-08-11

이 목록은 무조건 설치할 추천 순위가 아니다. 현재 framework와 기존 design system을 보존하면서 필요한 역할 하나를 채우는 후보군이다.

## 역할 구분

| 역할 | 후보 | 선택 기준 | 공식 자료 |
| --- | --- | --- | --- |
| 기존 foundation | 프로젝트에 이미 설치된 system | 기본 선택. API, token과 state를 유지 | 저장소의 package·components·styles |
| 소스 소유 registry | shadcn/ui와 compatible registries | code를 직접 보유·수정해야 하고 registry payload를 검토할 수 있을 때 | [shadcn/ui](https://ui.shadcn.com/docs), [registry directory](https://ui.shadcn.com/docs/directory) |
| React headless primitive | React Aria, Base UI, Radix Primitives | 복잡한 interaction·focus·keyboard 기반을 직접 styling할 때 | [React Aria](https://react-spectrum.adobe.com/react-aria/), [Base UI](https://base-ui.com/react/overview/about), [Radix](https://www.radix-ui.com/primitives/docs/overview/introduction) |
| 다중 framework primitive | Ark UI | React·Vue·Svelte·Solid에서 headless component가 필요할 때 | [Ark UI](https://ark-ui.com/docs/overview/about) |
| 마케팅·landing accent | Magic UI | 기존 React·Tailwind 화면에 제한된 effect나 section pattern을 넣을 때 | [Magic UI](https://magicui.design/docs) |
| 고강도 interactive accent | Aceternity UI | React·Next·Tailwind·Motion stack에서 hero·background·card 효과가 과업에 맞을 때 | [Aceternity UI](https://ui.aceternity.com/components) |
| animated component·background | React Bits | React 화면에 독립적인 text, background, animation component가 필요할 때 | [React Bits](https://reactbits.dev/) |
| data visualization | Bklit UI | shadcn 기반 dashboard chart를 구현할 때 | [Bklit UI](https://bklit.com/docs) |

## 선택 순서

1. 기존 component와 CSS로 표현할 수 있는지 확인한다.
2. semantics·focus·keyboard가 어려운 복합 widget이면 검증된 primitive를 선택한다.
3. 시각적 개성이 부족한 특정 구간에만 accent library를 검토한다.
4. chart는 장식 library가 아니라 `build-data-visualization`의 기준으로 선택한다.
5. timeline·gesture·scroll 구현은 `implement-ui-motion`의 기준으로 선택한다.

## framework 적합성

- React 전용 source를 Vue·Svelte로 수동 번역하기 전에 native 또는 multi-framework 대안을 찾는다.
- Next.js에서는 server/client boundary와 hydration을 확인한다.
- Vue·Svelte·Solid에서는 React demo의 DOM과 motion semantics만 참고하고 코드를 그대로 복사하지 않는다.
- plain HTML 또는 작은 widget에서는 framework 도입보다 CSS, Web Components와 네이티브 API가 더 적합할 수 있다.

## 시각적 과잉 방지

- 화면의 핵심 message와 CTA를 먼저 읽고 효과는 그 다음에 인지돼야 한다.
- 서로 다른 registry에서 유사한 glow, gradient, motion을 중복해서 가져오지 않는다.
- pointer follower, shader, 3D, infinite marquee와 parallax를 동시에 기본값으로 사용하지 않는다.
- 효과의 제거 전후로 이해도와 행동 가능성이 같으면 성능·주의 비용을 고려해 제거한다.
- 레퍼런스의 위계와 아이디어를 빌릴 수 있지만 제품의 typography, color, spacing과 content voice를 유지한다.

## 채택 전에 확인

- source와 package license, 유료·무료 경계
- registry payload와 transitively added dependency
- global CSS, Tailwind config와 reset 변경
- client-only API와 hydration
- keyboard, focus, screen reader, touch와 reduced motion
- responsive behavior와 content overflow
- bundle, image, font, canvas·shader 비용
- 최근 release, issue와 framework compatibility

공식 registry directory에 있다는 사실만으로 코드의 보안·품질·접근성이 보증된다고 보지 않는다.
