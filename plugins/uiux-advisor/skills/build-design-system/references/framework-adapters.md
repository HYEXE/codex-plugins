# 프레임워크별 적용 지침

공식 API와 설치 버전은 구현 시 다시 확인한다.

## React·Next.js

- server·client component 경계를 token과 presentational component 때문에 불필요하게 넓히지 않는다.
- ref, event, controlled state와 polymorphic API의 타입을 공개 계약으로 다룬다.
- headless primitive나 registry source를 추가하면 기존 provider, portal, hydration과 CSS order를 확인한다.

## Vue·Nuxt

- prop·emit·slot 계약과 attribute forwarding을 일관되게 둔다.
- composable과 component state의 소유권을 구분하고 SSR에서 browser-only theme 접근을 지연한다.
- scoped CSS가 semantic token cascade와 theme override를 가리지 않게 한다.

## Svelte·SvelteKit

- store·rune·component state를 설치된 Svelte 버전의 실제 패턴에 맞춘다.
- action과 transition cleanup, SSR-safe theme 초기화를 확인한다.
- React 전용 source를 번역하기보다 Svelte-native primitive와 작은 CSS 구현을 우선한다.

## Vanilla·Web Components

- CSS custom property를 안정적인 theming API로 사용하되 private implementation value까지 모두 노출하지 않는다.
- custom element의 attribute·property reflection, event, slot과 form association을 명시한다.
- shadow DOM을 쓰면 focus, label, global token과 high-contrast 전달 경계를 확인한다.

## 공통 완료 기준

- 같은 semantic token이 framework마다 다른 의미로 매핑되지 않는다.
- component 이름이 같으면 state와 keyboard contract도 같아야 한다.
- framework adapter가 core token source를 복제하지 않는다.
- 각 adapter는 독립적으로 build·typecheck·test되고 생성 산출물 drift가 없어야 한다.
