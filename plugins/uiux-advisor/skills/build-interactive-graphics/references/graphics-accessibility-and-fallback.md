# Graphics Accessibility and Fallback

## 정보와 제어

- canvas·WebGL 장면이 장식이면 보조기술에서 중복 내용을 노출하지 않는다.
- 정보를 전달하면 동일한 핵심 의미를 DOM 텍스트·표·목록으로 제공한다.
- 제어가 있으면 semantic button·input·label, keyboard order, 보이는 focus와 현재 상태를 DOM에서 관리한다.
- 색, 움직임, 깊이와 pointer 위치 하나만으로 상태를 전달하지 않는다.

## 대체 계층

1. 완전한 interactive renderer
2. 모션을 줄이고 품질을 제한한 renderer
3. 정적 poster·image·SVG + semantic DOM 내용·제어
4. asset도 실패한 경우 DOM 요약·오류·재시도·대체 이동

fallback은 클라이언트 예외 후 빈 캔버스를 가리는 장식이 아니다. JavaScript 비활성, asset timeout, decoder·WebGL 비지원, context loss와 성능 열화에서도 핵심 과업을 마칠 수 있어야 한다.

## 모션 감소

- 모션 감소 설정에서 autoplay, 반복, camera travel, parallax, shake와 과한 심도 변화를 제거·축소한다.
- 상태 변경은 즉시 또는 단순한 opacity·color 변경과 텍스트로 유지한다.
- 사용자가 일시정지·재생·다시 보기를 제어해야 하는 긴 연출은 보이는 제어를 제공한다.
