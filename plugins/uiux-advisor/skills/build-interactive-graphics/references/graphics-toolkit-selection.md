# Graphics Toolkit Selection

## 선택 순서

1. DOM, CSS, SVG가 과업·상태·시각 표현을 충분히 달성하는지 확인한다.
2. 기존 renderer·asset pipeline·component·dependency를 재사용한다.
3. `uiux-advisor/scripts/search_toolkits.py --role interactive-graphics --ecosystem <ecosystem> --recommend --max-risk high`로 후보를 확인한다.
4. 현재 공식 문서, 설치 버전, license·bundle·browser·SSR·asset 파이프라인을 확인한다.

## 역할별 적합성

| 도구 | 적합한 조건 | 선택하지 않을 조건 | 기본 fallback |
| --- | --- | --- | --- |
| Rive | designer-authored 벡터 state machine, runtime input·event | 단순 SVG·CSS 모션, 내용·제어를 canvas에만 숨김 | 정적 SVG·image + DOM 상태 |
| PixiJS | 다수 sprite·particle·object의 2D scene | 일반 form·card·table·navigation | static canvas·image + DOM 제어 |
| Three.js | framework 비종속 3D scene·camera·material 제어 | 2D illustration, 정적 제품 image로 충분 | poster·gallery·model 설명 |
| React Three Fiber | React state·lifecycle·composition이 필요한 3D | React와 무관하거나 imperative engine이 더 단순 | Three.js와 같은 정적·DOM fallback |
| Drei | R3F의 확인된 helper가 구현 비용을 실제로 줄임 | 사용하지 않는 helper 묶음 도입 | 직접 R3F·Three 구현 |
| Theatre.js | authored timeline, 런타임 state·sequence 편집 | 일반 hover·enter·exit transition | 단순 state transition·정적 scene |

## 조합 규칙

- renderer는 한 scene에 하나를 원칙으로 한다. Rive, PixiJS, Three.js를 같은 표현에 중첩하지 않는다.
- R3F + Drei, R3F + Theatre.js 같은 조합은 각 도구의 소유 lifecycle과 제거 순서를 적는다.
- interaction state를 renderer 내부와 application state에 중복 소유하지 않고, 한 쪽을 진실 원본으로 정한다.
- asset·renderer·timeline 중 하나만 실패해도 대체 경로로 전환할 수 있게 경계를 나눈다.
