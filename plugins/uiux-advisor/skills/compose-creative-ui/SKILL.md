---
name: compose-creative-ui
description: 기존 프론트엔드의 정체성과 디자인 시스템을 보존하면서 shadcn/ui registry, Magic UI, Aceternity UI, React Bits, Radix, Base UI, React Aria, Ark UI 등 호환 가능한 컴포넌트·시각 효과 도구를 선별해 화면 구성 자체를 구현·검증한다. 사용자가 랜딩 페이지, hero, 배경, 카드, bento, 텍스트 효과나 밋밋한 화면의 시각적 조합 개선을 요청할 때 사용한다. 시간·공간 변화는 implement-ui-motion을, 키보드·포커스·제스처·상태 동작은 implement-ui-interaction을, 공유 시스템은 build-design-system을, 조언은 uiux-advisor를, 감사는 uiux-auditor를 사용한다.
---

# Creative UI Composer

라이브러리 데모를 복제하거나 여러 시각 효과를 쌓는 대신, 제품의 메시지와 사용자 과업을 강화하는 소수의 표현을 기존 코드에 통합한다.

## 시작 절차

1. 저장소 지침과 현재 diff를 확인하고 프레임워크, 렌더링 방식, 스타일 도구, 패키지 관리자, `components.json`, 기존 component primitive와 디자인 token을 읽는다.
2. 현재 화면을 실행하거나 코드로 확인해 정보 위계, 브랜드 단서, 핵심 과업과 실제로 단조로운 지점을 찾는다.
3. 다음 표현 계약을 고정한다.

   ```text
   강화할 메시지·과업:
   유지할 제품 정체성:
   적용할 위치와 효과 수:
   base component와 accent source:
   interaction·responsive·reduced-motion 상태:
   성능·접근성·콘텐츠 위험:
   성공·제거 기준:
   ```

4. `../uiux-advisor/scripts/search_toolkits.py --role creative-ui --ecosystem <ecosystem>`으로 구조화 후보를 좁힌다.
5. `references/component-toolkit-selection.md`를 읽고 현재 프레임워크와 목적에 맞는 후보를 고른다.
6. registry·copy-paste 코드 통합과 QA는 `references/composition-and-qa.md`를 읽어 적용한다.

## 조합 원칙

- 기존 foundation이 있으면 유지한다. 새 foundation으로 전면 교체하지 않고 필요한 primitive나 accent만 추가한다.
- foundation, data visualization, motion, decorative registry의 역할을 구분한다.
- 한 화면에서는 기본 시스템 하나와 제한된 accent source를 중심으로 조합한다. 다른 라이브러리의 spacing, radius, typography와 state를 그대로 섞지 않는다.
- 효과를 선택하기 전에 “이 표현이 무엇을 더 빨리 이해하거나 행동하게 만드는가?”에 답한다.
- hero와 마케팅 영역의 장식 규칙을 form, settings, checkout 같은 과업 중심 화면에 그대로 적용하지 않는다.
- React 전용 도구를 Vue·Svelte 프로젝트에 억지로 이식하지 않는다. 해당 생태계의 primitive 또는 작은 네이티브 구현을 선택한다.

## 외부 코드 도입 규칙

1. 공식 문서와 실제 설치 대상의 현재 API를 확인한다.
2. package와 registry item의 소스, transitively added dependency, 스타일 전역 변경, 라이선스와 유지보수 상태를 확인한다.
3. shadcn-compatible registry는 설치 전에 가능한 경우 `view` 명령으로 payload를 읽는다. 커뮤니티 registry를 신뢰된 코드로 간주하지 않는다.
4. 가져온 컴포넌트의 DOM semantics, focus, keyboard, touch, resize, reduced motion, SSR와 hydration 동작을 직접 검토한다.
5. 사용하지 않는 variant, effect, dependency와 demo copy를 제거하고 제품 token·content·상태 모델에 맞게 변경한다.
6. 유료 template나 제한된 asset을 권한 확인 없이 복사하지 않는다.

## 구현 규칙

- 정보 위계, 콘텐츠와 상태를 먼저 완성한 뒤 배경·빛·입자·3D·pointer 효과를 추가한다.
- glow, blur, gradient, glass, bento와 marquee를 기본 스타일처럼 반복하지 않는다. 제품 맥락에 맞는 시각 문법을 선택한다.
- hover 전용 공개 정보나 pointer 추적만으로 가능한 핵심 행동을 만들지 않는다.
- 자동 반복, parallax, 3D tilt와 text animation은 reduced-motion에서 정적 표현으로 바꾼다.
- 장식 layer는 콘텐츠의 contrast, hit target, selection, scroll과 focus ring을 방해하지 않게 한다.
- image, canvas, shader, video와 particle 효과는 작은 화면·저전력 환경에서 지연 로드 또는 단순 대안을 제공한다.
- 기존 컴포넌트 API, theme, dark mode와 responsive breakpoint를 불필요하게 바꾸지 않는다.

## 검증

1. 관련 테스트, 타입 검사, 린트와 빌드를 실행한다.
2. 실제 브라우저에서 주요 viewport, 확대, dark mode, keyboard, touch와 reduced motion을 확인한다.
3. loading, error, empty, 긴 콘텐츠와 느린 asset 상태에서 시각 효과가 과업을 가리지 않는지 본다.
4. 새 의존성, registry source, 전역 CSS와 bundle 변화를 검토한다.
5. 콘솔 오류, hydration mismatch, layout shift, long task와 낮은 성능 환경을 확인한다.
6. 채택·제외한 도구와 이유, 제품에 맞게 바꾼 부분, 접근성·성능 검증과 미검증 항목을 보고한다.

## 경계

- 시각 방향과 컴포넌트 원칙만 비교하면 `uiux-advisor`를 사용한다.
- 기존 결과의 문제만 식별하면 `uiux-auditor`를 사용한다.
- 배경, 콘텐츠 블록, 카드나 텍스트 효과를 조합해 화면 구성을 개선하는 것이 주목적이면 이 스킬을 사용한다.
- hover·press·열기·닫기의 시각 전환 하나가 주목적이면 `implement-ui-motion`을 사용한다.
- keyboard, focus, touch, gesture와 비동기 상태가 정확한 widget 동작이 주목적이면 `implement-ui-interaction`을 사용한다.
- 여러 화면이 공유하는 token, theme, component API와 문서화를 구축하면 `build-design-system`을 사용한다.
- 복잡한 timeline, scroll 또는 SVG 모션을 직접 구현하면 `implement-ui-motion`을 함께 적용한다.
- 데이터 의미와 chart encoding이 중심이면 `build-data-visualization`을 사용한다.
