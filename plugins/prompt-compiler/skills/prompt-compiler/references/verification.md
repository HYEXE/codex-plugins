# Verification Framework

검증은 “자신감 있는 표현”을 만드는 과정이 아니라 사용자의 실제 outcome을 확인하는 과정이다.

## Node-level Verification

### Factual / Research
- material factual claim이 충분한 support를 가지는가
- time-sensitive claim이 충분히 최신인가
- primary/authoritative source가 적절히 사용되었는가
- uncertainty와 source disagreement가 정확히 표현되는가

### Analysis
- conclusion이 evidence와 evaluation criteria에서 도출되는가
- 중요한 trade-off가 다뤄졌는가
- 결과에 영향을 주는 assumption이 드러나는가

### Writing
- 필수 사실이 포함되는가
- unsupported detail을 피했는가
- audience/channel/tone/length가 맞는가
- 원하는 action이 명확한가

### Coding
- 원래 bug/requirement가 해결되는가
- targeted test를 가능한 경우 실행했는가
- relevant regression check를 수행했는가
- 적절하고 가능한 경우 typecheck/lint/build를 실행했는가
- 실제 실행 결과 없이 pass를 주장하지 않는가

### Artifact
- file이 실제로 열리거나 parse되는가
- 요청한 내용이 모두 들어 있는가
- table/formula/layout이 읽을 수 있고 맞는가
- filename/format이 맞는가

### External Action
- 올바른 target/recipient/resource인가
- action이 성공했는가
- 허용된 변경만 수행했는가

## Global Verification

node 완료 후:
- 모든 requested deliverable을 실제 result에 연결한다.
- research, analysis, final writing 사이의 일관성을 확인한다.
- date/number/entity가 서로 충돌하지 않는지 본다.
- final artifact가 upstream evidence를 반영하는지 본다.
- synthesis 과정에서 hard constraint가 사라지지 않았는지 확인한다.

## Verification Status

내부적으로 다음 상태를 사용할 수 있다.

- `verified`
- `partially_verified`
- `not_verified`
- `verification_not_applicable`

사용자에게는 중요한 verification limitation만 노출한다.

실제 근거 없이 `verified`, `passed`, `sent`, `created`, `updated`, `latest`에 해당하는 표현을 사용하지 않는다.
