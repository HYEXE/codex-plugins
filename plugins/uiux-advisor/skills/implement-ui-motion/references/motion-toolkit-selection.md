# 모션 도구 선택

공식 문서 확인 기준일: 2026-08-11

이 문서는 고정된 버전별 API 사본이 아니다. 구현할 때 프로젝트에 설치된 버전과 현재 공식 문서를 다시 확인한다.
구조화된 최신 후보 목록은 `../uiux-advisor/scripts/search_toolkits.py --role motion`으로 먼저 확인한다.

## 선택 전에 확인할 것

1. `package.json`, lockfile, framework와 렌더링 환경을 확인한다.
2. 이미 쓰는 animation package, CSS convention과 browser target을 찾는다.
3. 모션 계약에서 필요한 제어가 transition, timeline, layout, gesture, scroll, SVG 중 무엇인지 정한다.
4. 네이티브 API와 기존 도구로 충족되지 않을 때만 새 의존성을 고른다.

## 선택표

| 후보 | 우선 검토 상황 | 피할 상황 | 공식 자료 |
| --- | --- | --- | --- |
| CSS transitions/animations | hover, focus, reveal, 소수 속성의 상태 전환 | 여러 대상의 동적 timeline과 정밀한 재생 제어 | [MDN CSS animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Animations) |
| Web Animations API | dependency 없는 JS playback, cancel, reverse와 finished 상태 | framework의 layout·gesture 추상화가 핵심 | [MDN Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API) |
| View Transition API | DOM·문서·라우트 상태 사이의 시각적 연속성 | 지원 범위와 fallback을 수용할 수 없는 제품 | [MDN View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API) |
| Anime.js | 여러 대상, timeline, SVG, stagger, utility가 결합된 시퀀스 | 단순 transition 하나 때문에 dependency가 늘어나는 경우 | [Anime.js documentation](https://animejs.com/documentation/) |
| Motion | React·Vue 또는 JS 환경의 layout, gesture, spring, scroll과 선언형 조합 | 기존 stack과 adapter가 맞지 않거나 단순 CSS로 충분한 경우 | [Motion documentation](https://motion.dev/docs) |
| GSAP | 긴 timeline, 복잡한 scroll orchestration, 세밀한 playback 제어 | 짧은 상태 전환과 작은 bundle budget | [GSAP documentation](https://gsap.com/docs/v3/) |

## 판정 순서

1. 모션 없이도 상태 변화가 명확한가?
2. CSS로 완료·중단·반응형·reduced motion까지 처리 가능한가?
3. 브라우저 네이티브 API로 필요한 JS 제어를 제공할 수 있는가?
4. 기존 프로젝트 의존성이 요구 기능을 이미 제공하는가?
5. 새 라이브러리의 고유 기능이 dependency와 학습·유지보수 비용을 정당화하는가?

## 도구별 주의점

### Anime.js

- 현재 문서에서 import 경로와 사용 API를 확인한다. 오래된 예제의 전역 `anime` 호출을 그대로 복사하지 않는다.
- scope, animation과 timeline의 lifecycle을 컴포넌트 lifecycle에 연결한다.
- timeline callback을 비즈니스 상태의 유일한 진실 원본으로 만들지 않는다.
- SVG morph와 path animation은 축소·확대, reduced motion과 fallback을 함께 확인한다.

### Motion

- 프로젝트가 사용하는 React·Vue·vanilla API 문서를 구분한다.
- layout animation이 DOM semantics나 읽기 순서를 바꾸는 것처럼 보이지 않게 한다.
- gesture는 keyboard와 touch 대체 조작을 함께 제공한다.
- paid extension이나 별도 상품 기능이 필요한 예제를 기본 기능처럼 가정하지 않는다.

### GSAP

- core와 plugin의 역할, 등록 방법, 현재 라이선스 조건을 공식 자료에서 확인한다.
- ScrollTrigger를 scroll-jacking이나 핵심 정보 잠금에 사용하지 않는다.
- component unmount, route change와 development remount에서 timeline과 trigger를 정리한다.

### 네이티브 API

- progressive enhancement를 기본으로 두고 API 부재가 기능 실패로 이어지지 않게 한다.
- View Transition name 충돌, snapshot 범위와 브라우저 지원을 확인한다.
- WAAPI animation object를 보관해 cancel·reverse·finish와 cleanup을 명시적으로 처리한다.

## 의존성 도입 게이트

- 정확한 package 이름과 현재 버전
- 공식 문서와 저장소
- 라이선스와 유료 기능 경계
- tree-shaking, 번들 크기와 SSR 영향
- lockfile 변경과 transitively added package
- 프로젝트의 지원 browser·framework와의 호환성
- 제거 또는 교체 비용

위 항목을 확인할 수 없으면 추정으로 설치하지 말고 미검증 사항으로 보고한다.
