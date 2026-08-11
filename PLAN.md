# UI/UX Advisor 프론트엔드 도구 확장

## 목표

`uiux-advisor` 플러그인에 모션, 데이터 시각화와 창의적 UI 조합을 실제 코드로 구현·검증하는 독립 스킬을 추가한다.

## 범위

- `implement-ui-motion`: CSS, WAAPI, View Transition, Anime.js, Motion, GSAP
- `build-data-visualization`: Bklit UI, Recharts, ECharts, Observable Plot, D3
- `compose-creative-ui`: shadcn-compatible registry, Magic UI, Aceternity UI, React Bits와 headless primitive
- 기존 advisor·auditor와 신규 구현 스킬의 라우팅 경계
- 플러그인 0.4.0 메타데이터, 통합 검증과 설치 캐시 검증

## 완료 기준

- [x] 신규 스킬 구조와 역할 경계 정의
- [x] 공식 자료 기반 도구 선택·QA 참조 작성
- [x] manifest, README와 정적 검증기 연결
- [x] 신규 스킬별 라우팅 케이스 5개 이상 추가
- [x] 공식 skill·plugin validator와 저장소 통합 검증 통과
- [x] 임시 marketplace 설치와 source/cache 동일성 확인
- [x] 전체 diff 검토와 커밋 품질 게이트 준비
