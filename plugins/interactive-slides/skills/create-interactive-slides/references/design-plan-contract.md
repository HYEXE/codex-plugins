# Design plan 제작 계약

`design-plan.json`은 승인된 production proposal과 최종 HTML, CSS, JavaScript 사이의 구현 manifest다. 제작 전에 시각·interaction 결정을 검토할 수 있게 하고 생성 deck이 승인 범위에서 벗어나는 것을 막는다.

Production proposal은 계속 canonical scope record다. Design plan은 composition과 구현을 구체화할 수 있지만 slide를 추가하거나 선택된 모드를 바꾸거나 승인의 의미를 다시 해석할 수 없다.

## Proposal 결속

Proposal이 승인 게이트를 통과한 뒤에만 `templates/design-plan.json`에서 plan을 만든다. 다음 값을 정확히 결속한다.

- 승인된 proposal version
- proposal title
- 고정된 `demo` 또는 `experience` 모드
- proposal 전체 파일의 lowercase SHA-256
- row status가 `approved`인 모든 proposal slide

Design plan에는 `remove` 또는 `defer` row를 포함하지 않는다. Plan 생성 뒤 proposal이 바뀌면 hash가 stale 상태가 되므로 plan을 다시 생성하거나 개정한다.

## Art direction과 slide family

Layout을 배정하기 전에 하나의 일관된 art direction을 정의한다. 다음을 기록한다.

- editorial premise
- display, body와 numeral typography
- background, foreground와 accent palette
- image treatment
- grid와 geometry
- motion language
- 하나의 icon family

Composition, visual anchor와 density가 목적에 맞게 다른 소수의 slide family를 정의한다. Family를 일반적인 card grid로 만들지 않는다. 이야기의 연속성이 필요하면 인접 slide가 같은 family를 사용할 수 있지만, 전체 deck은 thumbnail view에서도 알아볼 수 있는 rhythm을 가져야 한다.

## Slide 제작 결정

승인된 각 slide는 다음을 선언해야 한다.

- `delivery_mode`: `demo` 또는 `experience`
- purpose와 working headline
- slide family, composition과 dominant visual
- speaking time과 content budget
- evidence boundary와 source 또는 asset ID
- interaction의 채택 또는 거부 결정
- keyboard, reduced-motion과 static-fallback 동작

Working headline을 선언된 글자 수 안에 유지하고 문서 읽기가 아니라 projection에 맞춰 작성한다. 승인 proposal의 source와 asset ID만 사용하고 composition을 채우기 위해 근거를 만들지 않는다.

승인된 proposal row는 scope contract다. Purpose, core content/headline, composition, speaking time, interaction decision과 scene type, 전체 asset/source ID set을 보존한다. 참조하는 모든 ID는 proposal resource inventory에 존재해야 한다.

## Interaction 계약

Interaction을 채택했다면 다음을 지킨다.

- `static`이 아닌 지원되는 scene type을 선택한다.
- `causality`, `temporal`, `decision`, `comparison`, `spatial` 중 서로 다른 이득을 두 개 이상 기록한다.
- `demo` 모드에서는 `ready-running-complete` lifecycle을 사용한다.
- `experience` 모드에서는 `direct-manipulation-reset` lifecycle을 사용한다.
- 의미 있는 static fallback을 제공한다.

Single-mode proposal에서는 모든 slide의 `delivery_mode`가 proposal mode와 같아야 한다. `hybrid` proposal은 slide별로 `demo` 또는 `experience`를 선택한다. Lifecycle과 scene 지원 여부는 해당 slide mode를 기준으로 검증한다. 예를 들어 `sequence`는 experience recipe가 아니라 demo recipe다.

Interaction을 거부했다면 `scene_type: static`, `lifecycle: none`을 사용하고 정적 composition이 더 명확한 이유를 적는다.

## Presentation chrome

Presentation panel과 utility는 slide content 바깥에 둔다. Plan은 이를 icon-only로 유지하면서 accessible name과 tooltip을 요구해야 한다. 하나의 SVG icon family를 사용하고 visible focus와 native keyboard 동작을 보존한다.

## 제작 게이트

Plan이 완성됐을 때만 `plan_status`를 `ready`로 설정하고 다음을 실행한다.

```text
python scripts/validate_design_plan.py design-plan.json --proposal production-proposal.md --require-ready
```

Proposal이 승인되지 않았거나 proposal hash가 stale 상태이거나 승인 slide ID 또는 mode가 다르거나, 채택한 interaction에 value, lifecycle 또는 fallback 근거가 없으면 최종 제작을 시작하지 않는다.
