# v3.1 → v3.2-ko Localization Equivalence Report

이 보고서는 한국어 localization 과정에서 canonical machine interface가 바뀌지 않았는지 확인한다.

| File | Identical |
|---|---|
| `schemas/intent-graph.schema.json` | YES |
| `evals/compiler-trace.schema.json` | YES |
| `evals/cases.jsonl` | YES |
| `evals/golden_results.jsonl` | YES |
| `scripts/eval_harness.py` | YES |

결론: 위 machine-critical 파일은 v3.1과 byte-for-byte 동일하다.

이 검증은 **interface equivalence**만 증명한다. 실제 모델 성능 동등성은 동일 eval case를 모델에 실행하는 A/B test가 필요하다.
