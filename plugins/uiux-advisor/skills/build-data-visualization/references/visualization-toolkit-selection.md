# 데이터 시각화 도구 선택

공식 문서 확인 기준일: 2026-08-11

라이브러리 API와 설치 방식은 변할 수 있다. 구현할 때 설치 버전과 현재 공식 문서를 확인한다.

## 도구보다 먼저 정할 것

- 사용자가 답해야 하는 질문: 비교, 순위, 추세, 분포, 관계, 흐름, 지리 또는 구성
- 데이터 규모와 갱신 빈도
- React·Vue·Svelte·vanilla 등 현재 framework
- SVG, Canvas, WebGL과 SSR 요구
- keyboard·screen reader·touch와 표 대안
- 기존 디자인 token과 차트 dependency

## 선택표

| 후보 | 적합한 상황 | 주요 전제·주의 | 공식 자료 |
| --- | --- | --- | --- |
| 텍스트·표·네이티브 SVG | 소수 값, 정확한 조회, 작은 사용자 정의 표현 | 차트가 실제 이해를 개선하는지 먼저 판단 | [WAI complex images tutorial](https://www.w3.org/WAI/tutorials/images/complex/) |
| Bklit UI | shadcn/ui 기반 React 대시보드, 디자인된 차트 조합과 registry workflow | shadcn 설정, registry payload와 추가 dependency 확인 | [Bklit UI docs](https://bklit.com/docs), [설치](https://bklit.com/docs/installation), [공식 skill 설명](https://bklit.com/docs/skills) |
| Recharts | React에서 일반적인 선언형 line, bar, area, pie와 조합 | 기존 버전의 API·반응형·접근성 보완을 실제로 확인 | [Recharts guide](https://recharts.github.io/en-US/guide/) |
| Apache ECharts | 많은 chart type, Canvas, 복합·지도·대규모 대화형 시각화 | 필요한 module만 import하고 ARIA·formatter 보안을 별도 설정 | [ECharts handbook](https://echarts.apache.org/handbook/en/get-started/), [ARIA](https://echarts.apache.org/handbook/en/best-practices/aria/), [보안](https://echarts.apache.org/handbook/en/best-practices/security/) |
| Observable Plot | 탐색적 분석, tabular data, concise layered grammar | 제품 component 통합과 interaction 수준을 확인 | [Observable Plot](https://observablehq.github.io/plot/) |
| D3 | 표준 chart abstraction 밖의 맞춤 encoding, layout와 interaction | low-level 제어 비용, DOM lifecycle와 접근성 직접 구현 | [D3 documentation](https://d3js.org/getting-started) |

## Bklit UI 적용 순서

1. React와 shadcn/ui 사용 여부, `components.json`, Tailwind와 alias를 확인한다.
2. 현재 Bklit 공식 문서에서 필요한 chart와 registry command를 찾는다.
3. 가능한 경우 shadcn CLI의 project info와 registry item view를 먼저 실행한다.
4. component source와 dependency가 기존 Recharts·theme·utility와 충돌하는지 확인한다.
5. chart CSS variable을 기존 semantic token에 매핑한다.
6. demo data, animation과 tooltip을 실제 제품 상태 계약으로 교체한다.

## 선택 실패 신호

- 정확한 수치 조회 과업인데 hover tooltip만 제공한다.
- 데이터가 작고 정적인데 대형 chart runtime을 추가한다.
- 기존 chart package가 충분한데 시각 스타일만을 위해 두 번째 engine을 추가한다.
- 데이터가 많아 DOM node가 폭증하거나 resize마다 전체 chart를 재생성한다.
- map, sankey, network 같은 특수 chart를 익숙해 보인다는 이유만으로 쓴다.
- 색상·animation·3D가 데이터 차이보다 더 강하게 읽힌다.

## 최신성·권리 확인

- package version, peer dependency와 framework support
- 공식 docs와 실제 import path
- license, 상업 사용과 유료 component 경계
- registry에서 복사되는 source와 asset의 권리
- maintenance, security advisory와 release state
- server rendering과 browser support

확인되지 않은 항목은 일반 지식으로 단정하지 않고 미검증으로 남긴다.
