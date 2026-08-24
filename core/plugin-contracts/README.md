# Plugin Contracts

## Purpose

Defines the common interface between the framework and plugins.

## Plugin Contract

Each plugin should declare:

```yaml
name: example-plugin
version: 1.0.0
capabilities:
  - capability-name
skills:
  - skill-name
evaluation:
  enabled: true
```

## Required concepts

### Capability

A capability describes a user-facing ability.

### Skill

A skill is an executable behavior implementation.

### Evaluation

Evaluation defines how behavior quality is measured.

## Compatibility

Future versions should preserve contract compatibility or provide migration paths.
