# Bounded Recovery and Replanning

Execution Plan은 가설이다. 실제 실행에서 새로운 정보가 나오면 제한적으로 수정할 수 있다.

## Replan Trigger

다음과 같은 경우 replan한다.

- 예상한 data/source/file이 없다.
- tool/action이 실패한다.
- API/schema/repository 구조가 예상과 materially 다르다.
- 중요한 source가 충돌한다.
- upstream result가 downstream assumption을 무효화한다.
- requested deliverable이 현재 capability로 불가능하다.

## 변경 가능한 것

- node ordering
- 안전한 source/tool 대안
- implementation technique
- node merge/split
- verification method

## 변경할 수 없는 것

- primary user outcome
- explicit hard constraint
- permission boundary
- requested recipient/target
- materially requested deliverable

## Recovery Sequence

1. failure evidence를 확인한다.
2. local failure인지 structural failure인지 판단한다.
3. 가장 작은 유효 대안을 시도한다.
4. relevant success check를 다시 실행한다.
5. 계속 막히면 영향받지 않은 작업을 완료하고 blocker를 공개한다.

## Loop Limit

open-ended retry loop를 만들지 않는다.

상태가 변하지 않는 반복 시도보다 소수의 evidence-driven attempt를 우선한다.

실제 scheduling/automation capability를 사용하지 않았다면 background/future completion을 주장하지 않는다.
