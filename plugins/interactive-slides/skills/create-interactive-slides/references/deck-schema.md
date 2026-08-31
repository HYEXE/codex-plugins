# Deck schema

`deck.js`는 `window.INTERACTIVE_DECK`에 다음 구조를 할당한다. JSON 직렬화 가능한 데이터만 사용하며 렌더러가 문자열을 실행하게 만들지 않는다.

```js
window.INTERACTIVE_DECK = {
  meta: {
    title: "발표 제목",
    subtitle: "선택 부제",
    author: "발표자",
    defaultMode: "demo",
    modeLocked: false,
    aspectRatio: "16:9"
  },
  slides: []
};
```

`modeLocked: true`이면 `defaultMode`가 제작 승인에서 확정된 모드다. 런타임은 URL mode override를 무시하고 모드 전환 control을 숨기며 키보드·API를 통한 mode 변경도 거부한다.

## Slide fields

- `id`: URL hash와 목차에 쓰는 고유한 lower-kebab-case 값
- `section`: 목차 그룹 이름
- `kicker`: 선택적인 장 표시
- `title`: 화면의 단일 핵심 주장
- `summary`: JavaScript 실패 또는 빠른 훑어보기를 위한 짧은 요약
- `body`: 0개 이상의 짧은 문단 배열
- `points`: 핵심 항목 배열
- `metrics`: `{ value, unit, label, detail }` 배열
- `evidence`: `{ label, tone }`; tone은 `verified`, `inferred`, `analysis`, `simulation`
- `scene`: 선택적인 장면 또는 interaction 객체
- `fallback`: scene 실패 또는 JavaScript 비활성화 시 유지할 정적 설명
- `notes`: speaker notes 문자열 배열
- `sources`: 화면 하단 출처 문자열 배열

## Scene fields

### sequence

`sequence`는 시연형에서 전역 다음 키를 가로채는 blocking 장면이다.

```js
{
  type: "sequence",
  label: "교육용 자동 시뮬레이션",
  nodes: ["입력", "처리", "결과"],
  phases: [
    {
      kicker: "PHASE 01",
      title: "입력 확인",
      detail: "시연 화면에 입력 상태를 표시합니다.",
      tone: "active",
      lines: [
        { kind: "system", text: "[READY] 입력 대기" },
        { kind: "result", text: "처리할 데이터 3건 확인" }
      ]
    }
  ]
}
```

`lines.kind`는 `system`, `command`, `telemetry`, `result`, `warning`, `success` 중 하나다. 실제 로그가 아니면 장면과 화면에 `SYNTHETIC TELEMETRY`를 표시한다.

### steps

```js
{ type: "steps", items: [{ label: "수집", detail: "입력을 정규화한다." }] }
```

### comparison

```js
{
  type: "comparison",
  left: { label: "기존", points: ["수동 전환"] },
  right: { label: "개선", points: ["장면 생명주기"] }
}
```

### choice

```js
{
  type: "choice",
  prompt: "어떤 진행이 적합할까요?",
  options: [{ label: "직접 탐색", feedback: "experience가 적합합니다." }]
}
```

### range

```js
{
  type: "range",
  label: "단계 수",
  min: 1,
  max: 10,
  step: 1,
  value: 4,
  unit: "단계",
  outputLabel: "예상 시간",
  result: { base: 1, factor: 0.5, decimals: 1, suffix: "분" }
}
```

`range` 결과는 `base + value * factor`만 계산한다. 다른 계산이 필요하면 `scenes.js`에 명시적인 scene type을 추가하고 접근 가능한 정적 설명을 함께 제공한다.

### timeline

```js
{
  type: "timeline",
  events: [
    { date: "2026.08", title: "설계", detail: "장면 계약을 정의합니다.", tone: "verified" }
  ]
}
```

`timeline`은 demo에서 blocking scene이며 experience에서는 날짜 또는 사건 button으로 임의 탐색한다. 날짜가 불확실하면 확정된 값처럼 정밀도를 높이지 않는다.

### diagram

```js
{
  type: "diagram",
  nodes: [
    { id: "input", label: "Input", detail: "발표문과 근거" },
    { id: "scene", label: "Scene", detail: "장면 계약" }
  ],
  links: [{ from: "input", to: "scene", label: "구조화" }]
}
```

노드는 button으로 탐색하며 link는 보조기술이 읽을 수 있는 관계 목록으로도 렌더링한다. 위치만으로 관계를 전달하지 않는다.

### code-walkthrough

```js
{
  type: "code-walkthrough",
  language: "js",
  lines: [
    { code: "scene.start();", explanation: "현재 장면의 자동 재생을 시작합니다." }
  ]
}
```

code walkthrough는 코드를 실행하지 않는다. code 문자열은 text로만 렌더링하고 demo에서 blocking scene으로 단계 진행한다.

### before-after

```js
{
  type: "before-after",
  before: { label: "Before", points: ["이동과 재생이 결합"] },
  after: { label: "After", points: ["Deck과 Scene 책임 분리"] }
}
```

전후 상태는 button으로 전환하고 현재 상태를 `aria-pressed`로 전달한다. 이미지 wipe가 필요하더라도 두 상태의 텍스트 설명을 유지한다.
