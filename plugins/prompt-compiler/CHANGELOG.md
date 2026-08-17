# Changelog

## Package 0.7.0 — Declarative Quality Gates and Observation Provenance

변경:
- 플러그인이 필요한 skill 파일과 의미적 marker를 `.codex-plugin/quality-gates.json`에서 직접 선언하도록 변경
- 날짜가 포함된 독립 관찰 snapshot을 안정적인 `evals/observations.json` manifest로 선택하도록 변경
- dataset과 observed result의 SHA-256, 관찰 시각, plugin 버전과 알려진 provenance 공백을 metadata로 기록
- 플러그인 패키지 버전 `0.7.0`과 내부 protocol spec `v3.2-ko`를 사용자 문서와 skill 본문에서 명확히 구분

사실적 경계:
- 기존 snapshot의 누락된 model·Codex build 정보는 추정하지 않고 `legacy-partial`로 보존한다.
- 완전한 provenance는 새 live eval 실행에서 생성한다.

## Package 0.6.0 — Task State and Delta Compilation

변경:
- 현재 대화에서 확인 가능한 목표, 확정 제약, 권한 상한, 대기 질문, preview 승인과 검증 상태만 유지하는 `Task State Capsule` 추가
- 후속 메시지를 `continue`, `amend`, `replace`, `approve`, `cancel`로 분류하고 변경된 의도와 downstream만 다시 컴파일하는 delta workflow 추가
- 사용자 정정, 입력·대상·권한 변경, 취소에 따라 오래된 가정·산출물·승인·검증을 무효화하는 규칙 추가
- preview 승인을 `action + target + material content`에 결합해 실질적 변경 후 기존 승인을 재사용하지 않도록 강화
- 형식만 바뀐 후속 요청, 대기 질문을 취소하는 새 목표, preview 대상 변경과 취소를 검증하는 행동 회귀 사례 추가

성능 원칙:
- 이미 해결된 질문, 유효한 source·tool 결과, 영향받지 않은 산출물과 검증은 재사용한다.
- freshness, mutable state, 입력 변경 또는 권한 경계 변경으로 결과가 달라질 때만 관련 노드를 재조회·재검증한다.

사실적 경계:
- 상태 캡슐은 현재 작업 연속성을 위한 내부 실행 상태이며 새 작업의 영구 메모리나 모든 turn의 스킬 재선택을 보장하지 않는다.
- 변경분 컴파일은 질문·도구 호출을 무조건 줄이는 최적화가 아니며 정확성, 권한과 검증을 유지한다.

## Package 0.5.0 — Prompt Orchestration Front Door

변경:
- `prompt-compiler`를 요청 충분성 점검부터 실제 수행·검증까지 담당하는 기본 진입점으로 확장
- 충분한 요청은 즉시 실행하고, 작은 누락은 명시적 가정으로 보완하며, 중요한 누락만 질문하는 실행 전 gate 추가
- 질문을 한 차례 1~3개, 최대 두 차례로 제한하고 핵심 대상·권한·비가역 행동 정보가 없으면 blocker로 중단
- 현재 작업의 후속 요청마다 충분성 gate와 실행·검증을 적용하는 task-scoped 모드 추가
- 확인 답변을 대기 중 요청과 합쳐 원 요청 재전송 없이 이어서 실행하는 clarification resume 추가
- preview와 실제 외부 행동의 승인을 분리하고 변경된 대상·내용에는 기존 승인을 재사용하지 않는 경계 추가
- 중요한 가정, capability 부족과 부분 완료 상태를 구분하는 실행 영수증 추가
- `prompt-coach`를 대화형 니즈 발견과 재사용 가능한 prompt-only 산출물로 한정
- 플러그인 호출, 프롬프트 전용, 평가 전용 요청의 라우팅 경계와 회귀 사례 보강
- 사용자에게 보인 transcript에서 13개 독립 사례의 실행 결과, 작업 단위 활성화, 이어가기, preview 경계, 부분 완료, 재전송 요구와 자동 연계 주장을 판정하는 오케스트레이션 행동 평가 추가
- capability가 없는 작업을 나중에 자동 완료한다고 주장하는 응답을 거부하는 회귀 검사 추가

사실적 경계:
- 내부 실행 명세는 같은 모델 실행에서 사용하는 중간 표현이며 별도 모델 호출이나 새 사용자 메시지가 아니다.
- 플러그인은 메시지 제출 전 입력창을 가로채는 전역 인터셉터가 아니다.
- task-scoped 모드는 현재 대화의 작업 지침이며 새 작업의 자동 활성화나 매 턴 스킬 재주입을 보장하지 않는다.
- 별도 tool trace가 없는 행동 평가는 사용자에게 보인 주장만 판정하며 실제 외부 side effect 부재를 증명하지 않는다.

유지:
- Prompt Compiler v3.2-ko의 canonical machine interface와 구조 평가 규약
- 외부 write·전송·게시·병합·삭제의 명시적 권한 경계
- 기존 Prompt Coach 0.4.0 행동 평가의 역사적 관찰 자료

## Package 0.4.0 — Prompt Coach

추가:
- 요청 충분성을 조용히 판단하는 `prompt-coach` 스킬
- 필요한 경우에만 1~3개 핵심 질문으로 니즈를 구체화하는 대화 흐름
- one-shot과 task-scoped coaching 모드
- Coach·Compiler·Evaluator 라우팅 경계와 회귀 사례
- task-scoped 후속 요청과 send·merge·publish·delete 권한 경계를 포함한 12개 독립 forward test
- 원문 transcript에서 관찰값을 계산하고 별도 판정 근거를 검증하는 Prompt Coach 행동 평가 도구

유지:
- Prompt Compiler v3.2-ko 실행 규칙과 기계 인터페이스
- Prompt Evaluator의 기존 프롬프트 평가 역할
- 명시적 실행 요청이 없으면 대상 작업을 수행하지 않는 권한 경계
- 스킬 간 자동 handoff를 가정하지 않는 실행 경계

## v3.2-ko — Korean Semantic Layer

목표:
- 한국어 사용자와 유지보수자가 Skill 규칙을 자연스럽게 읽을 수 있게 한다.
- machine identifier와 scoring protocol은 v3.1 호환성을 유지한다.

변경:
- `SKILL.md`의 자연어 지침을 한국어 중심으로 재작성
- `references/`의 설명과 예시를 한국어 중심으로 재작성
- eval adapter / end-to-end 설명을 한국어화
- README를 v3.2-ko 기준으로 갱신
- `skills/prompt-compiler/references/language-policy.md` 추가
- localization integrity validator 추가
- machine-critical 파일의 SHA-256 manifest 추가

유지:
- JSON key
- enum
- profile ID
- permission ID
- eval label
- JSON Schema
- deterministic eval harness protocol

주의:
- localization validator 통과는 현재 파일이 기록된 기준 체크섬과 일치한다는 뜻이다.
- 실제 모델 성능이 v3.1과 동일하다는 뜻은 아니며, 모델 기반 A/B eval이 별도로 필요하다.

## v3.1 — Eval-Hardened Intent Compiler

Main objective: make v3 measurable before adding more orchestration features.

Added:
- single-node-first bias;
- default node budget (1 / 2–5 / >5 only when justified);
- explicit anti-over-orchestration gate;
- freshness gate for stable vs time-sensitive vs connected-private facts;
- artifact gate;
- stricter clarification/question gate;
- separate evaluation discipline;
- 44 machine-readable compiler-decision eval cases;
- deterministic 100-point structural grader;
- permission-critical failure handling;
- category release gates;
- controlled eval trace JSON Schema;
- end-to-end product eval matrix;
- harness golden self-test fixture.

Release target:
- average >= 92;
- no permission-critical failures;
- every category >= 85;
- simple-task over-decomposition <= 5%;
- unauthorized writes = 0.

## v3

Architectural shift from prompt rewriting to intent-first execution:
Intent Frame → Complexity Gate → Minimal Task Graph → Execution Contracts → Capability Routing → Execute → Verify → Synthesize.
