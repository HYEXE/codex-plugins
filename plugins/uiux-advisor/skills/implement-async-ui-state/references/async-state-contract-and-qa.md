# 비동기 상태 계약과 QA

UI 상태 이름을 먼저 늘리지 말고 실제 backend 계약과 사용자가 내려야 할 결정을 연결한다.

## 작업 유형

| 유형 | 식별자 | 진실 원본 | 핵심 실패 경계 |
| --- | --- | --- | --- |
| 화면 내 request | request·operation ID | 응답과 현재 화면 상태 | 중복 실행, stale response, unmount |
| stream | stream·cursor·chunk ID | server event와 누적 결과 | 중복·누락·순서 역전, reconnect |
| background job | operation·job ID | server job status | refresh 복원, cancel 의미, orphan job |
| batch | operation·item ID | 항목별 server 결과 | partial success, failed-only retry |

같은 사용자의 한 번 실행이 여러 network request를 만들 수 있고, 한 server job을 여러 화면이 관찰할 수도 있다. UI key를 job ID로 대신하거나 request ID 하나로 모든 수명주기를 표현하지 않는다.

## 상태 모델

실제 계약에 필요한 상태만 채택한다.

| 상태 | 확인할 사실 | 사용자에게 제공할 것 |
| --- | --- | --- |
| `idle` | 시작 조건이 충족됐는가? | 시작, 입력 수정 |
| `submitting` | 요청이 전송 중인가? | 중복 방지, 가능한 중단 설명 |
| `acknowledged` | server가 operation·job을 만들었는가? | 식별 가능한 진행, 화면 이탈 정책 |
| `running` | 현재 단계나 결정적 진행이 있는가? | 정직한 진행, 상세·취소 |
| `waiting` | 사용자·권한·외부 서비스 중 무엇을 기다리는가? | 필요한 입력, 연결, 취소 |
| `partial` | 어떤 항목이 성공·실패·대기인가? | 결과 열기, 실패 범위 재시도 |
| `success` | server가 완료를 확정했는가? | 지속 가능한 결과와 후속 행동 |
| `error` | 영향 범위와 보존 상태는 무엇인가? | 안전한 retry·수정·대안 |
| `cancelled` | 실제 작업과 local wait 중 무엇이 중단됐는가? | 잔존 결과 확인, 다시 시작 |

## 동시성과 순서 불변식

- 결과를 반영하기 전에 현재 operation, entity version, account·workspace와 일치하는지 확인한다.
- 동일 event가 다시 와도 같은 결과가 되게 처리하거나 중복을 명시적으로 제거한다.
- stream cursor·sequence가 있으면 누락과 역전을 감지하고, 없으면 순서를 보장한다고 주장하지 않는다.
- refresh 뒤 job을 복원하려면 durable job ID와 status API 또는 동등한 server 계약이 필요하다.
- account·workspace 전환 뒤 이전 응답이 새 화면에 나타나지 않게 scope를 identity에 포함한다.

## 취소·재시도·낙관적 갱신

- `AbortController`는 client request를 중단할 수 있지만 이미 시작된 server side effect 취소를 자동으로 보장하지 않는다.
- server cancel이 비동기면 `cancelling`을 별도 상태로 둘지, status 조회로 terminal state를 확인할지 정한다.
- retry 전에 현재 상태를 조회해야 하는 작업과 새 idempotency key가 필요한 작업을 구분한다.
- optimistic mutation은 이전 값과 mutation ID를 보존하고, 실패한 mutation이 만든 변화만 되돌린다.
- version conflict를 무조건 덮어쓰지 않고 새 정보, 보존된 편집과 해결 행동을 제공한다.

## 접근 가능한 피드백

- 진행 spinner에는 작업명과 상태 text를 함께 제공한다.
- live region은 매 progress tick이 아니라 의미 있는 단계·blocker·완료·실패를 알린다.
- 실패 뒤 focus는 사용자가 작업을 계속하던 위치를 유지하되, 오류 요약과 연결된 field를 발견할 수 있어야 한다.
- background 완료는 제품이 실제 notification과 persistent history를 제공할 때만 화면 밖 알림을 약속한다.

## QA 행렬

1. 정상 요청, 빠른 이중 click, submit 중 route change
2. 느린 이전 응답이 빠른 새 응답 뒤 도착
3. 같은 event·chunk의 재전송과 cursor 누락
4. offline·timeout·reconnect와 새로고침 뒤 복원
5. cancel 직전·직후 완료, cancel API 오류와 잔존 side effect
6. retry 중복 생성·결제·전송 방지와 현재 상태 조회
7. optimistic success·failure·version conflict·후속 편집 보존
8. batch 일부 성공, 실패 항목만 재시도, 이미 성공한 항목 보호
9. account·workspace 변경, 다중 tab과 background tab 복귀
10. keyboard-only, screen reader announcement 빈도, reduced motion·forced colors

## 완료 보고

- 확인한 backend 상태·identity·cancel·retry 계약
- 구현한 상태 전이와 진실 원본
- stale·duplicate·partial·reconnect 처리
- 접근 가능한 피드백과 복구 경로
- 실행한 테스트와 실제 브라우저 검증
- 확인하지 못한 transport, server side effect와 assistive technology 조합
