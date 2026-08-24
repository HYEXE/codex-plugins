# Plugin Router Design

## Purpose

Select the most appropriate plugin and skill from a user request.

## Routing flow

```text
Request
  |
Intent extraction
  |
Capability matching
  |
Candidate ranking
  |
Skill selection
  |
Execution
```

## Routing signals

- User intent
- Required capability
- Domain
- Risk level
- Plugin availability
- Evaluation confidence

## Future implementation

Possible modules:

```text
router/
├── classifier
├── capability-matcher
├── ranker
└── conflict-resolver
```

The router should remain independent from individual plugins.
