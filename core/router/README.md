# Plugin Router Design

## Purpose

Select the most appropriate plugin and skill from a user request using explicit capability contracts.

## Routing flow

```text
Request
  |
Capability extraction
  |
Registry lookup
  |
Deterministic matching
  |
Candidate ranking
  |
Execution
  |
Evaluation
```

## Current prototype

- `capability-registry.json`: plugin capability declarations
- `matcher.py`: deterministic matcher
- `evals/routing-cases.jsonl`: regression dataset

## Future implementation

```text
router/
├── classifier
├── capability-matcher
├── ranker
└── conflict-resolver
```

The router remains independent from individual plugins.
