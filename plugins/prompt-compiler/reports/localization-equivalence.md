# v3.1 → v3.2-ko Localization Equivalence Report

이 보고서는 한국어 localization 과정에서 canonical machine interface가 바뀌지 않았는지 확인한다.

| File | v3.1 대비 상태 |
|---|---|
| `schemas/intent-graph.schema.json` | byte-for-byte 동일 |
| `evals/compiler-trace.schema.json` | byte-for-byte 동일 |
| `evals/cases.jsonl` | byte-for-byte 동일 |
| `evals/golden_results.jsonl` | byte-for-byte 동일 |
| `scripts/eval_harness.py` | CLI 도움말과 오류 안내 변경, scoring 동작 호환 |

결론: schema와 eval fixture 4개는 v3.1과 byte-for-byte 동일하다. Eval Harness는 `--help`와 명확한 사용법 출력을 추가해 파일 자체는 달라졌지만, scoring 항목·배점·release gate는 유지한다.

`scripts/validate_localization.py`는 현재 machine-critical 파일이 `machine-interface.sha256.json`에 기록된 승인 체크섬과 일치하는지만 검증한다. v3.1과의 동등성이나 실제 모델 성능은 증명하지 않으며, 이를 확인하려면 별도 baseline 비교와 동일 eval case의 모델 A/B test가 필요하다.
