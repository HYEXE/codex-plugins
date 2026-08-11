# 토큰과 컴포넌트 계약

공식 자료 확인 기준일: 2026-08-11

## 토큰 계층

| 계층 | 예 | 역할 |
| --- | --- | --- |
| primitive | blue-600, space-4 | 원시 palette와 scale |
| semantic | color-action-primary, space-layout-gap | 제품 의미와 theme 안정성 |
| component | button-background-primary | 독립적 변화가 반복되는 component 범위 |

- alias 방향은 component → semantic → primitive로 유지한다.
- state와 mode를 token 이름에 무제한 결합하지 말고 theme 구조와 component variant로 분리한다.
- token type, value, description과 deprecation 정보를 검증 가능한 형태로 둔다.
- 교환 형식이 필요하면 [DTCG Format](https://www.designtokens.org/tr/drafts/format/)의 현재 stable·draft 상태와 사용 도구의 지원 범위를 확인한다.
- 여러 platform 변환이 실제 요구면 [Style Dictionary](https://styledictionary.com/getting-started/installation/) 같은 build tool을 검토한다.
- 웹 runtime 소비는 [CSS Custom Properties](https://www.w3.org/TR/css-variables-1/)와 fallback·cascade 경계를 명시한다.

## 컴포넌트 계약

각 공개 component는 다음을 가진다.

- semantic element와 접근 가능한 name
- size·tone·emphasis 같은 제한된 variant
- controlled·uncontrolled state와 event contract
- normal, hover, focus-visible, active, disabled, loading, error와 selected 상태
- keyboard, pointer, touch와 focus 이동
- responsive, 긴 콘텐츠, locale·RTL
- reduced-motion과 고대비 대안
- public import path와 deprecation 정책

DOM 구조나 class name을 공개 API로 암묵적으로 고정하지 않는다. slot이나 render prop이 필요하면 의미와 focus contract를 깨지 않는 범위로 제한한다.

## 문서와 테스트

[Storybook](https://storybook.js.org/docs/get-started/why-storybook) 같은 격리 환경은 이미 사용 중이거나 component variation을 재현·검증하는 비용을 줄일 때 채택한다.

- 문서는 props 목록만이 아니라 사용·금지 조건과 콘텐츠 지침을 포함한다.
- story와 fixture는 실제 state matrix의 실행 가능한 표본이어야 한다.
- interaction, accessibility와 visual regression을 역할별로 분리한다.
- snapshot 하나만으로 focus, keyboard, async와 responsive contract를 검증했다고 보지 않는다.
