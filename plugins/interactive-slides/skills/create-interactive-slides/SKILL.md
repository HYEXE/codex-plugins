---
name: create-interactive-slides
description: 발표문·강의안·제품 시연을 스토리보드로 구조화하고 체험형 또는 시연형 HTML·CSS·JavaScript 슬라이드로 제작·검증한다. 내용에 맞는 인터랙션, 발표자 노트, 시연 cue, 리허설과 fallback이 필요할 때 사용한다. 일반 PPTX 편집이나 정적인 문서 작성에는 사용하지 않는다.
---

# Interactive Slides Creator

발표의 핵심 메시지가 인터랙션보다 먼저다. 모든 슬라이드를 움직이게 만들지 말고, 조작이 이해·비교·기억·시연 안정성을 실제로 높이는 경우에만 인터랙션을 넣는다. 시연형은 일반 슬라이드 이동과 장면 내부 재생을 분리한다.

## 입력과 산출물

발표문, 대상 청중, 발표 목적, 시간, 브랜드 자료와 원하는 모드를 확인한다. 결과를 크게 바꾸지 않는 정보는 안전한 기본값을 사용하고 완료 보고에 가정을 남긴다. 사실·수치·인용은 제공된 자료를 보존하며 출처 없이 만들지 않는다.

기존 발표의 범위가 명확한 소규모 수정은 해당 파일에 바로 구현할 수 있다. 새 발표는 아래 proposal-first gate를 거치고, 발표가 길거나 출처가 많거나 여러 시연 장면이 있으면 `assets/templates/presentation-brief.md`와 `assets/templates/storyboard.md`를 실제 정보로 채워 판단 근거를 보존한다. 작은 수정에 계획 문서를 기계적으로 추가하지 않는다.

기본 산출물은 다음 파일을 가진 독립 디렉터리다.

```text
presentation/
|-- presentation-brief.md  선택: 복잡한 발표의 목표·제약
|-- storyboard.md          선택: 장면별 제작 계약
|-- production-proposal.md 필수: 승인된 범위와 완료 기준
|-- design-plan.json       필수: 승인 범위에 고정된 제작 결정
|-- index.html
|-- styles.css
|-- deck.js
|-- scenes.js
`-- presentation.js
```

`assets/starter/`를 복사한 뒤 `deck.js`의 콘텐츠와 필요한 시각 스타일을 발표에 맞게 바꾼다. 프레임워크나 빌드 도구는 기존 프로젝트 또는 사용자가 요구할 때만 도입한다.

## 제작 흐름

새 발표는 proposal과 design plan이 승인·검증된 뒤 starter를 수정한다.

1. 긴 발표문이나 근거가 많은 발표는 [references/content-to-storyboard.md](references/content-to-storyboard.md)에 따라 주장, 근거, 전환, 시간과 장면 목표를 먼저 구조화한다.
2. 발표 시간에서 질의응답과 실제 시연 여유를 빼고 슬라이드 수와 밀도를 정한다.
3. 사용자가 지정한 `experience` 또는 `demo` 모드를 따른다. 새 발표에서 모드가 없다면 임의로 추론하지 말고 두 옵션의 차이를 설명해 하나를 선택받는다. `demo`에서는 일반 Deck Controller와 장면별 Scene Controller를 분리한다.
4. 승인 proposal을 [references/design-plan-contract.md](references/design-plan-contract.md)에 따라 `design-plan.json`으로 컴파일한다. 제안서 SHA, 승인 slide ID, mode, art direction, slide family와 scene 선택 근거를 고정한다.
5. [references/interaction-selection.md](references/interaction-selection.md)의 Interaction Value Gate를 통과한 장면만 인터랙티브하게 만들고 채택·제외 이유를 design plan과 storyboard에 기록한다.
6. 발표문을 그대로 화면에 복사하지 말고 화면용 핵심 문장과 speaker notes를 분리한다.
7. starter의 `deck.js`를 실제 콘텐츠로 교체하고 placeholder를 남기지 않는다.
8. [references/rehearsal-and-fallback.md](references/rehearsal-and-fallback.md)에 따라 정상 진행, replay, skip, 실패와 정적 fallback을 리허설한다.
9. `scripts/validate_deck_project.py <presentation-directory>`를 실행하고 로컬 브라우저에서 선택된 모드, 키보드, 작은 화면과 `prefers-reduced-motion`을 검증한다. 보지 못한 렌더링이나 실행 결과를 성공했다고 말하지 않는다.

## Interaction Value Gate

인터랙션 후보마다 인과관계, 시간적 변화, 선택에 따른 결과, 직접 조작의 설명 이득을 확인한다. 두 가지 이상의 의미 있는 이득이 없거나 정적 비교가 더 명확하면 제외한다. 자동 재생은 시간 순서가 메시지에 필수이고 replay·skip·fallback을 제공할 수 있을 때만 채택한다. 세부 점수와 비용 상한은 interaction selection reference를 따른다.

## 인터랙션 선별

| 내용 구조 | 우선 형식 | 사용 조건 |
| --- | --- | --- |
| 순서·프로세스 | `steps` | 단계별 변화가 결론 이해에 필요할 때 |
| 두 관점·전후 비교 | `comparison` | 차이를 같은 기준에서 대조할 수 있을 때 |
| 선택과 결과 | `choice` | 선택별 피드백이 메시지를 강화할 때 |
| 변수와 영향 | `range` | 값 변화와 결과 사이 관계를 설명할 때 |
| 공격 흐름·제품 시연·상태 변화 | `sequence` | 시간 순서와 중간 상태를 자동 재생해야 할 때 |
| 날짜·사건·릴리스 순서 | `timeline` | 각 시점의 변화와 근거를 단계적으로 강조할 때 |
| 시스템 구성·관계 | `diagram` | 노드를 선택하며 역할과 연결을 설명할 때 |
| 코드와 실행 원리 | `code-walkthrough` | 코드 줄과 해설을 같은 순서로 진행할 때 |
| 전후 상태 | `before-after` | 동일한 기준에서 변화 내용을 전환 비교할 때 |
| 제목·인용·단일 주장 | 정적 슬라이드 | 조작이 메시지를 더 명확하게 하지 못할 때 |

한 슬라이드에는 하나의 주 인터랙션만 둔다. 같은 조작을 반복하지 말고 전체 발표에서 인터랙션의 역할을 다양하게 배분한다. 실제 코드를 실행하는 데모는 `eval` 또는 `new Function`을 사용하지 않는다. 실행이 꼭 필요하면 별도 파일이나 sandbox가 적용된 iframe으로 격리하고 실패 시 정적 결과를 제공한다. 조사·분석 발표에서는 `VERIFIED`, `INFERRED`, `ANALYSIS`, `SYNTHETIC TELEMETRY`처럼 사실과 재구성의 경계를 화면에 표시한다.

## 모드와 콘텐츠 계약

- 모드별 진행·reset·cue 규칙은 [references/mode-contracts.md](references/mode-contracts.md)를 읽고 적용한다.
- slide와 interaction 데이터 필드는 [references/deck-schema.md](references/deck-schema.md)를 읽고 작성한다.
- 자동 시연 장면이 있으면 [references/scene-lifecycle.md](references/scene-lifecycle.md)를 읽고 장면 소유권·취소·재생 계약을 적용한다.
- timeline, diagram, code walkthrough 또는 before/after가 필요하면 [references/scene-recipes.md](references/scene-recipes.md)에서 해당 recipe만 읽고 데이터·fallback 계약을 적용한다.
- 복잡한 발표의 화면 문구·근거·시간·fallback은 storyboard에 기록하되, storyboard 자체를 최종 발표 화면에 노출하지 않는다.
- `experience`에서도 다음 슬라이드로 이동할 수 있어야 하고, `demo`에서도 발표자가 현재 상호작용을 reset할 수 있어야 한다.
- 핵심 정보는 JavaScript가 실패해도 제목과 요약에서 파악할 수 있게 한다.
- speaker notes에는 화면 문구 반복이 아니라 전환 문장, 강조점, 예상 시간과 시연 cue를 넣는다.

## 디자인과 접근성

- 프로젝트의 기존 브랜드가 있으면 우선하고, 없으면 발표 주제에 맞는 명확한 시각 방향과 CSS 변수를 정한다.
- 본문 최소 크기, 대비, 여백과 먼 거리 가독성을 일반 웹 페이지보다 보수적으로 잡는다.
- pointer 없이 모든 제어가 동작하고 focus가 보여야 한다. 현재 슬라이드와 상태 변화는 보조기술에 전달한다.
- `prefers-reduced-motion`에서는 장거리 이동, 반복 애니메이션과 자동 진행을 줄이되 정보와 제어를 제거하지 않는다.
- 모바일에서는 슬라이드를 축소판으로 만들지 말고 콘텐츠가 자연스럽게 재배치되도록 한다.

## 완료 기준

- 발표문의 핵심 주장과 순서가 보존되고 화면 문구와 speaker notes가 분리돼 있다.
- 선택한 모드와 인터랙션마다 교육적 또는 시연상의 이유가 설명된다.
- 처음 열기, 이전·다음, 목차, mode 전환, replay, zoom, fit, fullscreen, notes, hash 이동이 동작한다.
- `demo` 장면은 ready → running → complete를 따르고 이동 시 timer와 listener를 정리한다.
- mouse, keyboard, touch, 작은 화면과 reduced motion에서 핵심 과업을 완료할 수 있다.
- 외부 네트워크 없이 열리며 console 오류와 미완성 placeholder가 없다.
- 실제 수행한 검증과 미검증 환경을 구분해 보고한다.
- 복잡한 시연은 정상 경로, skip, replay, 장면 실패와 오프라인 상태를 요약한 Rehearsal Receipt를 남긴다.

## 제작 입력과 시각 완성도

스토리보드나 구현에 들어가기 전에 발표 제작 계약을 확정한다.

- 모드가 제공되지 않았다면 [templates/presentation-intake.md](templates/presentation-intake.md)를 사용해 `demo` 또는 `experience` 중 하나를 선택받는다.
- brief, storyboard나 starter file을 생성하기 전에 [references/authoring-intake.md](references/authoring-intake.md)를 읽는다.
- 선택된 모드를 brief, storyboard와 `data-presentation-mode`에 고정하고 납품물에 runtime mode switch를 남기지 않는다.
- design system을 정의하거나 slide를 구성하기 전에 [references/visual-quality-system.md](references/visual-quality-system.md)를 읽는다.
- 상용 deck은 품질 기준으로만 참고한다. 사용자의 콘텐츠, 근거와 brand에서 독창적인 visual system을 만든다.
- 반복되는 card grid, 불필요한 gradient, 장식용 dashboard, 만들어낸 데이터와 일반적인 AI presentation 흔적을 거부한다.
- panel과 utility의 presentation chrome은 SVG icon, accessible name, focus state와 tooltip이 있는 icon-only control로 만든다.

## Proposal-first 제작 게이트

새 발표는 모두 proposal과 승인 게이트를 거친다. 프로젝트 규모에 맞게 상세도를 조절하되, 원시 요구사항에서 최종 제작 파일을 바로 생성하지 않는다.

1. 제작 입력을 완료하고 `demo` 또는 `experience` 모드를 고정한다.
2. [references/proposal-workflow.md](references/proposal-workflow.md)를 읽는다.
3. 요구사항, 발표문, 근거, 자산, 시간과 interaction 기회를 분석한다.
4. [templates/production-proposal.md](templates/production-proposal.md)에 slide별 제작 범위 추정치를 작성한다.
5. 자연어 피드백을 받거나 [templates/proposal-feedback.md](templates/proposal-feedback.md)를 사용한다.
6. 새 버전과 명시적인 범위 영향 요약을 포함해 proposal을 개정한다.
7. 명시적 승인을 기록하고 승인된 proposal을 검증한다.
8. [references/design-plan-contract.md](references/design-plan-contract.md)를 읽고 승인 범위에서 [templates/design-plan.json](templates/design-plan.json)을 작성한다.
9. proposal SHA, slide ID, mode, visual system, scene 결정과 fallback 계약이 모두 유효할 때만 design plan을 `ready`로 표시한다.
10. 두 게이트가 모두 통과한 뒤 최종 제작을 시작하고, 납품 deck을 승인된 모든 slide와 acceptance criterion에 대조한다.

추정에는 slide 수, duration, composition, interaction, asset, effort와 risk를 포함한다. 사용자가 rate card와 pricing rule을 제공한 경우에만 금액을 계산한다.

제작 전에 다음을 실행한다.

    python scripts/validate_production_proposal.py <proposal.md> --require-approved
    python scripts/validate_design_plan.py <design-plan.json> --proposal <proposal.md> --require-ready

둘 중 하나라도 실패하면 proposal, review 또는 design-planning 상태에 머문다. 최종 HTML, CSS, JavaScript나 production asset을 생성하지 않는다.
