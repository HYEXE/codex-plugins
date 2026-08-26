window.INTERACTIVE_DECK = {
  meta: {
    title: "설명을 시연으로 바꾸는 발표",
    subtitle: "Interactive Slides starter",
    author: "발표자",
    defaultMode: "demo",
    aspectRatio: "16:9"
  },
  slides: [
    {
      id: "opening",
      section: "문제 정의",
      kicker: "DEMO-DRIVEN PRESENTATION",
      title: "시연형 슬라이드는 다음 장으로 가기 전에 현재 장면을 완성한다.",
      summary: "슬라이드 이동과 장면 재생을 분리하면 발표자는 같은 흐름을 안정적으로 반복할 수 있습니다.",
      evidence: { label: "설계 원칙", tone: "analysis" },
      points: ["Deck Controller는 이동을 관리합니다.", "Scene Controller는 재생 상태를 관리합니다."],
      notes: ["다음 키를 눌러 일반 슬라이드 이동을 먼저 보여줍니다.", "시연 슬라이드에서는 같은 키가 장면을 시작한다는 점을 예고합니다."],
      sources: ["Interactive Slides starter · architecture contract"]
    },
    {
      id: "evidence-boundary",
      section: "문제 정의",
      kicker: "EVIDENCE BOUNDARY",
      title: "사실과 재구성을 같은 화면에서 분명히 구분한다.",
      summary: "시연의 몰입감이 근거의 확실성을 흐리지 않도록 상태 배지를 사용합니다.",
      evidence: { label: "개념 해설", tone: "analysis" },
      scene: {
        type: "comparison",
        left: { label: "VERIFIED", points: ["제공된 자료로 확인", "수치와 출처 유지"] },
        right: { label: "SIMULATION", points: ["교육용 재구성", "실제 로그가 아님을 표시"] }
      },
      notes: ["두 열을 비교하며 시연 효과와 사실성을 동시에 지키는 기준을 설명합니다."],
      sources: ["발표자가 제공한 출처를 이 위치에 기록"]
    },
    {
      id: "sequence-demo",
      section: "시연",
      kicker: "SCENE 01",
      title: "한 번의 입력으로 전체 흐름을 재생하고 언제든 안전하게 중단한다.",
      summary: "다음 키를 누르면 자동 시연이 시작됩니다. 재생 중 다시 누르면 시연을 건너뛰고 다음 슬라이드로 이동합니다.",
      evidence: { label: "교육용 자동 시뮬레이션", tone: "simulation" },
      scene: {
        type: "sequence",
        label: "SYNTHETIC TELEMETRY",
        nodes: ["INPUT", "ANALYZE", "DECIDE", "OUTPUT"],
        phases: [
          {
            kicker: "PHASE 01",
            title: "입력 구조화",
            detail: "발표문에서 주장, 근거와 전환을 분리합니다.",
            tone: "active",
            lines: [
              { kind: "system", text: "[READY] 발표문 분석 시작" },
              { kind: "telemetry", text: "segments=12 · claims=4 · transitions=3" },
              { kind: "result", text: "핵심 주장 4개를 확인했습니다." }
            ]
          },
          {
            kicker: "PHASE 02",
            title: "인터랙션 선별",
            detail: "조작이 설명을 개선하는 장면만 남깁니다.",
            tone: "warning",
            lines: [
              { kind: "command", text: "> evaluate --interaction-value" },
              { kind: "telemetry", text: "static=7 · interactive=3 · rejected=2" },
              { kind: "result", text: "장식 목적의 모션 2개를 제외했습니다." }
            ]
          },
          {
            kicker: "PHASE 03",
            title: "장면 계약 생성",
            detail: "재생, 건너뛰기, 취소와 다시 보기를 연결합니다.",
            tone: "active",
            lines: [
              { kind: "command", text: "> build scene-controller" },
              { kind: "telemetry", text: "state=ready → running → complete" },
              { kind: "success", text: "반복 가능한 시연 장면이 준비됐습니다." }
            ]
          }
        ]
      },
      fallback: "입력 구조화 → 인터랙션 선별 → 장면 계약 생성의 세 단계 목록을 정적으로 표시합니다.",
      notes: ["오른쪽 방향키로 자동 시연을 시작합니다.", "재생 중 다시 누르면 timer가 취소되고 다음 슬라이드로 이동함을 보여줍니다.", "R을 눌러 같은 장면을 처음부터 다시 재생합니다."],
      sources: ["SYNTHETIC TELEMETRY · starter demonstration data"]
    },
    {
      id: "mode-choice",
      section: "적용",
      kicker: "MODE SELECTION",
      title: "청중의 탐색과 발표자의 통제 중 무엇이 중요한가?",
      summary: "같은 콘텐츠라도 학습 목표와 발표 환경에 따라 진행 계약이 달라집니다.",
      evidence: { label: "선택형 체험", tone: "analysis" },
      scene: {
        type: "choice",
        prompt: "현재 발표에 더 중요한 조건을 선택하세요.",
        options: [
          { label: "청중이 직접 탐색", feedback: "experience 모드가 적합합니다." },
          { label: "발표자가 순서 제어", feedback: "demo 모드가 적합합니다." }
        ]
      },
      notes: ["청중의 답을 받은 뒤 상단 mode 버튼으로 실제 동작을 전환합니다."],
      sources: ["Interactive Slides · mode contract"]
    },
    {
      id: "timeline-recipe",
      section: "장면 레시피",
      kicker: "TIMELINE",
      title: "사건의 순서는 변화가 일어난 이유를 드러낸다.",
      summary: "각 시점을 선택하거나 demo 모드에서 자동으로 진행해 변화의 맥락을 확인합니다.",
      evidence: { label: "예시 데이터", tone: "simulation" },
      scene: {
        type: "timeline",
        events: [
          { date: "STEP 01", title: "관찰", detail: "발표문에서 확인 가능한 사실과 불확실성을 분리합니다.", tone: "verified" },
          { date: "STEP 02", title: "구조화", detail: "주장, 근거와 전환을 하나의 흐름으로 연결합니다.", tone: "analysis" },
          { date: "STEP 03", title: "선별", detail: "Interaction Value Gate를 통과한 장면만 채택합니다.", tone: "active" },
          { date: "STEP 04", title: "리허설", detail: "정상 진행, replay, skip과 fallback을 확인합니다.", tone: "complete" }
        ]
      },
      fallback: "관찰 → 구조화 → 선별 → 리허설의 순서가 있는 단계 목록을 표시합니다.",
      notes: ["demo 모드에서 다음 키로 자동 진행을 시작합니다.", "experience 모드에서는 원하는 사건을 직접 선택합니다."],
      sources: ["Interactive Slides · timeline recipe example"]
    },
    {
      id: "diagram-recipe",
      section: "장면 레시피",
      kicker: "DIAGRAM",
      title: "구성 요소와 연결 관계를 같은 화면에서 탐색한다.",
      summary: "노드를 선택해 역할을 읽고, 아래 관계 목록에서 방향과 의미를 확인합니다.",
      evidence: { label: "구조 해설", tone: "analysis" },
      scene: {
        type: "diagram",
        nodes: [
          { id: "source", label: "Source", detail: "발표문, 근거와 시각 자산을 보존합니다." },
          { id: "storyboard", label: "Storyboard", detail: "슬라이드별 주장과 장면 계약을 정의합니다." },
          { id: "runtime", label: "Runtime", detail: "Deck과 Scene Controller가 발표를 실행합니다." },
          { id: "rehearsal", label: "Rehearsal", detail: "실패와 복구 경로를 실제 순서로 확인합니다." }
        ],
        links: [
          { from: "source", to: "storyboard", label: "구조화" },
          { from: "storyboard", to: "runtime", label: "구현" },
          { from: "runtime", to: "rehearsal", label: "검증" }
        ]
      },
      fallback: "Source → Storyboard → Runtime → Rehearsal 관계 목록을 표시합니다.",
      notes: ["각 노드를 선택하며 역할을 설명합니다.", "시각적 배치 외에도 관계 목록이 제공된다는 점을 확인합니다."],
      sources: ["Interactive Slides · diagram recipe example"]
    },
    {
      id: "code-walkthrough-recipe",
      section: "장면 레시피",
      kicker: "CODE WALKTHROUGH",
      title: "코드를 실행하지 않고 제어 흐름과 해설을 동기화한다.",
      summary: "각 줄은 text로만 렌더링되며 demo 모드에서는 순서대로 강조됩니다.",
      evidence: { label: "안전한 코드 해설", tone: "verified" },
      scene: {
        type: "code-walkthrough",
        language: "js",
        lines: [
          { code: "scene.cancel();", explanation: "이전 장면의 timer와 run token을 무효화합니다." },
          { code: "state.index = nextIndex;", explanation: "Deck Controller가 다음 슬라이드 위치를 갱신합니다." },
          { code: "renderSlide();", explanation: "새 슬라이드의 정적 내용과 scene mount를 만듭니다." },
          { code: "sceneFactory.create(...);", explanation: "새 Scene Controller가 자신의 생명주기를 시작합니다." }
        ]
      },
      fallback: "네 개의 코드 줄과 각 줄의 해설을 번호 목록으로 표시합니다.",
      notes: ["이 장면의 코드는 실행되지 않고 text로만 렌더링됩니다.", "오른쪽 방향키로 줄별 해설을 진행합니다."],
      sources: ["Interactive Slides · code walkthrough recipe example"]
    },
    {
      id: "before-after-recipe",
      section: "장면 레시피",
      kicker: "BEFORE / AFTER",
      title: "같은 기준을 유지해야 변화가 과장되지 않는다.",
      summary: "전후 버튼을 전환해 발표 runtime의 책임 구조 변화를 비교합니다.",
      evidence: { label: "동일 기준 비교", tone: "analysis" },
      scene: {
        type: "before-after",
        before: { label: "Before", points: ["이동과 시연 timer가 같은 코드에 혼재", "재생 중 이동 시 오래된 callback 위험", "실패 fallback이 장면마다 다름"] },
        after: { label: "After", points: ["Deck과 Scene Controller 책임 분리", "run token으로 오래된 callback 무효화", "정적 fallback과 공통 복구 제어"] }
      },
      fallback: "Before와 After를 같은 세 기준으로 비교하는 두 열을 표시합니다.",
      notes: ["두 상태의 항목 순서가 동일하다는 점을 짚습니다.", "After를 과장하기 위해 기준을 바꾸지 않았음을 설명합니다."],
      sources: ["Interactive Slides · before-after recipe example"]
    },
    {
      id: "closing",
      section: "적용",
      kicker: "TAKEAWAY",
      title: "좋은 시연은 화려한 장면이 아니라 통제 가능한 설명이다.",
      summary: "핵심 메시지, 근거 경계와 장면 생명주기가 함께 있을 때 시연은 반복 가능한 발표 도구가 됩니다.",
      evidence: { label: "결론", tone: "verified" },
      metrics: [
        { value: "2", unit: "층", label: "Deck + Scene", detail: "책임 분리" },
        { value: "3", unit: "상태", label: "ready · running · complete", detail: "재생 계약" },
        { value: "1", unit: "메시지", label: "슬라이드당", detail: "집중 유지" }
      ],
      notes: ["세 숫자를 차례로 짚고 발표의 핵심 문장을 반복합니다."],
      sources: ["Interactive Slides starter · completion contract"]
    }
  ]
};
