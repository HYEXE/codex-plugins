# Agent·Tool 실행 상태 UX

AI와 외부 tool 실행 화면은 내부 animation 이름보다 실제 작업 상태와 사용자 통제 가능성을 먼저 표현한다.

## 상태 적용

- `acknowledged`: 요청이 접수됐지만 실제 실행 단계는 아직 확인되지 않았다.
- `running`: 확인 가능한 현재 단계나 비결정적 진행을 표시한다.
- `waiting`: 사용자 입력, 권한 또는 외부 서비스 중 무엇을 기다리는지 명시한다.
- `partial`: 완료·실패한 하위 항목과 영향 범위를 나누고 실패 범위만 재시도하게 한다.
- `success`: 실제 완료 결과와 다시 찾을 수 있는 위치를 제공한다.
- `error`: 원인 범주, 보존 상태, retry 안전성과 대체 경로를 제공한다.
- `cancelled`: local wait와 server 작업 중 무엇이 중단됐고 side effect가 남았는지 설명한다.

## 표현 규칙

- 실제 수치를 계산할 수 있을 때만 percentage를 표시한다. 그렇지 않으면 단계 또는 비결정적 진행으로 표현한다.
- “thinking”, “planning”, “tool running” 같은 내부 label은 사용자가 다음 행동을 결정하는 데 유용할 때만 노출한다.
- tool 이름보다 사용자가 이해하는 작업명을 우선하고 technical detail은 점진적으로 공개한다.
- 완료 toast가 사라져도 중요한 결과, 부분 실패와 복구 경로는 작업 기록이나 결과 영역에 남긴다.
- 사용자가 떠나도 계속되는 job과 현재 화면을 떠나면 중단되는 request를 같은 표현으로 다루지 않는다.
- background completion, notification, refresh 이후 복원은 backend가 실제로 지원할 때만 약속한다.
- 사용자 메시지와 debug detail을 분리하고 prompt, token, credential, 개인정보와 내부 stack을 불필요하게 노출하지 않는다.

## 검증 질문

1. 이중 실행과 late response가 최신 결과를 덮지 않는가?
2. cancel 후 server side effect와 local UI 표현이 일치하는가?
3. partial result를 전체 success 또는 전체 failure로 오인하지 않는가?
4. retry가 안전하며 실패 범위만 다시 처리하는가?
5. 상태 변경이 screen reader에 너무 자주 발표되지 않는가?
6. focus를 매 상태 변화마다 빼앗지 않고 중요한 blocker를 발견할 수 있는가?
7. refresh·reconnect·다중 tab에서 현재 job을 정확히 복원하거나 복원 불가를 명시하는가?
8. 오류 detail에 민감 정보가 노출되지 않는가?
