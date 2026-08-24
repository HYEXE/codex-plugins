# Codex Agent Framework Architecture

## Overview

`codex-plugins` evolves from a collection of skills into an extensible agent framework.
The architecture separates plugin discovery, capability contracts, execution, and evaluation.

## High-level architecture

```text
User Request
    |
    v
Intent Router
    |
    +----------------+
    | Plugin Registry |
    +----------------+
            |
            v
     Selected Plugin
            |
            v
        Skill Runtime
            |
            v
      Evaluation Layer
```

## Core principles

### Capability first

Plugins should declare capabilities instead of relying only on names.

### Contract driven

Every plugin should expose a predictable manifest, lifecycle, and evaluation interface.

### Observable behavior

Agent behavior should be measured through routing cases, execution traces, and regression datasets.

## Future modules

```text
core/
├── contracts/
├── router/
├── evaluator/
└── runtime/
```

## Evolution path

1. Stabilize plugin contracts.
2. Introduce capability based routing.
3. Expand evaluation datasets.
4. Build reusable agent infrastructure.
