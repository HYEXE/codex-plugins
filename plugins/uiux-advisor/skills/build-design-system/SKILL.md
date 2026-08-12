---
name: build-design-system
description: 기존 코드베이스의 디자인 토큰, 테마, 컴포넌트 API, variant·state, 문서화와 회귀 검증을 하나의 시스템으로 설계·구현·마이그레이션한다. 사용자가 디자인 시스템이나 컴포넌트 라이브러리 구축·정리, CSS 변수·DTCG 토큰·Style Dictionary 파이프라인, Storybook 상태 문서, 다크 모드·브랜드 테마, 중복 컴포넌트 통합 또는 점진적 마이그레이션을 요청할 때 사용한다. 한 화면의 시각적 조합만 개선하면 compose-creative-ui를, 구현 없이 원칙이나 명세만 필요하면 uiux-advisor를, 기존 시스템 감사만 필요하면 uiux-auditor를 사용한다.
---

# Design System Builder

기존 제품의 언어와 API를 보존하면서 토큰, 컴포넌트, 문서와 검증이 같은 진실 원본을 공유하게 만든다. 새 라이브러리 도입보다 현재 시스템의 중복과 계약 공백을 먼저 해결한다.

## 시작 절차

1. 저장소 지침, 현재 diff, package와 lockfile, 스타일 도구, framework, build·test 명령을 확인한다.
2. 기존 CSS 변수, theme, token, primitive, component, Storybook·문서와 소비 경로를 검색해 실제 사용량을 기록한다.
3. 구현 전에 다음 시스템 계약을 작성한다.

   ```text
   소비자와 지원 platform:
   진실 원본과 생성 산출물:
   primitive·semantic·component token 계층:
   component API와 state 계약:
   theme·brand·dark mode 전략:
   호환성·버전·마이그레이션:
   문서·테스트·완료 기준:
   ```

4. 도구 후보가 필요하면 이 스킬 디렉터리를 기준으로 `../uiux-advisor/scripts/search_toolkits.py`에서 role과 ecosystem을 검색하고, 실제 도입 전 공식 문서를 다시 확인한다.
5. 시스템 경계와 점진적 이행은 `references/design-system-workflow.md`를 읽는다.
6. token·component API 설계는 `references/token-and-component-contracts.md`를 읽는다.
7. React·Vue·Svelte·vanilla 적용 차이는 `references/framework-adapters.md`를 읽는다.

## 구현 원칙

- primitive token을 제품 의미에 직접 노출하지 말고 semantic token을 안정적인 소비 계약으로 둔다.
- component token은 실제 반복과 독립적 변화 요구가 있을 때만 추가한다.
- color, spacing, typography만이 아니라 focus, motion, elevation, radius와 상태 표현도 계약에 포함한다.
- component API는 appearance와 behavior, content와 layout, controlled와 uncontrolled state를 구분한다.
- hover·focus·active·disabled·loading·error·empty·selected와 reduced-motion 상태를 문서와 테스트에 포함한다.
- 기존 공개 API와 token 이름을 한 번에 교체하지 않는다. alias, deprecation, codemod 또는 단계별 소비자 이전을 설계한다.
- 생성 산출물을 직접 편집하지 않는다. source token과 build pipeline의 소유권을 분명히 한다.
- Storybook, Style Dictionary나 새 package는 현재 프로젝트의 필요와 기존 도구로 해결할 수 없는 경우에만 추가한다.
- 웹 전용 시스템에서 불필요한 multi-platform pipeline을 만들지 않는다.

## 검증

1. token schema, alias cycle, 누락 reference, 생성물 재현성과 source/build drift를 검사한다.
2. component별 정상·경계·오류 상태와 keyboard, focus, screen reader, touch, zoom을 검증한다.
3. light·dark·고대비·브랜드 theme와 긴 콘텐츠, RTL, 작은 화면을 확인한다.
4. 관련 unit·interaction·visual regression, 타입 검사, 린트와 build를 실행한다.
5. 변경된 token과 component의 소비자를 찾아 호환성 영향과 migration 상태를 확인한다.
6. 추가 의존성, 번들·CSS 변화, 라이선스와 현재 지원 framework를 보고한다.

## 경계

- 디자인 시스템 원칙이나 token 계층을 설명만 하면 `uiux-advisor`를 사용한다.
- 기존 시스템의 문제를 식별하고 우선순위만 정하면 `uiux-auditor`를 사용한다.
- 한 화면의 hero, 배경, 카드와 텍스트 효과를 조합하면 `compose-creative-ui`를 사용한다.
- 단일 component의 시각 전환이 핵심이면 `implement-ui-motion`을 사용한다.
- 단일 widget의 keyboard, focus, touch, gesture와 비동기 상태 동작이 핵심이면 `implement-ui-interaction`을 사용한다.
- chart component의 데이터 의미와 시각 인코딩이 핵심이면 `build-data-visualization`을 사용한다.
