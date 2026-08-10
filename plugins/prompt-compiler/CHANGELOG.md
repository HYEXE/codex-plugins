# Changelog

## v3.2-ko — Korean Semantic Layer

목표:
- 한국어 사용자와 유지보수자가 Skill 규칙을 자연스럽게 읽을 수 있게 한다.
- machine interface는 v3.1과 동일하게 유지한다.

변경:
- `SKILL.md`의 자연어 지침을 한국어 중심으로 재작성
- `references/`의 설명과 예시를 한국어 중심으로 재작성
- eval adapter / end-to-end 설명을 한국어화
- README를 v3.2-ko 기준으로 갱신
- `LANGUAGE_POLICY.md` 추가
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
- localization validator 통과는 machine interface가 유지되었다는 뜻이다.
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
