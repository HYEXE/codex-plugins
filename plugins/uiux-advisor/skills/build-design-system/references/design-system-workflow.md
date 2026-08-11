# 디자인 시스템 구축·이행 절차

## 1. 현재 상태 인벤토리

- token source와 생성 산출물, CSS variable, Tailwind theme, theme provider를 찾는다.
- 같은 역할의 color·spacing·radius·typography 값과 중복 component를 사용처 수와 함께 기록한다.
- package boundary, public export, application-local component와 외부 소비자를 구분한다.
- Storybook·문서와 실제 component API가 어긋나는지 확인한다.

## 2. 시스템 경계 결정

| 질문 | 결정 |
| --- | --- |
| 누가 소비하는가? | 단일 앱, 모노레포, 외부 package, 여러 platform |
| 진실 원본은 무엇인가? | CSS, JSON token, TypeScript, design tool export |
| 무엇을 생성하는가? | CSS variables, TS types, native platform values, docs |
| 누가 변경을 승인하는가? | owner, review rule, release process |
| 호환성을 어떻게 지키는가? | alias, deprecation, versioning, migration |

새 도구는 실제 소비자와 산출물이 둘 이상이거나 수동 동기화가 반복될 때 검토한다. 단일 웹 앱이면 CSS custom properties와 기존 build만으로 충분할 수 있다.

## 3. 점진적 구현

1. 가장 많이 쓰이는 의미 token과 한두 foundation component로 pilot을 만든다.
2. 기존 값과 새 token의 시각·행동 동등성을 fixture로 확인한다.
3. alias를 통해 소비자를 작은 묶음으로 이전한다.
4. 사용하지 않는 token과 component는 소비자 검색 뒤 별도 변경으로 제거한다.
5. system source와 생성 산출물이 CI에서 재현되는지 확인한다.

## 4. 변경·릴리스 계약

- breaking, deprecation, additive change 기준을 저장소의 versioning과 맞춘다.
- token rename은 값 변경과 구분하고, theme별 의미가 바뀌면 시각 회귀를 요구한다.
- generated file과 source file을 같은 리뷰에서 혼동하지 않게 한다.
- component 제거 전 대체 API, migration 예제와 종료 조건을 제공한다.

## 실패 신호

- 사용처 조사 없이 전역 token 이름을 일괄 교체한다.
- Figma 이름을 제품 의미 검토 없이 코드 API로 그대로 노출한다.
- 한 앱뿐인데 multi-platform generator와 package 배포 체계를 먼저 만든다.
- demo story만 있고 loading·error·focus·긴 콘텐츠 상태가 없다.
- 새 system과 기존 system이 장기간 이중 진실 원본으로 남는다.
