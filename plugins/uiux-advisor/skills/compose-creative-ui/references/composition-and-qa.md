# 외부 UI 조합과 QA

## 통합 계약

외부 component를 넣기 전에 다음을 적는다.

- 해결할 사용자·브랜드 문제
- 기존 foundation과 유지할 token
- 가져올 source와 component
- 새 dependency와 전역 변경
- 정상·hover·focus·active·disabled·loading·error 상태
- mobile·touch·keyboard·reduced-motion 대안
- 성능 budget과 제거 기준

## registry·copy-paste 코드 검토

1. 설치 명령을 바로 실행하지 말고 가능한 경우 registry payload나 source를 먼저 본다.
2. 생성·수정·삭제될 파일과 package를 확인한다.
3. `dangerouslySetInnerHTML`, 외부 URL, iframe, canvas·WebGL, event listener와 dynamic style injection을 찾는다.
4. global selector, CSS reset, theme variable와 z-index가 기존 system을 덮는지 본다.
5. demo-only content, remote asset, tracking, placeholder와 불필요한 dependency를 제거한다.
6. component를 제품 namespace, token, error handling과 test convention에 맞춘다.

## 상태와 접근성

- semantic element와 heading order를 유지한다.
- hover 효과에는 focus-visible과 touch 동작을 제공한다.
- card 전체 click과 내부 link·button의 nested interaction을 피한다.
- animated text는 보조기술에 중복 낭독되지 않게 하고 정적인 accessible name을 유지한다.
- decorative SVG, canvas와 background는 accessibility tree에서 불필요한 noise가 되지 않게 한다.
- dialog, menu, carousel와 tooltip을 시각 효과 source만 보고 채택하지 않는다. focus, keyboard와 announcement 계약을 검증한다.

## 반응형과 콘텐츠

- 320px급 작은 폭, zoom/reflow, 긴 한국어·영문, 큰 글자와 RTL을 확인한다.
- absolute position과 fixed height가 콘텐츠를 자르지 않게 한다.
- hero effect가 CTA, nav, cookie notice와 mobile browser chrome을 가리지 않게 한다.
- animation·background asset이 실패해도 콘텐츠와 행동은 남아 있어야 한다.

## 성능

- initial route에 필요하지 않은 effect는 lazy load 또는 사용자 viewport 진입 뒤 활성화한다.
- requestAnimationFrame loop, pointer listener와 observer를 shared 또는 scoped lifecycle로 관리한다.
- image·video·font·shader asset의 크기와 preload 우선순위를 확인한다.
- blur, filter, backdrop, box-shadow와 large gradient의 paint 비용을 실제 장치 조건에서 본다.
- offscreen, hidden tab와 reduced-motion 상태에서 반복 작업을 중지한다.

## 시각 QA

1. 효과 없는 base 상태
2. 정상·hover·focus·active·disabled
3. light·dark·high contrast
4. desktop·tablet·mobile·zoom
5. keyboard·touch·coarse pointer
6. reduced motion
7. slow asset·offline·error
8. long content·empty content
9. route transition과 back navigation
10. 낮은 성능과 background tab 복귀

## 완료 보고

- 채택한 component·registry와 역할
- 검토 후 제외한 후보와 이유
- 제품 token·content·state에 맞게 수정한 부분
- dependency, global style와 bundle 변화
- 실행한 자동·브라우저·접근성·성능 검증
- 라이선스, 장치, 보조기술과 브라우저의 미검증 범위
