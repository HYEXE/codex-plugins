---
name: build-data-visualization
description: 데이터와 사용자 과업에 맞는 차트·시각화 표현을 정하고 Bklit UI, Recharts, Apache ECharts, Observable Plot, D3 또는 기존 도구로 실제 프론트엔드에 구현·검증한다. 사용자가 대시보드 차트, 분석 화면, 실시간·대용량 시각화, 지도·네트워크·사용자 정의 그래픽, Bklit UI 설치·활용이나 접근 가능한 데이터 표현을 요청할 때 사용한다. 원칙 설명·명세만 필요하면 uiux-advisor를, 기존 차트 감사만 필요하면 uiux-auditor를 사용한다.
---

# Data Visualization Builder

차트 유형이나 라이브러리보다 사용자가 찾아야 하는 비교, 추세, 분포, 관계와 이상치를 먼저 고정한다. 시각화와 동등한 핵심 정보에 텍스트 또는 표로 접근할 수 있게 한다.

## 시작 절차

1. 저장소 지침, 프레임워크, 렌더링 환경, 패키지 관리자, 기존 디자인 token과 차트 의존성을 확인한다.
2. 데이터의 출처, 단위, 시간대, 표본, 결측·0·음수·극단값, 갱신 주기와 최대 규모를 확인한다. 실제 데이터를 볼 수 없으면 가정과 fixture를 명시한다.
3. 다음 시각화 계약을 작성한다.

   ```text
   사용자 질문과 결정:
   데이터 차원·측정값·단위:
   주 시각 인코딩:
   비교 기준·정렬·필터:
   loading·empty·error·partial·stale 상태:
   텍스트 요약·표 대안:
   키보드·터치·모션 감소:
   성공·반증 기준:
   ```

4. `../uiux-advisor/scripts/search_toolkits.py --role data-visualization --ecosystem <ecosystem>`으로 구조화 후보를 확인한다.
5. `references/visualization-toolkit-selection.md`를 읽고 가장 작은 적합 도구를 고른다.
6. 접근성·상태·QA 기준은 `references/chart-contract-and-qa.md`를 읽어 적용한다.

## 도구 선택 규칙

- 단순한 수치와 한두 비교는 차트 대신 텍스트, progress 또는 표가 더 명확한지 먼저 판단한다.
- shadcn/ui 기반 React 프로젝트에서 완성도 높은 차트 조합이 필요하면 Bklit UI를 검토한다.
- 기존 React 프로젝트의 일반적인 선언형 차트는 이미 사용 중인 Recharts 같은 도구를 우선한다.
- 많은 시리즈, Canvas 렌더링, 복합·지도·대화형 시각화가 필요하면 Apache ECharts를 검토한다.
- 탐색적 분석과 간결한 grammar-of-graphics 조합에는 Observable Plot을 검토한다.
- 표준 라이브러리의 추상화로 표현하기 어려운 사용자 정의 시각 인코딩과 상호작용에만 D3를 직접 사용한다.
- 사용자 지정 그래픽이 작으면 SVG·Canvas·CSS의 네이티브 구현도 후보로 둔다.

Bklit UI는 shadcn/ui registry와 프로젝트 구성이 전제다. 설치 전에 `components.json`, 현재 shadcn 설정과 registry payload를 확인하고 가져오는 소스·의존성·라이선스를 검토한다.

## 구현 규칙

- 축, 단위, 기준선, 범례와 tooltip이 같은 의미를 전달하게 한다.
- 색상만으로 계열과 상태를 구분하지 않는다. label, shape, pattern, stroke 또는 직접 표기를 조합한다.
- tooltip에만 핵심 값을 숨기지 않는다. 키보드·터치에서도 같은 정보를 얻거나 표 대안을 사용할 수 있게 한다.
- 0과 결측값, 데이터 없음과 로딩 실패, 잠정치와 확정치를 구분한다.
- locale, 숫자·날짜·시간대 포맷과 RTL을 제품 규칙에 맞춘다.
- 축 범위 축소, 이중 축, 3D, 면적·크기 인코딩이 오해를 만들 수 있으면 기본값으로 사용하지 않는다.
- enter animation과 실시간 업데이트는 데이터 해석을 방해하지 않게 하고 reduced-motion 대안을 제공한다.
- 시각화가 컨테이너 크기 변화와 확대에서 잘리지 않게 하며 작은 화면에서는 정보 우선순위를 재구성한다.
- 외부 데이터가 tooltip HTML, 링크 또는 formatter로 들어가면 escape·sanitization 경계를 확인한다.

## 검증

1. 정상 데이터와 함께 empty, loading, error, partial, stale, 단일값, 동일값, 음수, 극단값과 긴 label fixture를 확인한다.
2. 관련 단위 테스트, 타입 검사, 린트와 빌드를 실행한다.
3. 실제 브라우저에서 반응형, 확대, dark mode, 키보드, touch와 reduced motion을 확인한다.
4. 시각값과 표·텍스트 값이 원본 데이터와 일치하는지 검산한다.
5. 큰 데이터셋과 업데이트 빈도에서 main-thread, 메모리, resize와 animation 비용을 측정한다.
6. 선택한 도구, 추가된 의존성, 데이터 가정, 접근 가능한 대안, 검증 결과와 미검증 항목을 보고한다.

## 경계

- 차트 유형과 UX 원칙만 비교하는 요청은 `uiux-advisor`로 보낸다.
- 기존 대시보드의 문제를 찾고 우선순위화하는 요청은 `uiux-auditor`로 보낸다.
- 여러 제품 화면이 공유하는 chart token과 component API를 시스템화하면 `build-design-system`을 함께 적용한다.
- 차트 밖의 페이지 배경, hero, 카드와 텍스트 효과 조합은 `compose-creative-ui`를 사용한다.
- 시각화 전이의 복잡한 타임라인 구현은 `implement-ui-motion`의 모션 계약도 적용한다.
- canvas·map·network의 gesture, keyboard와 focus 동작 구현은 `implement-ui-interaction`의 입력 계약도 적용한다.
