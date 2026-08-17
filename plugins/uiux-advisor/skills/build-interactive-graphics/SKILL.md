---
name: build-interactive-graphics
description: 기존 프론트엔드에 Rive 상태 머신, PixiJS 2D canvas, Three.js·React Three Fiber 3D, Theatre.js 연출을 실제로 구현하고 정적·DOM 폴백, 접근성, 렌더 루프, 자원 정리와 성능 예산을 검증한다. 사용자가 반응형 벡터 캐릭터, 노드 캔버스, 제품 3D 뷰어, 상태 연동 그래픽 또는 타임라인 기반 시각 장면을 코드로 만들어 달라고 할 때 사용한다. DOM 위젯의 키보드·포커스·제스처는 implement-ui-interaction을, 실제 비동기 작업 수명주기는 implement-async-ui-state를, 시간 기반 DOM 모션은 implement-ui-motion을, 데이터 인코딩은 build-data-visualization을, 화면 구성은 compose-creative-ui를 사용한다.
---

# Interactive Graphics Builder

시각적 임팩트보다 사용자 과업, 대체 경로와 실제 렌더링 비용을 먼저 고정한다. 일반 DOM·CSS로 동일한 결과를 더 단순하게 낼 수 있으면 고급 그래픽 런타임을 도입하지 않는다.

## 시작 절차

1. 저장소 지침, 현재 diff, framework·renderer·package manager·browser 범위·테스트 도구와 기존 그래픽 의존성을 확인한다.
2. 현재 화면과 산출물 형식을 관찰하고, 보지 못한 WebGL·canvas·Rive 동작을 성공했다고 단정하지 않는다.
3. 주 결과를 분류한다.

   - `state-vector`: 상태 기반 벡터 캐릭터·아이콘·설명 그래픽
   - `dense-two-dimensional`: 다수 object·particle·sprite가 있는 2D canvas
   - `three-dimensional`: camera·light·material·model·raycast가 필요한 3D
   - `authored-sequence`: designer-authored timeline을 런타임 상태와 연결하는 연출

4. 실패·비지원·reduced-motion에서도 유지할 정적·DOM 결과와 성공 기준을 먼저 적는다.
5. `references/graphics-toolkit-selection.md`로 도구를 선택하고, `references/graphics-accessibility-and-fallback.md`와 `references/render-loop-performance-and-qa.md`를 적용한다.
6. 지식·API·license·browser 지원이 바뀐 가능성이 있으면 현재 공식 자료와 설치된 버전을 확인한다.

## 구현 계약

```text
사용자 과업과 완료 상태:
그래픽이 표현할 상태·입력·출력:
semantic DOM과 보조기술 경계:
키보드·터치·직접 입력 대체 경로:
정적·DOM·모션 감소 fallback:
초기 로드·asset·frame·memory 예산:
시작·일시정지·재개·정리 lifecycle:
WebGL·canvas·asset 실패 복구:
성공·반증 기준과 실측 환경:
```

## 도구 선택

- Rive는 디자이너가 제작한 벡터 상태 머신과 런타임 입출력이 실제 요구일 때 검토한다. 단순 loader·icon 모션은 CSS·SVG·Anime.js로 더 가볍게 해결하는지 먼저 비교한다.
- PixiJS는 다수를 반복 렌더링하는 2D scene에 사용한다. 일반 form·card·navigation을 canvas로 만들지 않는다.
- Three.js는 framework 비종속 3D 제어가 필요할 때, React Three Fiber는 React lifecycle·state·composition이 실제 이득일 때 선택한다. Drei는 R3F 선택 후 필요한 helper만 쓴다.
- Theatre.js는 수작업 timeline authoring과 런타임 state 연결이 필수일 때만 추가한다. 일반 transition 코드의 대체로 추가하지 않는다.
- 기존에 적합한 renderer·asset pipeline이 있으면 새 의존성을 추가하지 않는다. 도입 전 current API, license, bundle, SSR·hydration, accessibility, 제거 비용을 확인한다.

## 핵심 구현 규칙

- canvas·WebGL은 시각 표현을 담고, heading·label·button·form·오류·현재 상태와 핵심 제어는 semantic DOM으로 보존한다.
- hover·drag·orbit·pinch만으로 핵심 과업을 완료하게 하지 않고 button·keyboard·direct input 경로를 제공한다.
- `prefers-reduced-motion`에서 반복, parallax, camera travel과 큰 공간 이동을 줄이되 상태·내용·제어를 제거하지 않는다.
- 그래픽 초기화 전과 실패 후에도 정적 image·poster·DOM 요약과 핵심 action을 제공한다.
- viewport 밖, background tab과 route 이동 중에는 불필요한 render loop·timer·asset work를 멈춘다. 이벤트 기반 렌더로 충분하면 지속 loop를 두지 않는다.
- unmount·route change·asset 교체에서 animation frame, listener, observer, geometry, material, texture, renderer과 context를 소유자가 정리한다.
- DPR·particle count·shadow·post-processing·model LOD는 보편 상수로 단정하지 않고 대상 기기 실측과 적응 규칙으로 제한한다.

## 검증

1. 관련 unit·interaction 테스트, type check, lint·build를 실행한다.
2. 실제 브라우저에서 초기, loading, ready, interaction, error, context loss·asset failure, retry·fallback, unmount를 확인한다.
3. mouse, keyboard, touch·coarse pointer, zoom·reflow, reduced motion과 그래픽 비지원 환경의 동등한 과업 완료를 확인한다.
4. 초기 전송량, 최대 asset, main-thread·GPU frame 비용, memory 증가와 Web Vitals를 적용 범위에서 실측한다. 측정하지 않은 성능 향상을 주장하지 않는다.
5. 새 의존성은 lockfile, transitive dependency, license, bundle split, SSR·hydration과 사용되지 않은 import를 검토한다.
6. 채택·제외 도구, fallback, 실행한 검증, 실측 환경과 미검증 조합을 보고한다.

## 경계

- Dialog·Popover·Carousel·drag·gesture의 DOM 입력·포커스 계약이 주 결과면 `implement-ui-interaction`을 사용한다.
- agent·tool 실행의 비동기 작업 수명주기가 주 결과면 `implement-async-ui-state`를 사용한다. Rive가 그 상태를 표현하는 것이 핵심이면 두 스킬의 계약을 함께 적용한다.
- easing·timeline·scroll choreography가 있더라도 DOM 모션이 주 결과면 `implement-ui-motion`을 사용한다.
- 값을 위치·길이·색·면적으로 인코딩해 분석하는 것이 주 목적이면 `build-data-visualization`을 사용한다.
- hero·card·background·text effect의 시각 조합이 주 결과면 `compose-creative-ui`를 사용한다.
- 설명·대안 비교·명세만 필요하면 `uiux-advisor`, 기존 결과의 결함 감사만 필요하면 `uiux-auditor`를 사용한다.
