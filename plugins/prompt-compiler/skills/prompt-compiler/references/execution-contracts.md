# Execution Contracts

각 의미 있는 task node에 대해 필요한 만큼만 Execution Contract를 만든다.

기본적으로 사용자에게 노출하지 않는다.

## 공통 필드

필요한 것만 사용한다.

- Objective
- Inputs
- Constraints
- Output
- Success check

## Research Node

필요할 수 있는 항목:
- Research question
- Freshness requirement
- Time/geographic/jurisdictional scope
- Source hierarchy
- Inclusion/exclusion criteria
- Comparison dimensions
- Citation requirement
- Conflict-handling rule

검증:
- 중요한 claim이 근거를 가지는가
- 최신성이 필요한 claim이 충분히 최신인가
- fact와 interpretation이 구분되는가
- source disagreement가 중요할 때 드러나는가

## Analysis / Decision Node

필요할 수 있는 항목:
- Decision question
- Evaluation dimensions
- Priority/trade-off rules
- Alternatives
- Risks
- 결론을 바꿀 수 있는 조건

검증:
- recommendation이 evidence에서 도출되는가
- 중요한 counterargument가 필요한 경우 다뤄졌는가
- uncertainty가 숨겨지지 않았는가

## Writing Node

필요할 수 있는 항목:
- Audience/recipient
- Purpose/desired action
- 포함해야 할 사실
- 임의로 만들면 안 되는 사실
- Tone/formality
- Length/channel
- Delicate points

검증:
- 제공된 사실이 보존되는가
- unsupported detail을 만들지 않았는가
- 요청한 surface/format을 지켰는가

현재 제품이 별도의 structured writing-input flow를 요구하면 해당 흐름을 따른다.

## Coding / Codex Node

필요할 수 있는 항목:
- Problem
- Current behavior
- Expected behavior
- Relevant code/reproduction
- Allowed scope
- Do not change
- Implementation requirements
- Acceptance criteria
- Verification checks

규칙:
- 관련 repository instruction과 구현을 먼저 확인한다.
- 가능한 경우 기존 pattern을 재사용한다.
- 필요한 최소 변경을 우선한다.
- unrelated refactor, rename, dependency 추가, formatting churn을 피한다.
- test를 통과시키기 위해 test를 약화하거나 삭제하지 않는다.

검증:
- 원래 bug/requirement가 해결되었는가
- targeted test
- relevant regression check
- 적절하고 가능한 경우 typecheck/lint/build
- 실제로 실행하지 않은 check를 통과했다고 말하지 않음

## Artifact Node

필요할 수 있는 항목:
- Artifact type
- Required sections/sheets/slides/pages
- Source material
- Style/format constraints
- Formulas/calculations
- Accessibility/visual requirements
- File format/name

검증:
- 실제 file이 존재하는가
- 열거나 parse할 수 있는가
- 필수 내용이 포함되는가
- 계산/formula가 필요한 경우 맞는가
- 요청한 format/name을 만족하는가

환경의 artifact-specific workflow를 따른다.

## External Action Node

필요할 수 있는 항목:
- Action
- Target/recipient/resource
- Exact change/data
- Time/date
- Preconditions
- Permission level
- Success condition

규칙:
- 가능한 경우 authorized connected data에서 정확한 target을 resolve한다.
- consequential write의 대상이 모호하면 함부로 추정하지 않는다.
- preview/draft와 write를 구분한다.
- product-level confirmation/safety requirement를 유지한다.

검증:
- action response가 성공을 확인하는가
- 올바른 대상인가
- 요청한 범위만 변경되었는가
