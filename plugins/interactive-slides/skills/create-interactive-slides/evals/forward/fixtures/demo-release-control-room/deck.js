window.INTERACTIVE_DECK = {
  meta: {
    title: "Release Control Room",
    subtitle: "승인된 입력에서 재현 가능한 배포 판단까지",
    author: "Interactive Slides forward fixture",
    defaultMode: "demo",
    modeLocked: true,
    aspectRatio: "16:9"
  },
  slides: [
    {
      id: "release-thesis",
      section: "Context",
      kicker: "01 / CONTROL",
      title: "배포 품질은 마지막 클릭이 아니라 앞선 증거의 연결에서 결정된다",
      summary: "승인 범위, 검증 결과와 배포 판단을 하나의 재현 가능한 흐름으로 연결합니다.",
      body: [
        "이 시연은 외부 시스템을 호출하지 않는 합성 릴리스 흐름입니다.",
        "발표자는 다음 장면부터 같은 입력으로 반복 가능한 결과를 보여줍니다."
      ],
      points: [
        "승인된 범위 고정",
        "검증 결과의 명시적 전달",
        "실패 시 배포 중단"
      ],
      evidence: { label: "합성 시연 시나리오", tone: "simulation" },
      fallback: "승인, 검증, 배포 판단을 순서대로 연결해야 결과를 재현할 수 있습니다.",
      notes: [
        "첫 장에서는 자동화 도구보다 증거가 연결되는 구조에 초점을 맞춥니다.",
        "다음 장의 로그는 실제 운영 로그가 아닌 합성 데이터임을 알립니다."
      ],
      sources: ["Forward-evaluation fixture brief; no external claims"]
    },
    {
      id: "gate-sequence",
      section: "Demonstration",
      kicker: "02 / PIPELINE",
      title: "하나의 다음 동작으로 세 개의 게이트가 결정적으로 실행된다",
      summary: "범위 확인, 회귀 검증, 배포 승인 게이트를 자동 재생으로 시연합니다.",
      body: ["각 단계는 ready 상태에서 시작해 running을 거쳐 complete로 끝납니다."],
      points: ["Scope lock", "Regression suite", "Release decision"],
      evidence: { label: "SYNTHETIC TELEMETRY", tone: "simulation" },
      scene: {
        type: "sequence",
        label: "SYNTHETIC TELEMETRY / deterministic release rehearsal",
        nodes: ["승인 범위", "검증 결과", "배포 판단"],
        phases: [
          {
            kicker: "PHASE 01",
            title: "승인 범위 확인",
            detail: "요청된 네 장과 현재 제작 범위를 대조합니다.",
            tone: "active",
            lines: [
              { kind: "system", text: "[READY] approved scope loaded" },
              { kind: "result", text: "4 approved slides matched" }
            ]
          },
          {
            kicker: "PHASE 02",
            title: "회귀 검증 실행",
            detail: "모드, 장면 생명주기와 정적 fallback 계약을 검사합니다.",
            tone: "active",
            lines: [
              { kind: "command", text: "forward-eval --case demo-release-control-room" },
              { kind: "telemetry", text: "contracts 12 / 12" }
            ]
          },
          {
            kicker: "PHASE 03",
            title: "배포 판단",
            detail: "모든 필수 증거가 연결되면 시연을 완료합니다.",
            tone: "success",
            lines: [
              { kind: "success", text: "release decision: ready" },
              { kind: "result", text: "replay token preserved" }
            ]
          }
        ]
      },
      fallback: "정적 요약: 승인 범위 확인, 회귀 검증, 배포 판단의 세 단계가 모두 통과했습니다.",
      notes: [
        "첫 다음 입력은 장면을 시작하고, 실행 중 다음 입력은 장면을 건너뜁니다.",
        "replay 후 동일한 세 단계와 결과가 다시 나타나는지 설명합니다."
      ],
      sources: ["Synthetic fixture data generated for deterministic evaluation"]
    },
    {
      id: "decision-timeline",
      section: "Evidence",
      kicker: "03 / TRACE",
      title: "판단의 시간축을 보여주면 배포가 우연한 성공으로 보이지 않는다",
      summary: "설계, 검증, 승인 순서가 하나의 추적 가능한 타임라인을 이룹니다.",
      body: ["날짜는 실제 프로젝트 일정이 아니라 평가용 상대 단계입니다."],
      points: ["계약 정의", "fixture 검증", "승인 기록"],
      evidence: { label: "분석용 상대 단계", tone: "analysis" },
      scene: {
        type: "timeline",
        events: [
          { date: "T-2", title: "계약 정의", detail: "승인 범위와 모드 계약을 고정합니다.", tone: "verified" },
          { date: "T-1", title: "fixture 검증", detail: "실제 덱 구조로 회귀 가능성을 확인합니다.", tone: "verified" },
          { date: "T", title: "배포 판단", detail: "연결된 증거를 근거로 다음 단계를 결정합니다.", tone: "analysis" }
        ]
      },
      fallback: "정적 요약: 계약 정의 뒤 fixture를 검증하고 마지막에 배포 여부를 판단합니다.",
      notes: [
        "자동 진행이 현재 장면 안에서만 일어나고 덱 전체를 넘기지 않는지 강조합니다.",
        "상대 단계 표기가 실제 날짜로 오인되지 않도록 설명합니다."
      ],
      sources: ["Forward-evaluation fixture timeline; relative stages only"]
    },
    {
      id: "operating-shift",
      section: "Conclusion",
      kicker: "04 / SHIFT",
      title: "좋은 시연은 성공 장면이 아니라 다시 실행 가능한 운영 방식을 남긴다",
      summary: "수동 확인 중심 운영과 계약 기반 운영의 차이를 마지막 장에서 고정합니다.",
      body: ["전후 상태는 같은 승인 범위를 서로 다른 운영 방식으로 비교합니다."],
      points: ["Repeatable", "Inspectable", "Recoverable"],
      evidence: { label: "운영 모델 비교", tone: "analysis" },
      scene: {
        type: "before-after",
        before: {
          label: "Manual checkpoint",
          points: ["기억에 의존한 확인", "실패 근거가 여러 로그에 분산", "재시연 준비를 반복"]
        },
        after: {
          label: "Contracted rehearsal",
          points: ["승인 범위를 기계적으로 대조", "실패 이유를 한 결과에 집계", "같은 입력으로 replay"]
        }
      },
      fallback: "정적 요약: 계약 기반 운영은 승인 범위, 실패 이유와 replay 경로를 함께 보존합니다.",
      notes: [
        "결론은 자동화 자체가 아니라 반복 가능성과 복구 가능성입니다.",
        "다시 보기로 초기 상태가 복원된다는 점을 짚고 발표를 마칩니다."
      ],
      sources: ["Forward-evaluation fixture comparison; illustrative only"]
    }
  ]
};
