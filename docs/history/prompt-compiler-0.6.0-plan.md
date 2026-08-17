# Prompt Compiler 0.6.0 Delta Orchestration

## 목표

0.5.0의 end-to-end 진입점을 유지하면서 다중 턴 후속 요청을 전체 재컴파일하지 않고 안전한 변경분만 반영한다.

## 범위

- 현재 작업의 목표·확정 제약·권한 상한·대기 질문·승인 대상을 압축한 task state capsule
- 후속 요청을 `continue`, `amend`, `replace`, `approve`, `cancel`로 분류
- `continue`·`amend`에서 영향받은 IR과 검증만 갱신하는 delta compilation
- 사용자 정정 시 충돌하는 가정·이전 산출물·검증 상태를 폐기하는 invalidation 규칙
- preview의 action·target·content가 바뀌면 승인을 다시 묶는 approval binding
- 새 목표와 취소 요청을 대기 중 요청에 섞지 않는 전환 경계
- 상태 캡슐을 사용자에게 기본 노출하지 않고 새 작업·대화 영속성을 주장하지 않는 사실적 경계
- 다중 턴 forward test와 회귀 평가, 공식 validator, 전체 통합 검증
- 플러그인 0.6.0 버전 갱신

## 완료 기준

- [x] 기존 0.5.0 미커밋 기준선과 검증 상태 확인
- [x] task state capsule과 delta compilation 규칙 구현
- [x] 정정·대체·취소·승인 무효화 회귀 사례 추가
- [x] 독립 다중 턴 forward test 수행
- [x] manifest, README, CHANGELOG와 공통 validator 갱신
- [x] 공식 skill·plugin validator와 전체 통합 검증
- [x] 전체 diff와 Git 상태 최종 검토
