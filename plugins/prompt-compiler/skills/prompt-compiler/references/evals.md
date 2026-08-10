# Behavioral Evals

v3.2-ko의 machine-readable eval suite:

- `evals/cases.jsonl` — 44개 compiler-decision case
- `evals/compiler-trace.schema.json` — controlled eval trace schema
- `evals/eval_adapter.md` — test trace 생성 규칙
- `scripts/eval_harness.py` — deterministic structural grader
- `evals/end_to_end.md` — product-native end-to-end matrix

scoring과 release gate는 `references/evaluation.md`를 참고한다.
