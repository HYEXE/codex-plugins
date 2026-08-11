# 차트 계약과 QA

## 의미 계약

| 영역 | 필수 확인 |
| --- | --- |
| 데이터 | 출처, 단위, 표본, 시간대, 갱신 시점, 결측과 잠정치 |
| 질문 | 사용자가 비교·탐색·판단할 대상 |
| 인코딩 | position, length, color, area, shape가 뜻하는 값 |
| 기준 | 정렬, baseline, 축 범위, normalization과 필터 |
| 상태 | loading, empty, error, partial, stale와 permission |
| 대안 | 핵심 요약, 전체 또는 핵심 데이터 표, export |
| 조작 | keyboard, touch, pointer, zoom, pan과 reset |

## 접근성

- chart 앞뒤의 title과 summary로 주제, 기간, 단위와 핵심 추세를 설명한다.
- interactive point가 많으면 모든 점을 무조건 tab stop으로 만들지 말고 구조화된 탐색이나 표 대안을 설계한다.
- color 외에 label, pattern, shape, stroke와 직접 표기를 사용한다.
- legend와 filter가 keyboard로 조작되고 현재 상태를 노출하게 한다.
- tooltip trigger와 내용이 focus, touch와 screen reader 경로에서 동등한지 확인한다.
- animation을 제거해도 최신 값, 변경 방향과 selection을 이해할 수 있어야 한다.

자동 생성 ARIA 설명은 출발점일 뿐이다. 실제 사용자 질문과 핵심 insight를 대신하는 것으로 간주하지 않는다.

## 상태 fixture

최소한 다음 데이터를 준비한다.

1. 일반 데이터
2. 빈 배열과 null
3. loading과 request error
4. 부분 응답과 stale cache
5. 단일 point와 모든 값 동일
6. 0, 음수와 극단값
7. 긴 label, 다국어와 RTL
8. 많은 series와 큰 dataset
9. 잘못되거나 예상 밖의 category
10. 시간대·DST 경계를 지나는 시계열

## 시각적 검산

- source data의 최소·최대·합계와 화면 값을 직접 대조한다.
- 축 tick, tooltip, label과 summary의 formatter가 같은 단위·반올림 규칙을 사용하게 한다.
- filter 전후 denominator와 aggregation이 바뀌는지 표시한다.
- truncated axis나 broken scale이 차이를 과장하지 않는지 확인한다.
- responsive 축약으로 series, 단위 또는 경고가 사라지지 않는지 본다.

## 성능과 보안

- 데이터 크기와 update frequency를 실제 최대치 또는 현실적인 fixture로 측정한다.
- hidden chart와 offscreen animation을 중지한다.
- resize observer loop, stale instance와 event listener leak을 확인한다.
- 외부 문자열을 HTML tooltip이나 formatter에 넣을 때 escape·sanitization을 확인한다.
- export되는 CSV, SVG와 image에도 민감 정보와 injection 경계가 있는지 본다.

## 완료 보고

- 사용자 질문과 선택한 chart·도구
- 데이터 가정과 변환
- 접근 가능한 summary·table·interaction
- loading·empty·error·partial 상태
- 실행한 데이터 검산, 자동 테스트, 브라우저·성능 검증
- 미검증 데이터 규모, locale, 보조기술과 브라우저
