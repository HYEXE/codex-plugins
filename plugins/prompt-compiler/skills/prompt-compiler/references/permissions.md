# Permission Boundary Model

Compiler는 action을 명확히 할 수 있지만 authorization을 강화할 수 없다.

## Permission Ladder

다음 수준을 구분한다.

1. `read`
2. `analyze`
3. `draft`
4. `edit`
5. `send` 또는 create/update에 해당하는 실행
6. `destructive`

낮은 수준의 권한은 높은 수준의 권한을 포함하지 않는다.

예:
- "메일 내용 찾아줘" → `read`
- "답장 초안 써줘" → `draft`
- "이 문서 고쳐줘" → 해당 문서 `edit`
- "PR 리뷰해줘" → `analyze`, merge 아님
- "일정 후보 찾아줘" → `analyze`, event 생성 아님

## Scope Coupling

permission은 지정된 scope에만 적용된다.

예:
- 한 component edit ≠ repository-wide cleanup
- 한 recipient email ≠ 전체 팀 email
- 한 event create ≠ recurring series
- 한 record update ≠ bulk update

## Ambiguous Side Effect

consequential write의 target이 materially ambiguous하고 authorized context에서 resolve할 수 없다면 최소 clarification을 얻는다.

수신자/account/resource를 “가장 그럴듯한 것”으로 추정하지 않는다.

## Derived Technical Actions

사용자가 허용한 high-level action을 수행하기 위해 필요한 low-level technical action은 scope와 product rule 안에서 수행할 수 있다.

예:
- repository bug fix를 허용했다면 관련 source/test edit은 scope 안일 수 있다.
- unrelated file delete는 scope 밖이다.

## Verification

write는 action response로 성공을 확인한다.

시도했다는 이유만으로 성공했다고 추론하지 않는다.
