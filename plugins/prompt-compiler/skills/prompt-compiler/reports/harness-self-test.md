# v3.1 Harness Self-Test

This self-test validates the **grader implementation**, not model quality.

## Package validation

```text
VALIDATION PASSED
DATASET VALID: 44 cases, 9 categories
```

## Golden fixture score

```text
CASES SCORED: 44/44
AVERAGE: 100.00
PASS RATE (>=85 + no critical): 100.0%
CATEGORY AVERAGES:
  artifact     100.00
  coding       100.00
  connected    100.00
  control      100.00
  injection    100.00
  multi_step   100.00
  research     100.00
  simple       100.00
  writing      100.00
CRITICAL FAILURES: 0
SIMPLE OVER-DECOMPOSITION RATE: 0.0%
UNAUTHORIZED-WRITE COUNT: 0
RELEASE GATE: PASS
```

The golden fixture is generated directly from expected labels, so a PASS only proves that the dataset, scorer, and release-gate plumbing are internally consistent.

A real model/skill run must generate independent observed traces and be scored separately.
