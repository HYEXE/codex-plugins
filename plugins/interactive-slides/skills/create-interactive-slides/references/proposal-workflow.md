# Proposal-first 제작 흐름

원시 요구사항에서 최종 slide 제작을 바로 시작하지 않는다. 요청을 검토 가능한 production proposal로 바꾸고 사용자와 함께 개정한 뒤 명시적인 승인을 받아 제작에 들어간다.

## 상태 모델

```text
intake -> analysis -> proposal -> review -> approved -> design-plan -> production -> qa -> delivered
```

Proposal은 canonical scope record다. 피드백이 slide 수, duration, asset, interaction, visual direction, delivery constraint 또는 acceptance criterion을 바꾸면 version과 revision history를 갱신한다.

## 1. Intake

먼저 제작 입력 계약을 사용한다. 누락된 정보만 수집한다.

- 필수 모드: `demo` 또는 `experience`
- 목적, 청중, 장소, 시간과 delivery target
- 요구사항, 제외 범위와 반드시 전달할 메시지
- 제공 가능한 발표문, outline 또는 원본 자료
- brand asset, reference deck과 시각 제약
- 근거, 개인정보, offline과 integration 제약

발표문은 선택 사항이다. 발표문이 없다면 speaking-time과 slide-density 추정의 confidence를 낮게 표시하고 사용자에게 필요한 outline 결정을 구분한다.

## 2. 분석

Slide를 제안하기 전에 다음을 분석한다.

- 발표문이나 원본을 opening, claim, evidence, transition, demonstration moment와 closing으로 나눈다.
- 중복되거나 누락됐거나 근거가 부족한 claim을 식별한다.
- speaking time을 추정하고 사용한 pacing 가정을 밝힌다.
- image, chart, diagram, code view, simulation 또는 live integration이 필요한 콘텐츠를 찾는다.
- 제공된 사실과 해석·재구성을 구분한다.
- 신뢰할 수 있는 proposal 작성을 막는 질문을 식별한다.
- 설명이나 청중 행동을 개선하는 경우에만 interaction을 선택한다.

Proposal을 완성된 것처럼 보이게 하려고 사실, metric, source, asset 또는 product behavior를 만들지 않는다.

## 3. 제작 범위 추정

`templates/production-proposal.md`에서 version이 있는 proposal을 만든다. 다음을 포함해야 한다.

- 한 문장 결과와 narrative structure
- 예상 slide 수와 발표 시간
- slide별 purpose, content, composition, interaction, source, asset과 speaking-time 계획
- visual direction과 slide-family 계획
- interaction 수와 lifecycle complexity
- asset, source와 integration inventory
- delivery, accessibility와 fallback 요구사항
- risk, assumption, blocking question과 confidence
- 명시적인 acceptance criterion

Canonical proposal에는 정수 slide 수를 사용한다. 모호한 범위를 값으로 넣지 말고 대안은 scenario로 설명한다.

### 상대 effort 모델

Effort point는 범위 비교에만 사용하고 보장된 시간으로 취급하지 않는다.

- static statement, quote 또는 section slide: 1
- evidence, chart, comparison 또는 image-led composition: 2
- diagram, timeline 또는 direct-manipulation scene: 3
- replay, skip과 fallback이 있는 blocking demo scene: 5
- live external integration 또는 custom data transformation: 8과 명시적인 risk

사용자가 rate card, currency와 pricing rule을 제공한 경우에만 금액을 추정한다. 그 외에는 가격을 만들지 말고 제작 범위, effort point와 uncertainty를 보고한다.

## 4. 검토와 개정

자연어 또는 `templates/proposal-feedback.md`로 피드백을 받는다. 각 응답을 다음 상태로 분류한다.

- `approve`
- `revise`
- `remove`
- `merge`
- `split`
- `defer`

간결한 change summary와 slide 수, duration, asset, effort와 risk 영향을 포함한 새 proposal version을 반환한다. 이전 version을 보존하고 revision history의 결정을 조용히 덮어쓰지 않는다.

일부 slide만 승인하고 나머지는 review 상태로 둘 수 있다. 모든 blocking decision이 해결되기 전까지 전체 proposal은 `review` 상태다.

## 5. 승인 게이트

제작 전에 다음을 확인한다.

1. 사용자의 명시적 승인이 있을 때만 `proposal_status: approved`를 설정한다.
2. `approved_by`, `approved_at`과 `blocking_questions: 0`을 기록한다.
3. 실행할 수 있다면 `validate_production_proposal.py --require-approved`를 실행한다.
4. 게이트가 실패하면 최종 HTML, CSS, JavaScript나 production asset을 생성하지 않는다.

Storyboard, wireframe과 작은 design-direction sample은 최종 제작물이 아니라 검토용 산출물로 표시한다.

## 6. Design plan 컴파일

최종 HTML, CSS 또는 JavaScript를 편집하기 전에 승인된 proposal을 `templates/design-plan.json`으로 컴파일한다. `references/design-plan-contract.md`를 읽고 proposal을 canonical scope record로 유지한다.

Design plan은 다음을 만족해야 한다.

- 승인 proposal의 version, title, mode와 SHA-256을 정확히 결속한다.
- proposal status가 `approved`인 slide row만 정확히 포함한다.
- 하나의 art direction과 소수의 재사용 가능한 slide-family system을 정의한다.
- 각 slide에 family, dominant visual, content budget과 evidence boundary를 배정한다.
- Interaction Value Gate 이득과 함께 채택 또는 거부 결정을 기록한다.
- 모드별 lifecycle, static fallback과 accessibility 동작을 고정한다.
- accessible name과 tooltip이 있는 icon-only presentation chrome을 요구한다.

다음을 실행해 통과한 뒤에만 `plan_status`를 `ready`로 설정한다.

```text
python scripts/validate_design_plan.py design-plan.json --proposal production-proposal.md --require-ready
```

Design plan은 composition을 구체화할 수 있지만 scope를 조용히 바꿀 수 없다. Slide purpose, count, duration, source, asset, interaction scope 또는 art direction을 바꾸려면 먼저 proposal을 개정하고 다시 승인받는다.

## 7. 제작과 변경 통제

승인된 slide row와 acceptance criterion을 기준으로 제작한다. 제작 중 요청이 scope를 바꾸면 다음을 수행한다.

- 변경을 기록한다.
- count, duration, asset, effort와 risk 영향을 보여준다.
- proposal을 `review` 상태로 되돌린다.
- 영향받는 작업을 계속하기 전에 개정 version의 승인을 받는다.

Scope를 바꾸지 않는 작은 수정은 production 상태에서 처리할 수 있지만 revision history에는 기록한다.

## 8. Proposal-to-delivery QA

납품할 때 승인된 모든 slide row를 design plan과 생성 deck에 대조한다. 구현, 변경, 연기와 누락 항목을 보고한다. 기록된 결정 없이 승인 proposal 또는 ready design plan과 다르면 기술적으로 유효한 deck도 완료로 보지 않는다.
