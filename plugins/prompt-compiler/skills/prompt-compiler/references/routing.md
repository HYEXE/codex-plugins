# Capability Routing

먼저 **semantic need**를 판단하고, 그 다음 현재 환경에서 실제로 사용 가능한 capability를 선택한다.

존재하지 않는 tool name을 만들어내지 않는다.

## Routing Principles

### Current Public Information

필요:
- 최신 사실
- 최근 정책/법률/일정/제품/기업 정보
- source-backed research

경로:
- 사용 가능하고 허용된 current web/research capability

### Connected / Private Information

필요:
- 사용자의 email
- calendar
- contacts
- Drive/workspace docs
- private repository
- 기타 connected data

경로:
- 관련 connected source

정확한 답이 connected data에 달려 있다면 기억이나 public web으로 대신하지 않는다.

### Codebase Changes

필요:
- repository inspect
- code edit
- test/command execution

경로:
- repository/code execution environment

가능하면 편집 전에 project instruction을 확인한다.

### Artifact Production

필요:
- spreadsheet
- document
- PDF
- slide deck
- image/design
- 기타 native file

경로:
- artifact-specific workflow

실제 artifact 생성이 가능한데 prose outline으로 대체하지 않는다.

### External Writes

필요:
- send
- create
- update
- delete
- publish
- comment
- schedule

경로:
- authorized connector/action capability

permission/confirmation boundary를 보존한다.

### Pure Reasoning / Transformation

필요:
- 제공된 text 요약
- 번역
- stable concept 설명
- 모든 사실이 제공된 rewrite

경로:
- 외부 capability가 정확성을 materially 높이지 않는다면 direct model execution

## Capability Selection Priority

동일한 node를 여러 경로로 수행할 수 있다면 다음을 우선한다.

1. 필수 private/authoritative source
2. freshness가 중요할 때 primary/current source
3. task-native tool
4. 검증을 유지하면서 최소 tool call
5. correctness/permission을 보존하는 fallback

## Tool Failure

tool failure는 결과를 만들어내도 된다는 허가가 아니라 bounded replanning의 근거다.

필수 capability가 unavailable이면:
- 안전한 equivalent path가 있으면 적응한다.
- 없으면 가능한 범위만 완료하고 limitation을 명시한다.
