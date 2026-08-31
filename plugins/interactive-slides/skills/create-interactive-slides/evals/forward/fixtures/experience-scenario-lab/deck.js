window.INTERACTIVE_DECK = {
  meta: {
    title: "Scenario Lab",
    subtitle: "선택하고 조절하며 이해하는 운영 전략 워크숍",
    author: "Interactive Slides forward fixture",
    defaultMode: "experience",
    modeLocked: true,
    aspectRatio: "16:9"
  },
  slides: [
    {
      id: "choose-strategy",
      section: "Explore",
      kicker: "01 / CHOICE",
      title: "첫 선택이 참가자의 관점을 수동 청취에서 능동 탐색으로 바꾼다",
      summary: "참가자가 안정성 또는 속도 중심 전략을 선택하고 즉시 결과 설명을 확인합니다.",
      body: ["정답을 맞혀야 진행하는 퀴즈가 아니라 관점의 차이를 드러내는 선택입니다."],
      points: ["즉시 피드백", "숨겨진 정답 없음", "언제든 다시 선택"],
      evidence: { label: "워크숍용 가상 시나리오", tone: "simulation" },
      scene: {
        type: "choice",
        prompt: "이번 운영 주기에서 무엇을 먼저 최적화할까요?",
        options: [
          { label: "안정성 우선", feedback: "검증 범위를 넓히고 변경량을 작게 유지하는 전략입니다." },
          { label: "학습 속도 우선", feedback: "관찰 범위를 좁히고 짧은 실험을 반복하는 전략입니다." },
          { label: "균형 운영", feedback: "핵심 위험은 고정하고 나머지는 단계적으로 탐색하는 전략입니다." }
        ]
      },
      fallback: "정적 요약: 안정성, 학습 속도, 균형 운영은 서로 다른 검증 범위와 피드백 주기를 만듭니다.",
      notes: [
        "참가자에게 원하는 선택지를 직접 눌러 보도록 안내합니다.",
        "선택은 평가가 아니라 다음 장의 조절 기준을 만드는 과정임을 설명합니다."
      ],
      sources: ["Synthetic workshop prompt for forward evaluation"]
    },
    {
      id: "tune-scope",
      section: "Explore",
      kicker: "02 / RANGE",
      title: "범위를 움직이면 속도와 검증 비용의 관계가 즉시 보인다",
      summary: "슬라이더로 검증 단계를 조절하고 예상 워크숍 시간을 즉시 확인합니다.",
      body: ["표시되는 시간은 실제 성능 수치가 아닌 상호작용 검증용 계산 결과입니다."],
      points: ["키보드 조절", "결정적 초기값", "reset 가능"],
      evidence: { label: "합성 계산 모델", tone: "simulation" },
      scene: {
        type: "range",
        label: "검증 단계 수",
        min: 1,
        max: 8,
        step: 1,
        value: 4,
        unit: "단계",
        outputLabel: "예상 워크숍 시간",
        result: { base: 2, factor: 1.5, decimals: 1, suffix: "분" }
      },
      fallback: "정적 요약: 초기값 4단계는 합성 계산식에서 8.0분으로 표시되며 1단계씩 조절할 수 있습니다.",
      notes: [
        "마우스뿐 아니라 화살표 키로 값을 바꿀 수 있음을 안내합니다.",
        "replay는 값 4와 초기 결과로 돌아가야 합니다."
      ],
      sources: ["Synthetic range model; values are illustrative"]
    },
    {
      id: "inspect-system",
      section: "Understand",
      kicker: "03 / SYSTEM",
      title: "관계망을 직접 탐색하면 선택이 시스템에 미치는 영향을 설명할 수 있다",
      summary: "입력, 검증, 관찰, 결정 노드를 임의 순서로 탐색하고 관계 목록을 함께 읽습니다.",
      body: ["공간 배치만으로 관계를 전달하지 않고 텍스트 관계 목록을 함께 제공합니다."],
      points: ["임의 순서 탐색", "focus 이동", "텍스트 관계 제공"],
      evidence: { label: "개념 모델", tone: "analysis" },
      scene: {
        type: "diagram",
        nodes: [
          { id: "input", label: "Input", detail: "참가자가 선택한 운영 전략" },
          { id: "gate", label: "Gate", detail: "선택에 맞춘 검증 범위" },
          { id: "signal", label: "Signal", detail: "결과를 설명하는 관찰 신호" },
          { id: "decision", label: "Decision", detail: "다음 반복에서 유지하거나 바꿀 항목" }
        ],
        links: [
          { from: "input", to: "gate", label: "범위를 조정" },
          { from: "gate", to: "signal", label: "증거를 생성" },
          { from: "signal", to: "decision", label: "판단을 지원" },
          { from: "decision", to: "input", label: "다음 선택에 반영" }
        ]
      },
      fallback: "정적 요약: 운영 전략은 검증 범위를 바꾸고, 검증 신호는 다음 결정을 통해 새로운 입력으로 돌아갑니다.",
      notes: [
        "노드를 정해진 순서로 누를 필요가 없다는 점을 먼저 알립니다.",
        "보조기술에서는 관계 목록으로 같은 구조를 읽을 수 있음을 설명합니다."
      ],
      sources: ["Conceptual system model for forward evaluation"]
    },
    {
      id: "compare-outcome",
      section: "Reflect",
      kicker: "04 / REFLECT",
      title: "마지막 비교가 참가자의 조작을 자신의 운영 언어로 바꾼다",
      summary: "관찰 전후 상태를 직접 전환하며 선택, 범위와 시스템 관계를 하나의 결론으로 연결합니다.",
      body: ["현재 상태는 aria-pressed로 전달되고 reset하면 첫 상태로 돌아갑니다."],
      points: ["직접 전환", "현재 상태 노출", "초기 상태 복원"],
      evidence: { label: "워크숍 성찰 프레임", tone: "analysis" },
      scene: {
        type: "before-after",
        before: {
          label: "Before exploration",
          points: ["운영 전략을 추상적인 구호로 이해", "검증 범위를 고정된 절차로 인식", "결과만 확인"]
        },
        after: {
          label: "After exploration",
          points: ["전략을 선택 가능한 관점으로 이해", "범위를 조절 가능한 변수로 인식", "관계와 근거를 함께 설명"]
        }
      },
      fallback: "정적 요약: 체험 뒤에는 전략, 검증 범위와 관찰 신호의 관계를 함께 설명할 수 있습니다.",
      notes: [
        "참가자가 before와 after를 직접 오가며 자신의 언어로 차이를 말하도록 요청합니다.",
        "정답을 채점하지 않고 조작이 남긴 이해를 회고하며 마칩니다."
      ],
      sources: ["Workshop reflection frame; illustrative only"]
    }
  ]
};
