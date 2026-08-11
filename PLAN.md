# UI/UX Advisor 0.5.0 개선

## 목표

`uiux-advisor` 플러그인에 구조화된 프론트엔드 도구 선택 체계와 디자인 시스템 구현 역량을 추가한다.

## 범위

- 0.4.0 모션·데이터 시각화·창의적 UI 스킬을 Google Drive 저장소 작업 브랜치로 이전
- framework·역할·도입 방식·공식 문서·검토 상태를 기록하는 toolkit registry
- registry 검색 CLI와 schema·coverage 통합 검증
- `build-design-system`: token, theme, component API, Storybook, migration과 regression
- React·Vue·Svelte·vanilla framework adapter
- 기존 advisor·auditor·구현 스킬과 신규 스킬의 라우팅 경계
- 플러그인 0.5.0 버전과 설치 cache 검증

## 완료 기준

- [x] 더티한 Google Drive main을 보존하고 별도 worktree에 0.4.0 이전
- [x] toolkit registry와 검색 CLI 구현
- [x] build-design-system 구조와 참조 구현
- [x] manifest, README, validator와 라우팅 평가 연결
- [x] 포워드 테스트와 공식 skill·plugin validator 통과
- [x] 임시 marketplace 설치와 source/cache 동일성 확인
- [x] 전체 diff 검토와 커밋 품질 게이트 준비
