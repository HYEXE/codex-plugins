# Minimal Task Graph

실질적인 dependency 또는 multi-capability coordination이 필요할 때만 Task Graph를 사용한다.

## 목적

Task Graph는 프로젝트 관리 문서가 아니라 실행 IR이다.

다음을 명확하게 하기 위한 것이다.

- 무엇을 해야 하는가
- 무엇이 무엇에 의존하는가
- 무엇을 독립적으로 실행할 수 있는가
- permission boundary가 어디에 있는가
- 검증이 어디서 필요한가

## Node Schema

필요한 경우 다음 field를 사용한다.

- `id`: 예 `T1`
- `objective`: 하나의 의미 있는 결과
- `profile`: `direct | research | analysis | writing | coding | artifact | external_action`
- `inputs`: 필요한 사용자/upstream/tool data
- `depends_on`: 선행 node ID
- `capability_need`: 필요한 능력의 의미적 설명
- `constraints`: 상속되거나 node에 특화된 hard constraint
- `permission_level`: `read | analyze | draft | edit | send | destructive`
- `success_check`: 관찰 가능한 완료 조건
- `output_for`: 최종 출력 또는 downstream node

## 분해 규칙

다음 중 하나가 있을 때만 node를 분리한다.

- 다른 capability/tool class가 필요하다.
- 한 node의 output이 다른 node의 prerequisite다.
- side effect가 별도의 permission boundary를 가진다.
- 독립 실행이 latency 또는 reliability를 실제로 개선한다.
- verification 자체가 별도 결과로 다룰 만큼 중요하다.

다음을 별도 node로 만들지 않는다.

- 요청 이해
- 생각
- 지침 읽기
- 답변 계획
- 개별 검색 query
- 개별 file read
- 개별 test command
- 서론/본론/결론 작성

이들은 node 내부 구현 세부사항이다.

## Graph Size

권장:
- 단순 작업: 1 node
- 대부분의 복합 작업: 2–5 nodes
- 그 이상: 실제 독립 산출물/의존관계가 있을 때만

graph가 클수록 좋은 것이 아니다.

## Parallelism

다음 조건에서만 병렬 실행한다.

- 서로 output dependency가 없다.
- write 충돌이 없다.
- 안전, 비용, rate, product constraint를 위반하지 않는다.

병렬 가능 예:
- 한국 정책 조사
- EU 정책 조사

순차 실행 예:
- code inspect → modify → test

## Side-effect Isolation

write/action이 research/analysis와 다른 permission boundary를 가지면 별도 node로 분리한다.

예:
- T1: 일정 정보 확인
- T2: event parameter 준비
- T3: calendar event 생성

planning node가 T3를 몰래 수행해서는 안 된다.

## 완료 조건

모든 최종 deliverable이 성공한 node에 연결되거나, 실패가 명확하게 공개되면 graph가 완료된 것이다.
